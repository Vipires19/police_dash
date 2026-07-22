"""PublishedSchedule — publicação versionada DEJEM (Sprint C10)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from operations.dejem.models.enums import PublishedScheduleStatus

if TYPE_CHECKING:
    from models.dejem import DejemMonth
    from models.user import User


class PublishedSchedule(Base):
    """Versão publicada da escala operacional DEJEM (snapshot imutável)."""

    __tablename__ = "dejem_published_schedules"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "version",
            name="uq_dejem_published_campaign_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    published_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PublishedScheduleStatus] = mapped_column(
        Enum(PublishedScheduleStatus, name="dejempublishedschedulestatus", create_type=False),
        nullable=False,
        default=PublishedScheduleStatus.ACTIVE,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    snapshot_json: Mapped[str] = mapped_column(Text(), nullable=False)
    mapa_payload_json: Mapped[str] = mapped_column(Text(), nullable=False, default="[]")
    change_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    previous_publication_id: Mapped[int | None] = mapped_column(
        ForeignKey("dejem_published_schedules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    campaign: Mapped[DejemMonth] = relationship("DejemMonth", foreign_keys=[campaign_id])
    publisher: Mapped[User] = relationship("User", foreign_keys=[published_by])
    previous: Mapped[PublishedSchedule | None] = relationship(
        "PublishedSchedule",
        remote_side="PublishedSchedule.id",
        foreign_keys=[previous_publication_id],
    )


class PublishedScheduleAudit(Base):
    __tablename__ = "dejem_published_schedule_audits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    publication_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_published_schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    publication: Mapped[PublishedSchedule] = relationship(
        "PublishedSchedule",
        foreign_keys=[publication_id],
    )
