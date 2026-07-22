"""CreditRepository — créditos + auditoria de status."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from operations.dejem.models.allocation_audit import CreditStatusAudit
from operations.dejem.models.credit import Credit
from operations.dejem.models.enums import CreditStatus


class CreditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, credit_id: int) -> Credit | None:
        return self.db.get(Credit, credit_id)

    def get_for_update(self, credit_id: int) -> Credit | None:
        stmt = select(Credit).where(Credit.id == credit_id).with_for_update()
        return self.db.scalars(stmt).first()

    def list_by_campaign(self, campaign_id: int) -> list[Credit]:
        stmt = (
            select(Credit)
            .where(Credit.campaign_id == campaign_id)
            .order_by(Credit.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_officer(self, police_officer_id: int) -> list[Credit]:
        stmt = (
            select(Credit)
            .where(Credit.police_officer_id == police_officer_id)
            .order_by(Credit.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_allocation(self, allocation_id: int) -> list[Credit]:
        stmt = (
            select(Credit)
            .where(Credit.allocation_id == allocation_id)
            .order_by(Credit.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_status(self, campaign_id: int, status: CreditStatus) -> list[Credit]:
        stmt = (
            select(Credit)
            .where(Credit.campaign_id == campaign_id, Credit.status == status)
            .order_by(Credit.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def add(self, row: Credit) -> Credit:
        self.db.add(row)
        self.db.flush()
        return row

    def save(self, row: Credit) -> Credit:
        self.db.add(row)
        self.db.flush()
        return row

    def delete(self, row: Credit) -> None:
        self.db.delete(row)
        self.db.flush()

    def add_status_audit(self, row: CreditStatusAudit) -> CreditStatusAudit:
        self.db.add(row)
        self.db.flush()
        return row

    def list_status_audits(self, credit_id: int) -> list[CreditStatusAudit]:
        stmt = (
            select(CreditStatusAudit)
            .where(CreditStatusAudit.credit_id == credit_id)
            .order_by(CreditStatusAudit.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())
