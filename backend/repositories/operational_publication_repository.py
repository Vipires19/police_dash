"""Repositório do domínio OperationalPublication."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.operational_publication import (
    OperationalPublication,
    OperationalPublicationAudit,
    OperationalPublicationStatus,
)


class OperationalPublicationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, publication_id: int) -> OperationalPublication | None:
        return self.db.scalars(
            select(OperationalPublication)
            .where(OperationalPublication.id == publication_id)
            .options(
                joinedload(OperationalPublication.created_by),
                joinedload(OperationalPublication.published_by),
                joinedload(OperationalPublication.audits).joinedload(
                    OperationalPublicationAudit.actor
                ),
            )
        ).unique().first()

    def get_active_workspace(self, service_scale_id: int) -> OperationalPublication | None:
        return self.db.scalars(
            select(OperationalPublication)
            .where(
                OperationalPublication.service_scale_id == service_scale_id,
                OperationalPublication.status.in_(
                    [
                        OperationalPublicationStatus.DRAFT,
                        OperationalPublicationStatus.READY,
                    ]
                ),
            )
            .order_by(OperationalPublication.updated_at.desc())
            .limit(1)
            .options(
                joinedload(OperationalPublication.created_by),
                joinedload(OperationalPublication.published_by),
            )
        ).unique().first()

    def list_published_for_scale(self, service_scale_id: int) -> list[OperationalPublication]:
        return list(
            self.db.scalars(
                select(OperationalPublication)
                .where(
                    OperationalPublication.service_scale_id == service_scale_id,
                    OperationalPublication.status == OperationalPublicationStatus.PUBLISHED,
                )
                .order_by(OperationalPublication.version.desc())
                .options(
                    joinedload(OperationalPublication.published_by),
                    joinedload(OperationalPublication.created_by),
                )
            ).unique().all()
        )

    def list_history(
        self,
        *,
        scale_date: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OperationalPublication], int]:
        filters = [
            OperationalPublication.status.in_(
                [
                    OperationalPublicationStatus.PUBLISHED,
                    OperationalPublicationStatus.ARCHIVED,
                ]
            )
        ]
        if scale_date is not None:
            filters.append(OperationalPublication.scale_date == scale_date)
        total = int(
            self.db.scalar(
                select(func.count()).select_from(OperationalPublication).where(*filters)
            )
            or 0
        )
        rows = list(
            self.db.scalars(
                select(OperationalPublication)
                .where(*filters)
                .order_by(
                    OperationalPublication.published_at.desc().nullslast(),
                    OperationalPublication.id.desc(),
                )
                .offset(offset)
                .limit(limit)
                .options(
                    joinedload(OperationalPublication.published_by),
                    joinedload(OperationalPublication.created_by),
                )
            ).unique().all()
        )
        return rows, total

    def next_version(self, service_scale_id: int) -> int:
        current = self.db.scalar(
            select(func.max(OperationalPublication.version)).where(
                OperationalPublication.service_scale_id == service_scale_id
            )
        )
        return int(current or 0) + 1

    def next_publication_number(self) -> int:
        current = self.db.scalar(select(func.max(OperationalPublication.publication_number)))
        return int(current or 0) + 1

    def latest_published(self, service_scale_id: int) -> OperationalPublication | None:
        return self.db.scalars(
            select(OperationalPublication)
            .where(
                OperationalPublication.service_scale_id == service_scale_id,
                OperationalPublication.status == OperationalPublicationStatus.PUBLISHED,
            )
            .order_by(OperationalPublication.version.desc())
            .limit(1)
            .options(joinedload(OperationalPublication.published_by))
        ).unique().first()

    def add(self, row: OperationalPublication) -> OperationalPublication:
        self.db.add(row)
        self.db.flush()
        return row

    def add_audit(self, audit: OperationalPublicationAudit) -> None:
        self.db.add(audit)
        self.db.flush()
