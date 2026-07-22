"""ShiftSlot — turno compartilhado disponível para reserva (Sprint C8)."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from operations.dejem.models.enums import ShiftSlotStatus

if TYPE_CHECKING:
    from models.dejem import DejemMonth
    from operations.dejem.models.credit import Credit


class ShiftSlot(Base):
    """Recurso de capacidade: data + intervalo + vagas.

    Créditos APPROVED reservam este slot (1 crédito = 1 vaga).
    Montagem de equipes/viaturas fica na C9.
    """

    __tablename__ = "dejem_shift_slots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    total_slots: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remaining_slots: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ShiftSlotStatus] = mapped_column(
        Enum(ShiftSlotStatus, name="dejemshiftslotstatus", create_type=False),
        nullable=False,
        default=ShiftSlotStatus.OPEN,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    campaign: Mapped[DejemMonth] = relationship("DejemMonth", foreign_keys=[campaign_id])
    reservations: Mapped[list[Credit]] = relationship(
        "Credit",
        back_populates="shift_slot",
        foreign_keys="Credit.shift_slot_id",
    )

    def sync_capacity(self) -> None:
        """Recalcula remaining e status OPEN/FULL (preserva CLOSED)."""
        self.remaining_slots = max(0, self.total_slots - self.reserved_slots)
        if self.status == ShiftSlotStatus.CLOSED:
            return
        self.status = (
            ShiftSlotStatus.FULL
            if self.remaining_slots <= 0
            else ShiftSlotStatus.OPEN
        )
