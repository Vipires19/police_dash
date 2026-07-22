"""Repositório de publicações DEJEM (C10 / R1)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from operations.dejem.models.enums import PublishedScheduleStatus
from operations.dejem.models.published_schedule import (
    PublishedSchedule,
    PublishedScheduleAudit,
)


class PublishedScheduleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, publication_id: int) -> PublishedSchedule | None:
        return self.db.get(PublishedSchedule, publication_id)

    def list_by_campaign(self, campaign_id: int) -> list[PublishedSchedule]:
        stmt = (
            select(PublishedSchedule)
            .where(PublishedSchedule.campaign_id == campaign_id)
            .order_by(PublishedSchedule.version.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_active(self, campaign_id: int) -> PublishedSchedule | None:
        stmt = select(PublishedSchedule).where(
            PublishedSchedule.campaign_id == campaign_id,
            PublishedSchedule.status == PublishedScheduleStatus.ACTIVE,
        )
        return self.db.scalars(stmt).first()

    def get_active_for_update(self, campaign_id: int) -> PublishedSchedule | None:
        stmt = (
            select(PublishedSchedule)
            .where(
                PublishedSchedule.campaign_id == campaign_id,
                PublishedSchedule.status == PublishedScheduleStatus.ACTIVE,
            )
            .with_for_update()
        )
        return self.db.scalars(stmt).first()

    def max_version(self, campaign_id: int) -> int:
        value = self.db.scalar(
            select(func.coalesce(func.max(PublishedSchedule.version), 0)).where(
                PublishedSchedule.campaign_id == campaign_id
            )
        )
        return int(value or 0)

    def add(self, row: PublishedSchedule) -> PublishedSchedule:
        self.db.add(row)
        self.db.flush()
        return row

    def save(self, row: PublishedSchedule) -> PublishedSchedule:
        self.db.add(row)
        self.db.flush()
        return row

    def add_audit(self, row: PublishedScheduleAudit) -> PublishedScheduleAudit:
        self.db.add(row)
        self.db.flush()
        return row

    def list_audits(self, publication_id: int) -> list[PublishedScheduleAudit]:
        stmt = (
            select(PublishedScheduleAudit)
            .where(PublishedScheduleAudit.publication_id == publication_id)
            .order_by(PublishedScheduleAudit.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())
