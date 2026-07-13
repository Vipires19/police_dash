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
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class DejemMonthStatus(str, enum.Enum):
    OPEN_INTEREST = "OPEN_INTEREST"
    DISTRIBUTED_PENDING = "DISTRIBUTED_PENDING"
    DISTRIBUTED = "DISTRIBUTED"
    OPEN_SHIFTS = "OPEN_SHIFTS"
    FINISHED = "FINISHED"


class DejemShiftStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    FINISHED = "FINISHED"


class ParticipationType(str, enum.Enum):
    NORMAL = "NORMAL"
    EXTRAORDINARY = "EXTRAORDINARY"
    SUBSTITUTION = "SUBSTITUTION"


class ParticipantStatus(str, enum.Enum):
    REGISTERED = "REGISTERED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class DejemMonth(Base):
    __tablename__ = "dejem_months"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_dejem_months_year_month"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    total_available_slots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_limit_per_officer: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    month_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time(), nullable=False)
    end_time: Mapped[time] = mapped_column(Time(), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[DejemShiftStatus] = mapped_column(
        Enum(DejemShiftStatus, name="dejemshiftstatus", create_type=False),
        nullable=False,
        default=DejemShiftStatus.OPEN,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    month: Mapped["DejemMonth"] = relationship("DejemMonth", back_populates="shifts")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    participants: Mapped[list["DejemParticipant"]] = relationship(
        "DejemParticipant",
        back_populates="shift",
        cascade="all, delete-orphan",
    )


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
    status: Mapped[ParticipantStatus] = mapped_column(
        Enum(ParticipantStatus, name="participantstatus", create_type=False),
        nullable=False,
        default=ParticipantStatus.REGISTERED,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    shift: Mapped["DejemShift"] = relationship("DejemShift", back_populates="participants")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
