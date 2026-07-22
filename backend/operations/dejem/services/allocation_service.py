"""AllocationService — infraestrutura de alocações (Sprint C4).

CRUD + auditoria. NÃO executa algoritmo de distribuição.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.dejem import DejemAllocation
from models.user import User
from operations.dejem.models.allocation_audit import AllocationAudit
from operations.dejem.repositories.allocation_repository import AllocationRepository
from operations.dejem.repositories.campaign_repository import CampaignRepository
from operations.dejem.schemas.allocation import (
    AllocationAuditResponse,
    AllocationCreate,
    AllocationResponse,
    AllocationUpdate,
)


class AllocationError(ValueError):
    pass


class AllocationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AllocationRepository(db)
        self.campaigns = CampaignRepository(db)

    def list_by_campaign(self, campaign_id: int) -> list[AllocationResponse]:
        self._require_campaign(campaign_id)
        return [self._to_response(r) for r in self.repo.list_by_campaign(campaign_id)]

    def get(self, allocation_id: int) -> AllocationResponse:
        return self._to_response(self._get_or_raise(allocation_id))

    def create(self, actor: User, body: AllocationCreate) -> AllocationResponse:
        self._require_campaign(body.campaign_id)
        existing = self.repo.get_by_campaign_and_officer(
            body.campaign_id,
            body.police_officer_id,
        )
        if existing:
            raise AllocationError(
                "Já existe allocation para este policial nesta campanha."
            )

        row = DejemAllocation(
            month_id=body.campaign_id,
            user_id=body.police_officer_id,
            allocated_slots=body.allocated_slots,
            used_slots=0,
            remaining_slots=body.allocated_slots,
        )
        self.repo.add(row)
        self._audit(
            allocation_id=row.id,
            campaign_id=body.campaign_id,
            actor_id=actor.id,
            action="CREATED",
            details=f"allocated_slots={body.allocated_slots}",
        )
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def update(
        self,
        allocation_id: int,
        actor: User,
        body: AllocationUpdate,
    ) -> AllocationResponse:
        row = self._get_or_raise(allocation_id)
        if body.allocated_slots < row.used_slots:
            raise AllocationError(
                f"allocated_slots ({body.allocated_slots}) não pode ser menor "
                f"que used_slots ({row.used_slots})."
            )
        previous = row.allocated_slots
        row.allocated_slots = body.allocated_slots
        row.remaining_slots = body.allocated_slots - row.used_slots
        self.repo.save(row)
        self._audit(
            allocation_id=row.id,
            campaign_id=row.month_id,
            actor_id=actor.id,
            action="UPDATED",
            details=f"allocated_slots {previous} → {body.allocated_slots}",
        )
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def delete(self, allocation_id: int, actor: User) -> None:
        row = self._get_or_raise(allocation_id)
        campaign_id = row.month_id
        details = f"allocated_slots={row.allocated_slots} officer={row.user_id}"
        self._audit(
            allocation_id=row.id,
            campaign_id=campaign_id,
            actor_id=actor.id,
            action="DELETED",
            details=details,
        )
        self.repo.delete(row)
        self.db.commit()

    def list_audits(self, campaign_id: int) -> list[AllocationAuditResponse]:
        self._require_campaign(campaign_id)
        return [
            AllocationAuditResponse.model_validate(r)
            for r in self.repo.list_audits(campaign_id)
        ]

    def _audit(
        self,
        *,
        allocation_id: int | None,
        campaign_id: int,
        actor_id: int,
        action: str,
        details: str | None,
    ) -> None:
        self.repo.add_audit(
            AllocationAudit(
                allocation_id=allocation_id,
                campaign_id=campaign_id,
                actor_id=actor_id,
                action=action,
                details=details,
            )
        )

    def _get_or_raise(self, allocation_id: int) -> DejemAllocation:
        row = self.repo.get(allocation_id)
        if not row:
            raise AllocationError("Allocation não encontrada.")
        return row

    def _require_campaign(self, campaign_id: int) -> None:
        if not self.campaigns.get(campaign_id):
            raise AllocationError("Campanha DEJEM não encontrada.")

    def _to_response(self, row: DejemAllocation) -> AllocationResponse:
        return AllocationResponse(
            id=row.id,
            campaign_id=row.month_id,
            police_officer_id=row.user_id,
            allocated_slots=row.allocated_slots,
            used_slots=row.used_slots,
            remaining_slots=row.remaining_slots,
            created_at=row.created_at,
        )
