from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class ScaleStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class ScaleModality(str, enum.Enum):
    FT = "FT"
    ROCAM = "ROCAM"


class ScaleLogAction(str, enum.Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    PUBLISHED = "PUBLISHED"
    UNPUBLISHED = "UNPUBLISHED"
    DEJEM_INTEGRATED = "DEJEM_INTEGRATED"
    VERSION_CREATED = "VERSION_CREATED"
    TEAM_ADDED = "TEAM_ADDED"
    TEAM_UPDATED = "TEAM_UPDATED"
    TEAM_REMOVED = "TEAM_REMOVED"
    MEMBERS_CHANGED = "MEMBERS_CHANGED"
    DELETED = "DELETED"


class ServiceScale(Base):
    __tablename__ = "service_scales"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scale_date: Mapped[date] = mapped_column(Date(), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    fardamento: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[ScaleStatus] = mapped_column(
        Enum(ScaleStatus, name="scalestatus", create_type=False),
        nullable=False,
        default=ScaleStatus.DRAFT,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("service_scale_versions.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
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

    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    current_version: Mapped["ServiceScaleVersion | None"] = relationship(
        "ServiceScaleVersion",
        foreign_keys=[current_version_id],
        post_update=True,
    )
    teams: Mapped[list["ScaleTeam"]] = relationship(
        "ScaleTeam",
        back_populates="service_scale",
        cascade="all, delete-orphan",
        order_by="ScaleTeam.start_datetime",
    )
    logs: Mapped[list["ScaleLog"]] = relationship(
        "ScaleLog",
        back_populates="service_scale",
        cascade="all, delete-orphan",
        order_by="ScaleLog.created_at.desc()",
    )
    versions: Mapped[list["ServiceScaleVersion"]] = relationship(
        "ServiceScaleVersion",
        back_populates="service_scale",
        foreign_keys="ServiceScaleVersion.service_scale_id",
        cascade="all, delete-orphan",
        order_by="ServiceScaleVersion.version_number.desc()",
    )


class ScaleTeam(Base):
    __tablename__ = "scale_teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    service_scale_id: Mapped[int] = mapped_column(
        ForeignKey("service_scales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    modality: Mapped[ScaleModality] = mapped_column(
        Enum(ScaleModality, name="scalemodality", create_type=False),
        nullable=False,
    )
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True, index=True)
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mission_name: Mapped[str] = mapped_column(String(256), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    service_scale: Mapped["ServiceScale"] = relationship("ServiceScale", back_populates="teams")
    vehicle: Mapped["Vehicle | None"] = relationship("Vehicle", foreign_keys=[vehicle_id])
    members: Mapped[list["ScaleTeamMember"]] = relationship(
        "ScaleTeamMember",
        back_populates="scale_team",
        cascade="all, delete-orphan",
    )


class ScaleTeamMember(Base):
    __tablename__ = "scale_team_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scale_team_id: Mapped[int] = mapped_column(
        ForeignKey("scale_teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    assigned_vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True, index=True)
    role_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    scale_team: Mapped["ScaleTeam"] = relationship("ScaleTeam", back_populates="members")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    assigned_vehicle: Mapped["Vehicle | None"] = relationship("Vehicle", foreign_keys=[assigned_vehicle_id])


class ScaleLog(Base):
    __tablename__ = "scale_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    service_scale_id: Mapped[int] = mapped_column(
        ForeignKey("service_scales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action_type: Mapped[ScaleLogAction] = mapped_column(
        Enum(ScaleLogAction, name="scalelogaction", create_type=False),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    service_scale: Mapped["ServiceScale"] = relationship("ServiceScale", back_populates="logs")
    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])


class ServiceScaleVersion(Base):
    """Snapshot imutável de cada publicação (Mapa Força versionado)."""

    __tablename__ = "service_scale_versions"
    __table_args__ = (
        UniqueConstraint(
            "service_scale_id",
            "version_number",
            name="uq_service_scale_versions_scale_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    service_scale_id: Mapped[int] = mapped_column(
        ForeignKey("service_scales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    snapshot_json: Mapped[str] = mapped_column(Text(), nullable=False)
    export_text: Mapped[str] = mapped_column(Text(), nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    dejem_integrated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    service_scale: Mapped["ServiceScale"] = relationship(
        "ServiceScale",
        back_populates="versions",
        foreign_keys=[service_scale_id],
    )
    published_by: Mapped["User"] = relationship("User", foreign_keys=[published_by_id])


class ScaleMessageTemplate(Base):
    """Template da mensagem operacional (WhatsApp / grupo)."""

    __tablename__ = "scale_message_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    body_text: Mapped[str] = mapped_column(Text(), nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
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

    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_id])
