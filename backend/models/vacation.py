from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class VacationType(str, enum.Enum):
    FERIAS = "FERIAS"
    LP = "LP"


class VacationStatus(str, enum.Enum):
    PENDING = "PENDING"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class VacationLogAction(str, enum.Enum):
    CREATED = "CREATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    UPDATED = "UPDATED"


class VacationRequest(Base):
    __tablename__ = "vacation_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    vacation_type: Mapped[VacationType] = mapped_column(
        Enum(VacationType, name="vacationtype", create_type=False),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    total_days: Mapped[int] = mapped_column(Integer(), nullable=False)
    status: Mapped[VacationStatus] = mapped_column(
        Enum(VacationStatus, name="vacationstatus", create_type=False),
        nullable=False,
        default=VacationStatus.PENDING,
    )
    review_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    approval_logs: Mapped[list["VacationApprovalLog"]] = relationship(
        "VacationApprovalLog",
        back_populates="vacation_request",
        cascade="all, delete-orphan",
    )


class VacationApprovalLog(Base):
    __tablename__ = "vacation_approval_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vacation_request_id: Mapped[int] = mapped_column(
        ForeignKey("vacation_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[VacationLogAction] = mapped_column(
        Enum(VacationLogAction, name="vacationlogaction", create_type=False),
        nullable=False,
    )
    from_status: Mapped[VacationStatus | None] = mapped_column(
        Enum(VacationStatus, name="vacationstatus", create_type=False),
        nullable=True,
    )
    to_status: Mapped[VacationStatus | None] = mapped_column(
        Enum(VacationStatus, name="vacationstatus", create_type=False),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    vacation_request: Mapped["VacationRequest"] = relationship(
        "VacationRequest",
        back_populates="approval_logs",
    )
