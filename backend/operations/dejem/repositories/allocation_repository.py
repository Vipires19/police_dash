"""AllocationRepository — alocações + auditoria."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from operations.dejem.models.allocation import Allocation
from operations.dejem.models.allocation_audit import AllocationAudit


class AllocationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, allocation_id: int) -> Allocation | None:
        return self.db.get(Allocation, allocation_id)

    def get_by_campaign_and_officer(
        self,
        campaign_id: int,
        police_officer_id: int,
    ) -> Allocation | None:
        stmt = select(Allocation).where(
            Allocation.month_id == campaign_id,
            Allocation.user_id == police_officer_id,
        )
        return self.db.scalars(stmt).first()

    def list_by_campaign(self, campaign_id: int) -> list[Allocation]:
        stmt = (
            select(Allocation)
            .where(Allocation.month_id == campaign_id)
            .order_by(Allocation.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def add(self, row: Allocation) -> Allocation:
        self.db.add(row)
        self.db.flush()
        return row

    def save(self, row: Allocation) -> Allocation:
        self.db.add(row)
        self.db.flush()
        return row

    def delete(self, row: Allocation) -> None:
        self.db.delete(row)
        self.db.flush()

    def add_audit(self, row: AllocationAudit) -> AllocationAudit:
        self.db.add(row)
        self.db.flush()
        return row

    def list_audits(self, campaign_id: int) -> list[AllocationAudit]:
        stmt = (
            select(AllocationAudit)
            .where(AllocationAudit.campaign_id == campaign_id)
            .order_by(AllocationAudit.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())
