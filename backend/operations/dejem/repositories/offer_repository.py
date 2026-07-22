"""OfferRepository — eventos de oferta."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from operations.dejem.models.offer_event import OfferEvent


class OfferRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, offer_event_id: int) -> OfferEvent | None:
        return self.db.get(OfferEvent, offer_event_id)

    def list_by_campaign(self, campaign_id: int) -> list[OfferEvent]:
        stmt = (
            select(OfferEvent)
            .where(OfferEvent.campaign_id == campaign_id)
            .order_by(OfferEvent.created_at.asc(), OfferEvent.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def sum_quantity(self, campaign_id: int) -> int:
        stmt = select(func.coalesce(func.sum(OfferEvent.quantity), 0)).where(
            OfferEvent.campaign_id == campaign_id
        )
        return int(self.db.scalar(stmt) or 0)

    def count_by_campaign(self, campaign_id: int) -> int:
        stmt = select(func.count()).select_from(OfferEvent).where(
            OfferEvent.campaign_id == campaign_id
        )
        return int(self.db.scalar(stmt) or 0)

    def add(self, row: OfferEvent) -> OfferEvent:
        self.db.add(row)
        self.db.flush()
        return row

    def save(self, row: OfferEvent) -> OfferEvent:
        self.db.add(row)
        self.db.flush()
        return row

    def delete(self, row: OfferEvent) -> None:
        self.db.delete(row)
        self.db.flush()
