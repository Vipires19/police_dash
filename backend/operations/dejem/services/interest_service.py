"""InterestService — manifestação de interesse DEJEM (Sprint C3)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.dejem import DejemInterest, DejemMonth
from models.user import OrganizationalUnit, User
from operations.dejem.models.enums import CampaignStatus
from operations.dejem.models.status_mapping import from_legacy
from operations.dejem.repositories.campaign_repository import CampaignRepository
from operations.dejem.repositories.interest_repository import InterestRepository
from operations.dejem.schemas.interest import (
    InterestAdminListResponse,
    InterestAdminRow,
    InterestCreate,
    InterestMyResponse,
    InterestResponse,
    InterestStatisticsResponse,
    InterestUpdate,
)


class InterestError(ValueError):
    """Erro de regra de negócio da manifestação de interesse."""


class InterestService:
    """Gerencia interesse do policial em campanhas OPEN."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InterestRepository(db)
        self.campaigns = CampaignRepository(db)

    def upsert(self, officer: User, body: InterestCreate) -> InterestResponse:
        campaign = self._require_interest_writable(body.campaign_id)
        desired = self._validate_desired(body.desired_slots, campaign)

        existing = self.repo.get_by_campaign_and_officer(campaign.id, officer.id)
        if existing:
            existing.interested = True
            existing.desired_slots = desired
            self.repo.save(existing)
            self.db.commit()
            self.db.refresh(existing)
            return self._to_response(existing)

        row = DejemInterest(
            month_id=campaign.id,
            user_id=officer.id,
            interested=True,
            desired_slots=desired,
        )
        self.repo.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def update(self, officer: User, body: InterestUpdate) -> InterestResponse:
        campaign = self._require_interest_writable(body.campaign_id)
        desired = self._validate_desired(body.desired_slots, campaign)

        row = self.repo.get_by_campaign_and_officer(campaign.id, officer.id)
        if not row:
            raise InterestError("Manifestação não encontrada. Registre o interesse primeiro.")

        row.interested = True
        row.desired_slots = desired
        self.repo.save(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def cancel(self, officer: User, campaign_id: int) -> None:
        campaign = self._get_campaign_or_raise(campaign_id)
        status = from_legacy(campaign.status)

        if status == CampaignStatus.OPEN:
            row = self.repo.get_by_campaign_and_officer(campaign_id, officer.id)
            if not row:
                raise InterestError("Manifestação não encontrada.")
            self.repo.delete(row)
            self.db.commit()
            return

        if status == CampaignStatus.ALLOCATED:
            # C6: libera créditos AVAILABLE; marca interesse como cancelado
            from operations.dejem.services.incremental_allocation_service import (
                IncrementalAllocationService,
            )

            IncrementalAllocationService(self.db).release_available_credits(
                officer,
                campaign_id,
                officer.id,
                reason="interest_cancel",
            )
            row = self.repo.get_by_campaign_and_officer(campaign_id, officer.id)
            if row:
                row.interested = False
                row.desired_slots = 0
                self.repo.save(row)
                self.db.commit()
            return

        raise InterestError(
            "Cancelamento de interesse não permitido neste status da campanha."
        )

    def get_mine(self, officer: User, campaign_id: int) -> InterestMyResponse | None:
        campaign = self._get_campaign_or_raise(campaign_id)
        row = self.repo.get_by_campaign_and_officer(campaign.id, officer.id)
        if not row:
            return None
        return InterestMyResponse(
            id=row.id,
            campaign_id=campaign.id,
            campaign_month=campaign.month,
            campaign_year=campaign.year,
            campaign_status=from_legacy(campaign.status),
            desired_slots=row.desired_slots,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def list_admin(
        self,
        campaign_id: int,
        *,
        organizational_unit: OrganizationalUnit | None = None,
    ) -> InterestAdminListResponse:
        self._get_campaign_or_raise(campaign_id)
        rows = self.repo.list_by_campaign(
            campaign_id,
            organizational_unit=organizational_unit,
            only_interested=True,
        )
        items = [self._to_admin_row(r) for r in rows]
        total_desired = sum(i.desired_slots for i in items)
        return InterestAdminListResponse(
            campaign_id=campaign_id,
            participants_count=len(items),
            total_desired_slots=total_desired,
            items=items,
        )

    def statistics(self, campaign_id: int) -> InterestStatisticsResponse:
        self._get_campaign_or_raise(campaign_id)
        stats = self.repo.statistics(campaign_id)
        return InterestStatisticsResponse(
            campaign_id=campaign_id,
            interested_officers=int(stats["interested_officers"]),
            total_desired_slots=int(stats["total_desired_slots"]),
            average_desired_slots=round(float(stats["average_desired_slots"]), 2),
            max_desired_slots=int(stats["max_desired_slots"]),
            min_desired_slots=int(stats["min_desired_slots"]),
        )

    def _require_open_campaign(self, campaign_id: int) -> DejemMonth:
        campaign = self._get_campaign_or_raise(campaign_id)
        status = from_legacy(campaign.status)
        if status != CampaignStatus.OPEN:
            raise InterestError(
                "A manifestação de interesse só é permitida com a campanha OPEN."
            )
        return campaign

    def _require_interest_writable(self, campaign_id: int) -> DejemMonth:
        """OPEN (manifestação) ou ALLOCATED (novos interessados antes de RUNNING — C6)."""
        campaign = self._get_campaign_or_raise(campaign_id)
        status = from_legacy(campaign.status)
        if status in {CampaignStatus.OPEN, CampaignStatus.ALLOCATED}:
            return campaign
        raise InterestError(
            "Registro/edição de interesse não permitido neste status da campanha."
        )

    def _get_campaign_or_raise(self, campaign_id: int) -> DejemMonth:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise InterestError("Campanha DEJEM não encontrada.")
        return campaign

    def _validate_desired(self, desired_slots: int, campaign: DejemMonth) -> int:
        if desired_slots < 1:
            raise InterestError("A quantidade desejada deve ser no mínimo 1.")
        limit = campaign.monthly_limit_per_officer
        if desired_slots > limit:
            raise InterestError(
                f"A quantidade desejada não pode exceder o limite mensal ({limit})."
            )
        return desired_slots

    def _to_response(self, row: DejemInterest) -> InterestResponse:
        return InterestResponse(
            id=row.id,
            campaign_id=row.month_id,
            police_officer_id=row.user_id,
            desired_slots=row.desired_slots,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_admin_row(self, row: DejemInterest) -> InterestAdminRow:
        user = row.user
        return InterestAdminRow(
            id=row.id,
            campaign_id=row.month_id,
            police_officer_id=row.user_id,
            desired_slots=row.desired_slots,
            created_at=row.created_at,
            updated_at=row.updated_at,
            patente=user.patente,
            nome_guerra=user.nome_guerra,
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            organizational_unit=user.organizational_unit,
        )
