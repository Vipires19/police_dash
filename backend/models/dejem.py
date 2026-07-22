from __future__ import annotations

import enum
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from operations.dejem.models.enums import AssignmentRole


class DejemMonthStatus(str, enum.Enum):
    CREATED = "CREATED"
    OPEN_INTEREST = "OPEN_INTEREST"
    DISTRIBUTED_PENDING = "DISTRIBUTED_PENDING"
    DISTRIBUTED = "DISTRIBUTED"
    OPEN_SHIFTS = "OPEN_SHIFTS"
    FINISHED = "FINISHED"


class DejemShiftStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    READY_FOR_MAP = "READY_FOR_MAP"
    INTEGRATED = "INTEGRATED"
    FINISHED = "FINISHED"


class DejemShiftType(str, enum.Enum):
    FT = "FT"
    ROCAM = "ROCAM"
    OUTROS = "OUTROS"


class ParticipationType(str, enum.Enum):
    NORMAL = "NORMAL"
    EXTRAORDINARY = "EXTRAORDINARY"
    SUBSTITUTION = "SUBSTITUTION"


class ParticipantStatus(str, enum.Enum):
    REGISTERED = "REGISTERED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class DejemEnrollmentAction(str, enum.Enum):
    ENROLLED = "ENROLLED"
    CANCELLED = "CANCELLED"
    ADMIN_ADDED = "ADMIN_ADDED"
    ADMIN_REMOVED = "ADMIN_REMOVED"
    CLOSED = "CLOSED"
    INTEGRATED = "INTEGRATED"
    MAP_REOPENED = "MAP_REOPENED"


class DejemMonth(Base):
    __tablename__ = "dejem_months"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_dejem_months_year_month"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    total_available_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_limit_per_officer: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    undistributed_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    offer_excess_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[DejemMonthStatus] = mapped_column(
        Enum(DejemMonthStatus, name="dejemmonthstatus", create_type=False),
        nullable=False,
        default=DejemMonthStatus.OPEN_INTEREST,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
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

    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    interests: Mapped[list["DejemInterest"]] = relationship(
        "DejemInterest",
        back_populates="month",
        cascade="all, delete-orphan",
    )
    allocations: Mapped[list["DejemAllocation"]] = relationship(
        "DejemAllocation",
        back_populates="month",
        cascade="all, delete-orphan",
    )
    shifts: Mapped[list["DejemShift"]] = relationship(
        "DejemShift",
        back_populates="month",
        cascade="all, delete-orphan",
    )


class DejemInterest(Base):
    __tablename__ = "dejem_interests"
    __table_args__ = (
        UniqueConstraint("month_id", "user_id", name="uq_dejem_interests_month_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    month_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    interested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    desired_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    month: Mapped["DejemMonth"] = relationship("DejemMonth", back_populates="interests")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class DejemAllocation(Base):
    __tablename__ = "dejem_allocations"
    __table_args__ = (
        UniqueConstraint("month_id", "user_id", name="uq_dejem_allocations_month_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    month_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    allocated_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remaining_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    month: Mapped["DejemMonth"] = relationship("DejemMonth", back_populates="allocations")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class DejemShift(Base):
    __tablename__ = "dejem_shifts"
    __table_args__ = (
        UniqueConstraint(
            "month_id",
            "date",
            "start_time",
            "end_time",
            name="uq_dejem_shifts_month_date_start_end",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    month_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time(), nullable=False)
    end_time: Mapped[time] = mapped_column(Time(), nullable=False)
    shift_type: Mapped[DejemShiftType] = mapped_column(
        Enum(DejemShiftType, name="dejemshifttype", create_type=False),
        nullable=False,
        default=DejemShiftType.FT,
        index=True,
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mission_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[DejemShiftStatus] = mapped_column(
        Enum(DejemShiftStatus, name="dejemshiftstatus", create_type=False),
        nullable=False,
        default=DejemShiftStatus.OPEN,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id"),
        nullable=True,
        index=True,
    )
    service_scale_id: Mapped[int | None] = mapped_column(
        ForeignKey("service_scales.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    integrated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    integrated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
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

    month: Mapped["DejemMonth"] = relationship("DejemMonth", back_populates="shifts")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    closed_by: Mapped["User | None"] = relationship("User", foreign_keys=[closed_by_id])
    integrated_by: Mapped["User | None"] = relationship("User", foreign_keys=[integrated_by_id])
    vehicle: Mapped["Vehicle | None"] = relationship("Vehicle", foreign_keys=[vehicle_id])
    participants: Mapped[list["DejemParticipant"]] = relationship(
        "DejemParticipant",
        back_populates="shift",
        cascade="all, delete-orphan",
    )


class DejemShiftTemplate(Base):
    __tablename__ = "dejem_shift_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    shift_type: Mapped[DejemShiftType] = mapped_column(
        Enum(DejemShiftType, name="dejemshifttype", create_type=False),
        nullable=False,
        default=DejemShiftType.FT,
        index=True,
    )
    start_time: Mapped[time] = mapped_column(Time(), nullable=False)
    end_time: Mapped[time] = mapped_column(Time(), nullable=False)
    default_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
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

    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])


class DejemParticipant(Base):
    __tablename__ = "dejem_participants"
    __table_args__ = (
        UniqueConstraint("shift_id", "user_id", name="uq_dejem_participants_shift_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    shift_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_shifts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    participation_type: Mapped[ParticipationType] = mapped_column(
        Enum(ParticipationType, name="participationtype", create_type=False),
        nullable=False,
        default=ParticipationType.NORMAL,
    )
    role: Mapped[AssignmentRole] = mapped_column(
        Enum(AssignmentRole, name="dejemassignmentrole", create_type=False),
        nullable=False,
        default=AssignmentRole.MEMBER,
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        Enum(ParticipantStatus, name="participantstatus", create_type=False),
        nullable=False,
        default=ParticipantStatus.REGISTERED,
        index=True,
    )
    enrolled_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    consumes_balance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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

    shift: Mapped["DejemShift"] = relationship("DejemShift", back_populates="participants")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    enrolled_by: Mapped["User | None"] = relationship("User", foreign_keys=[enrolled_by_id])
    cancelled_by: Mapped["User | None"] = relationship("User", foreign_keys=[cancelled_by_id])


class DejemEnrollmentAudit(Base):
    __tablename__ = "dejem_enrollment_audits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    action: Mapped[DejemEnrollmentAction] = mapped_column(
        Enum(DejemEnrollmentAction, name="dejemenrollmentaction", create_type=False),
        nullable=False,
        index=True,
    )
    shift_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_shifts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_id: Mapped[int | None] = mapped_column(
        ForeignKey("dejem_participants.id", ondelete="SET NULL"),
        nullable=True,
    )
    subject_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    details: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])
    subject: Mapped["User | None"] = relationship("User", foreign_keys=[subject_user_id])
