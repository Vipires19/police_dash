from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class LeaveType(str, enum.Enum):
    MONTHLY = "MONTHLY"
    COMPENSATION = "COMPENSATION"


class LeaveStatus(str, enum.Enum):
    PENDING = "PENDING"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LeaveLogAction(str, enum.Enum):
    CREATED = "CREATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    UPDATED = "UPDATED"


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    leave_on: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    leave_type: Mapped[LeaveType] = mapped_column(
        Enum(LeaveType, name="leavetype", create_type=False),
        nullable=False,
    )
    user_compensation_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_compensations.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[LeaveStatus] = mapped_column(
        Enum(LeaveStatus, name="leavestatus", create_type=False),
        nullable=False,
        default=LeaveStatus.PENDING,
    )
    review_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    decision_motivo: Mapped[str | None] = mapped_column(Text(), nullable=True)
    decided_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    user_compensation: Mapped["UserCompensation | None"] = relationship(
        "UserCompensation",
        foreign_keys=[user_compensation_id],
    )
    approval_logs: Mapped[list["LeaveApprovalLog"]] = relationship(
        "LeaveApprovalLog",
        back_populates="leave_request",
        cascade="all, delete-orphan",
    )


class LeaveApprovalLog(Base):
    __tablename__ = "leave_approval_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    leave_request_id: Mapped[int] = mapped_column(
        ForeignKey("leave_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[LeaveLogAction] = mapped_column(
        Enum(LeaveLogAction, name="leavelogaction", create_type=False),
        nullable=False,
    )
    from_status: Mapped[LeaveStatus | None] = mapped_column(
        Enum(LeaveStatus, name="leavestatus", create_type=False),
        nullable=True,
    )
    to_status: Mapped[LeaveStatus | None] = mapped_column(
        Enum(LeaveStatus, name="leavestatus", create_type=False),
        nullable=True,
    )
    motivo: Mapped[str | None] = mapped_column(Text(), nullable=True)
    details: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    leave_request: Mapped["LeaveRequest"] = relationship("LeaveRequest", back_populates="approval_logs")
