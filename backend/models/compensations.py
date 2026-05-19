from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class CompensationType(str, enum.Enum):
    CPJ_SUPPORT = "CPJ_SUPPORT"
    WEAPON_OCCURRENCE = "WEAPON_OCCURRENCE"
    RELEVANT_OCCURRENCE = "RELEVANT_OCCURRENCE"
    TWO_WANTED = "TWO_WANTED"
    FIVE_FLAGRANTS = "FIVE_FLAGRANTS"
    FOLGA_MENSAL = "FOLGA_MENSAL"
    COMPENSACAO = "COMPENSACAO"
    DS = "DS"


class CompensationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    REVERTED = "REVERTED"


class UserCompensationStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    USED = "USED"
    REVOKED = "REVOKED"


class CompensationLogAction(str, enum.Enum):
    CREATED = "CREATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    UPDATED = "UPDATED"
    CANCELLED = "CANCELLED"
    REVERTED = "REVERTED"


# Referência visual anual — não bloqueia criação.
DS_ANNUAL_REFERENCE_QUOTA = 5


class CompensationEvent(Base):
    __tablename__ = "compensation_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[CompensationType] = mapped_column(
        Enum(CompensationType, name="compensationtype", create_type=False),
        nullable=False,
    )
    motivo: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[CompensationStatus] = mapped_column(
        Enum(CompensationStatus, name="compensationstatus", create_type=False),
        nullable=False,
        default=CompensationStatus.PENDING,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    decided_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_motivo: Mapped[str | None] = mapped_column(Text(), nullable=True)
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

    participants: Mapped[list["CompensationEventParticipant"]] = relationship(
        "CompensationEventParticipant",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    credits: Mapped[list["UserCompensation"]] = relationship(
        "UserCompensation",
        back_populates="event",
    )
    logs: Mapped[list["CompensationEventLog"]] = relationship(
        "CompensationEventLog",
        back_populates="event",
        order_by="CompensationEventLog.created_at.desc()",
    )


class CompensationEventLog(Base):
    __tablename__ = "compensation_event_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    compensation_event_id: Mapped[int] = mapped_column(
        ForeignKey("compensation_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[CompensationLogAction] = mapped_column(
        Enum(CompensationLogAction, name="compensationlogaction", create_type=False),
        nullable=False,
    )
    from_status: Mapped[CompensationStatus | None] = mapped_column(
        Enum(CompensationStatus, name="compensationstatus", create_type=False),
        nullable=True,
    )
    to_status: Mapped[CompensationStatus | None] = mapped_column(
        Enum(CompensationStatus, name="compensationstatus", create_type=False),
        nullable=True,
    )
    motivo: Mapped[str | None] = mapped_column(Text(), nullable=True)
    details: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped["CompensationEvent"] = relationship("CompensationEvent", back_populates="logs")


class CompensationEventParticipant(Base):
    __tablename__ = "compensation_event_participants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    compensation_event_id: Mapped[int] = mapped_column(
        ForeignKey("compensation_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    event: Mapped["CompensationEvent"] = relationship("CompensationEvent", back_populates="participants")


class UserCompensation(Base):
    __tablename__ = "user_compensations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    compensation_event_id: Mapped[int] = mapped_column(
        ForeignKey("compensation_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[UserCompensationStatus] = mapped_column(
        Enum(UserCompensationStatus, name="usercompensationstatus", create_type=False),
        nullable=False,
        default=UserCompensationStatus.AVAILABLE,
    )
    display_label: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    used_leave_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("leave_requests.id"),
        nullable=True,
        unique=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    event: Mapped["CompensationEvent"] = relationship("CompensationEvent", back_populates="credits")
