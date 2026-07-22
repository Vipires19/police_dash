"""ShiftSlotRepository — turnos + capacidade (C8)."""

from __future__ import annotations

from datetime import date as DateValue

from sqlalchemy import select
from sqlalchemy.orm import Session

from operations.dejem.models.enums import ShiftSlotStatus
from operations.dejem.models.reservation_audit import CreditReservationAudit
from operations.dejem.models.shift_slot import ShiftSlot


class ShiftSlotRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, slot_id: int) -> ShiftSlot | None:
        return self.db.get(ShiftSlot, slot_id)

    def get_for_update(self, slot_id: int) -> ShiftSlot | None:
        stmt = (
            select(ShiftSlot)
            .where(ShiftSlot.id == slot_id)
            .with_for_update()
        )
        return self.db.scalars(stmt).first()

    def list_by_campaign(
        self,
        campaign_id: int,
        *,
        on_date: DateValue | None = None,
        status: ShiftSlotStatus | None = None,
    ) -> list[ShiftSlot]:
        stmt = select(ShiftSlot).where(ShiftSlot.campaign_id == campaign_id)
        if on_date is not None:
            stmt = stmt.where(ShiftSlot.date == on_date)
        if status is not None:
            stmt = stmt.where(ShiftSlot.status == status)
        stmt = stmt.order_by(ShiftSlot.date.asc(), ShiftSlot.start_time.asc())
        return list(self.db.scalars(stmt).all())

    def list_available(self, campaign_id: int) -> list[ShiftSlot]:
        stmt = (
            select(ShiftSlot)
            .where(
                ShiftSlot.campaign_id == campaign_id,
                ShiftSlot.status == ShiftSlotStatus.OPEN,
                ShiftSlot.remaining_slots > 0,
            )
            .order_by(ShiftSlot.date.asc(), ShiftSlot.start_time.asc())
        )
        return list(self.db.scalars(stmt).all())

    def add(self, row: ShiftSlot) -> ShiftSlot:
        self.db.add(row)
        self.db.flush()
        return row

    def save(self, row: ShiftSlot) -> ShiftSlot:
        self.db.add(row)
        self.db.flush()
        return row

    def delete(self, row: ShiftSlot) -> None:
        self.db.delete(row)
        self.db.flush()

    def add_reservation_audit(self, row: CreditReservationAudit) -> CreditReservationAudit:
        self.db.add(row)
        self.db.flush()
        return row

    def list_reservation_audits(self, credit_id: int) -> list[CreditReservationAudit]:
        stmt = (
            select(CreditReservationAudit)
            .where(CreditReservationAudit.credit_id == credit_id)
            .order_by(CreditReservationAudit.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())
