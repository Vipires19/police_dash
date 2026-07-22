"""CampaignService — ciclo de vida da campanha DEJEM."""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.dejem import DejemMonth
from models.user import User
from operations.dejem.models.campaign_audit import CampaignStatusAudit
from operations.dejem.models.enums import CampaignStatus
from operations.dejem.models.status_mapping import assert_transition, from_legacy, to_legacy
from operations.dejem.repositories.campaign_repository import CampaignRepository
from operations.dejem.schemas.campaign import (
    CampaignAuditResponse,
    CampaignCreate,
    CampaignResponse,
)

# Defaults seguros para colunas NOT NULL herdadas de `dejem_months`
# (oferta/limite evoluem via OfferEvent / API legado).
_DEFAULT_TOTAL_SLOTS = 0
_DEFAULT_MONTHLY_LIMIT = 1


class CampaignError(ValueError):
    """Erro de regra de negócio do ciclo de vida da campanha."""


class CampaignService:
    """Gerencia criação e transições de status da campanha."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CampaignRepository(db)

    def list_campaigns(self) -> list[CampaignResponse]:
        return [self._to_response(row) for row in self.repo.list_all()]

    def list_open_campaigns(self) -> list[CampaignResponse]:
        return [self._to_response(row) for row in self.repo.list_open()]

    def get_campaign(self, campaign_id: int) -> CampaignResponse:
        return self._to_response(self._get_or_raise(campaign_id))

    def create_campaign(self, actor: User, body: CampaignCreate) -> CampaignResponse:
        existing = self.repo.get_by_year_month(body.year, body.month)
        if existing:
            raise CampaignError(
                f"Já existe uma campanha DEJEM para {body.month:02d}/{body.year}."
            )

        row = DejemMonth(
            year=body.year,
            month=body.month,
            total_available_slots=_DEFAULT_TOTAL_SLOTS,
            monthly_limit_per_officer=_DEFAULT_MONTHLY_LIMIT,
            status=to_legacy(CampaignStatus.CREATED),
            created_by_id=actor.id,
        )
        self.repo.add(row)
        self._audit(
            campaign_id=row.id,
            actor_id=actor.id,
            from_status=None,
            to_status=CampaignStatus.CREATED,
        )
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def open_campaign(self, campaign_id: int, actor: User) -> CampaignResponse:
        return self._transition(campaign_id, actor, CampaignStatus.OPEN)

    def close_registration(self, campaign_id: int, actor: User) -> CampaignResponse:
        return self._transition(campaign_id, actor, CampaignStatus.REGISTRATION_CLOSED)

    def mark_allocated(self, campaign_id: int, actor: User) -> CampaignResponse:
        """Marca ALLOCATED sem executar algoritmo de distribuição."""
        return self._transition(campaign_id, actor, CampaignStatus.ALLOCATED)

    def start_campaign(self, campaign_id: int, actor: User) -> CampaignResponse:
        return self._transition(campaign_id, actor, CampaignStatus.RUNNING)

    def close_campaign(self, campaign_id: int, actor: User) -> CampaignResponse:
        return self._transition(campaign_id, actor, CampaignStatus.CLOSED)

    def change_status(
        self,
        campaign_id: int,
        actor: User,
        target: CampaignStatus,
    ) -> CampaignResponse:
        return self._transition(campaign_id, actor, target)

    def list_audits(self, campaign_id: int) -> list[CampaignAuditResponse]:
        self._get_or_raise(campaign_id)
        return [
            CampaignAuditResponse.model_validate(row)
            for row in self.repo.list_status_audits(campaign_id)
        ]

    def _transition(
        self,
        campaign_id: int,
        actor: User,
        target: CampaignStatus,
    ) -> CampaignResponse:
        row = self._get_or_raise(campaign_id)
        current = from_legacy(row.status)
        try:
            assert_transition(current, target)
        except ValueError as exc:
            raise CampaignError(str(exc)) from exc

        row.status = to_legacy(target)
        self.repo.save(row)
        self._audit(
            campaign_id=row.id,
            actor_id=actor.id,
            from_status=current,
            to_status=target,
        )
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def _audit(
        self,
        *,
        campaign_id: int,
        actor_id: int,
        from_status: CampaignStatus | None,
        to_status: CampaignStatus,
    ) -> None:
        self.repo.add_status_audit(
            CampaignStatusAudit(
                campaign_id=campaign_id,
                actor_id=actor_id,
                from_status=from_status.value if from_status else None,
                to_status=to_status.value,
            )
        )

    def _get_or_raise(self, campaign_id: int) -> DejemMonth:
        row = self.repo.get(campaign_id)
        if not row:
            raise CampaignError("Campanha DEJEM não encontrada.")
        return row

    def _to_response(self, row: DejemMonth) -> CampaignResponse:
        return CampaignResponse(
            id=row.id,
            month=row.month,
            year=row.year,
            status=from_legacy(row.status),
            created_by_id=row.created_by_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            total_available_slots=row.total_available_slots,
            monthly_limit_per_officer=row.monthly_limit_per_officer,
            undistributed_slots=getattr(row, "undistributed_slots", 0) or 0,
            offer_excess_slots=getattr(row, "offer_excess_slots", 0) or 0,
        )
