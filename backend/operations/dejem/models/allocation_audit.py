"""Auditoria de status de Credit e de mutações de Allocation."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.dejem import DejemAllocation, DejemMonth
    from models.user import User
    from operations.dejem.models.credit import Credit


class CreditStatusAudit(Base):
    __tablename__ = "dejem_credit_status_audits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    credit_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_credits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    origin: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    credit: Mapped[Credit] = relationship("Credit", foreign_keys=[credit_id])
    campaign: Mapped[DejemMonth] = relationship("DejemMonth", foreign_keys=[campaign_id])
    actor: Mapped[User] = relationship("User", foreign_keys=[actor_id])


class AllocationAudit(Base):
    __tablename__ = "dejem_allocation_audits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    allocation_id: Mapped[int | None] = mapped_column(
        ForeignKey("dejem_allocations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    details: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    allocation: Mapped[DejemAllocation | None] = relationship(
        "DejemAllocation",
        foreign_keys=[allocation_id],
    )
    campaign: Mapped[DejemMonth] = relationship("DejemMonth", foreign_keys=[campaign_id])
    actor: Mapped[User] = relationship("User", foreign_keys=[actor_id])
