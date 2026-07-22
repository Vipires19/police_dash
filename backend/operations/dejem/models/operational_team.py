"""OperationalTeam + OperationalAssignment — planejamento (Sprint C9)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from operations.dejem.models.enums import AssignmentRole, TeamStatus, TeamType

if TYPE_CHECKING:
    from models.dejem import DejemMonth
    from models.user import User
    from models.vehicle import Vehicle
    from operations.dejem.models.credit import Credit
    from operations.dejem.models.shift_slot import ShiftSlot


class OperationalTeam(Base):
    """Equipe planejada sobre um ShiftSlot (sem publicação)."""

    __tablename__ = "dejem_operational_teams"
    __table_args__ = (
        UniqueConstraint(
            "shift_slot_id",
            "vehicle_id",
            name="uq_dejem_op_team_slot_vehicle",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shift_slot_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_shift_slots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_type: Mapped[TeamType] = mapped_column(
        Enum(TeamType, name="dejemteamtype", create_type=False),
        nullable=False,
        index=True,
    )
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    commander_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[TeamStatus] = mapped_column(
        Enum(TeamStatus, name="dejemteamstatus", create_type=False),
        nullable=False,
        default=TeamStatus.DRAFT,
        index=True,
    )
    max_members: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
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
    shift_slot: Mapped[ShiftSlot] = relationship("ShiftSlot", foreign_keys=[shift_slot_id])
    vehicle: Mapped[Vehicle | None] = relationship("Vehicle", foreign_keys=[vehicle_id])
    commander: Mapped[User | None] = relationship("User", foreign_keys=[commander_id])
    assignments: Mapped[list[OperationalAssignment]] = relationship(
        "OperationalAssignment",
        back_populates="team",
        cascade="all, delete-orphan",
    )


class OperationalAssignment(Base):
    """Policial (via Credit) alocado em uma equipe."""

    __tablename__ = "dejem_operational_assignments"
    __table_args__ = (
        UniqueConstraint("credit_id", name="uq_dejem_op_assignment_credit"),
        UniqueConstraint(
            "operational_team_id",
            "user_id",
            name="uq_dejem_op_assignment_team_user",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operational_team_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_operational_teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    credit_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_credits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[AssignmentRole] = mapped_column(
        Enum(AssignmentRole, name="dejemassignmentrole", create_type=False),
        nullable=False,
        default=AssignmentRole.MEMBER,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    team: Mapped[OperationalTeam] = relationship(
        "OperationalTeam",
        back_populates="assignments",
        foreign_keys=[operational_team_id],
    )
    credit: Mapped[Credit] = relationship("Credit", foreign_keys=[credit_id])
    user: Mapped[User] = relationship("User", foreign_keys=[user_id])


class OperationalTeamAudit(Base):
    """Auditoria de planejamento operacional."""

    __tablename__ = "dejem_operational_team_audits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("dejem_operational_teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    credit_id: Mapped[int | None] = mapped_column(
        ForeignKey("dejem_credits.id", ondelete="SET NULL"),
        nullable=True,
    )
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    commander_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    details: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
