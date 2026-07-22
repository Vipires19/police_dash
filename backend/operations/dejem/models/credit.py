"""Credit — crédito individual atribuído a um policial."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from operations.dejem.models.enums import CreditStatus

if TYPE_CHECKING:
    from models.dejem import DejemAllocation, DejemMonth
    from models.user import User
    from operations.dejem.models.shift_slot import ShiftSlot


class Credit(Base):
    """Unidade atômica de vaga DEJEM (identidade própria por crédito)."""

    __tablename__ = "dejem_credits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    allocation_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_allocations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    police_officer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[CreditStatus] = mapped_column(
        Enum(CreditStatus, name="dejemcreditstatus", create_type=False),
        nullable=False,
        default=CreditStatus.AVAILABLE,
        index=True,
    )
    shift_slot_id: Mapped[int | None] = mapped_column(
        ForeignKey("dejem_shift_slots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    allocation: Mapped[DejemAllocation] = relationship(
        "DejemAllocation",
        foreign_keys=[allocation_id],
    )
    campaign: Mapped[DejemMonth] = relationship("DejemMonth", foreign_keys=[campaign_id])
    police_officer: Mapped[User] = relationship("User", foreign_keys=[police_officer_id])
    shift_slot: Mapped[ShiftSlot | None] = relationship(
        "ShiftSlot",
        back_populates="reservations",
        foreign_keys=[shift_slot_id],
    )
