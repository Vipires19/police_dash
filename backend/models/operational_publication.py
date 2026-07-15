"""Domínio OperationalPublication — documento oficial do serviço do dia (fase 4.10)."""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class OperationalPublicationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class OperationalPublicationAuditAction(str, enum.Enum):
    CREATED = "CREATED"
    REFRESHED = "REFRESHED"
    VALIDATED = "VALIDATED"
    PUBLISHED = "PUBLISHED"
    REPUBLISHED = "REPUBLISHED"
    ARCHIVED = "ARCHIVED"
    RISK_ACK = "RISK_ACK"


class OperationalPublication(Base):
    """Snapshot oficial e versionado do serviço operacional do dia."""

    __tablename__ = "operational_publications"
    __table_args__ = (
        UniqueConstraint(
            "service_scale_id",
            "version",
            name="uq_operational_publications_scale_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    service_scale_id: Mapped[int] = mapped_column(
        ForeignKey("service_scales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scale_date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    publication_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[OperationalPublicationStatus] = mapped_column(
        Enum(OperationalPublicationStatus, name="operationalpublicationstatus", create_type=False),
        nullable=False,
        default=OperationalPublicationStatus.DRAFT,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    published_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    generated_pdf: Mapped[str | None] = mapped_column(Text(), nullable=True)
    snapshot_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    checklist_json: Mapped[str | None] = mapped_column(Text(), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    publish_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    risk_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Preparado para comparação Versão N × Versão N-1
    previous_publication_id: Mapped[int | None] = mapped_column(
        ForeignKey("operational_publications.id", ondelete="SET NULL"),
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
    published_by: Mapped["User | None"] = relationship("User", foreign_keys=[published_by_id])
    previous_publication: Mapped["OperationalPublication | None"] = relationship(
        "OperationalPublication",
        remote_side="OperationalPublication.id",
        foreign_keys=[previous_publication_id],
    )
    audits: Mapped[list["OperationalPublicationAudit"]] = relationship(
        "OperationalPublicationAudit",
        back_populates="publication",
        cascade="all, delete-orphan",
        order_by="OperationalPublicationAudit.created_at.desc()",
    )


class OperationalPublicationAudit(Base):
    __tablename__ = "operational_publication_audits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    publication_id: Mapped[int] = mapped_column(
        ForeignKey("operational_publications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[OperationalPublicationAuditAction] = mapped_column(
        Enum(
            OperationalPublicationAuditAction,
            name="operationalpublicationauditaction",
            create_type=False,
        ),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    details: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    publication: Mapped["OperationalPublication"] = relationship(
        "OperationalPublication",
        back_populates="audits",
    )
    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])


from typing import TYPE_CHECKING  # noqa: E402

if TYPE_CHECKING:
    from models.user import User
