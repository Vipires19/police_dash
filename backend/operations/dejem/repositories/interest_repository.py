"""InterestRepository — persistência de interesses (`dejem_interests`)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.user import OrganizationalUnit, User
from operations.dejem.models.interest import Interest


class InterestRepository:
    """Acesso a interesses. Commit fica no service."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, interest_id: int) -> Interest | None:
        return self.db.get(Interest, interest_id)

    def get_by_campaign_and_officer(
        self,
        campaign_id: int,
        police_officer_id: int,
    ) -> Interest | None:
        stmt = select(Interest).where(
            Interest.month_id == campaign_id,
            Interest.user_id == police_officer_id,
        )
        return self.db.scalars(stmt).first()

    def list_by_campaign(
        self,
        campaign_id: int,
        *,
        organizational_unit: OrganizationalUnit | None = None,
        only_interested: bool = True,
    ) -> list[Interest]:
        stmt = (
            select(Interest)
            .options(joinedload(Interest.user))
            .where(Interest.month_id == campaign_id)
        )
        if only_interested:
            stmt = stmt.where(Interest.interested.is_(True))
        if organizational_unit is not None:
            stmt = stmt.join(User, Interest.user_id == User.id).where(
                User.organizational_unit == organizational_unit
            )
        stmt = stmt.order_by(Interest.created_at.asc())
        return list(self.db.scalars(stmt).unique().all())

    def statistics(self, campaign_id: int) -> dict[str, float | int]:
        stmt = select(
            func.count(Interest.id),
            func.coalesce(func.sum(Interest.desired_slots), 0),
            func.coalesce(func.avg(Interest.desired_slots), 0),
            func.coalesce(func.max(Interest.desired_slots), 0),
            func.coalesce(func.min(Interest.desired_slots), 0),
        ).where(
            Interest.month_id == campaign_id,
            Interest.interested.is_(True),
        )
        count, total, avg, max_v, min_v = self.db.execute(stmt).one()
        return {
            "interested_officers": int(count or 0),
            "total_desired_slots": int(total or 0),
            "average_desired_slots": float(avg or 0),
            "max_desired_slots": int(max_v or 0),
            "min_desired_slots": int(min_v or 0),
        }

    def add(self, row: Interest) -> Interest:
        self.db.add(row)
        self.db.flush()
        return row

    def save(self, row: Interest) -> Interest:
        self.db.add(row)
        self.db.flush()
        return row

    def delete(self, row: Interest) -> None:
        self.db.delete(row)
        self.db.flush()
