"""Repositório do módulo DEJEM."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.dejem import DejemAllocation, DejemInterest, DejemMonth


class DejemMonthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, month_id: int) -> DejemMonth | None:
        return self.db.get(DejemMonth, month_id)

    def get_by_year_month(self, year: int, month: int) -> DejemMonth | None:
        stmt = select(DejemMonth).where(DejemMonth.year == year, DejemMonth.month == month)
        return self.db.scalars(stmt).first()

    def list_all(self) -> list[DejemMonth]:
        stmt = select(DejemMonth).order_by(DejemMonth.year.desc(), DejemMonth.month.desc())
        return list(self.db.scalars(stmt).all())

    def add(self, row: DejemMonth) -> DejemMonth:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save(self, row: DejemMonth) -> DejemMonth:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def count_interested(self, month_id: int) -> int:
        stmt = select(func.count()).select_from(DejemInterest).where(
            DejemInterest.month_id == month_id,
            DejemInterest.interested.is_(True),
        )
        return int(self.db.scalar(stmt) or 0)


class DejemInterestRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, interest_id: int) -> DejemInterest | None:
        return self.db.get(DejemInterest, interest_id)

    def get_by_month_and_user(self, month_id: int, user_id: int) -> DejemInterest | None:
        stmt = select(DejemInterest).where(
            DejemInterest.month_id == month_id,
            DejemInterest.user_id == user_id,
        )
        return self.db.scalars(stmt).first()

    def list_by_month_with_users(self, month_id: int) -> list[DejemInterest]:
        stmt = (
            select(DejemInterest)
            .options(joinedload(DejemInterest.user))
            .where(DejemInterest.month_id == month_id)
            .order_by(DejemInterest.created_at.asc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def add(self, row: DejemInterest) -> DejemInterest:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save(self, row: DejemInterest) -> DejemInterest:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: DejemInterest) -> None:
        self.db.delete(row)
        self.db.commit()

    def list_interested_with_users(self, month_id: int) -> list[DejemInterest]:
        stmt = (
            select(DejemInterest)
            .options(joinedload(DejemInterest.user))
            .where(
                DejemInterest.month_id == month_id,
                DejemInterest.interested.is_(True),
            )
            .order_by(DejemInterest.id.asc())
        )
        return list(self.db.scalars(stmt).unique().all())


class DejemAllocationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_month_and_user(self, month_id: int, user_id: int) -> DejemAllocation | None:
        stmt = select(DejemAllocation).where(
            DejemAllocation.month_id == month_id,
            DejemAllocation.user_id == user_id,
        )
        return self.db.scalars(stmt).first()

    def list_by_month_with_users(self, month_id: int) -> list[DejemAllocation]:
        stmt = (
            select(DejemAllocation)
            .options(joinedload(DejemAllocation.user))
            .where(DejemAllocation.month_id == month_id)
            .order_by(DejemAllocation.id.asc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def count_by_month(self, month_id: int) -> int:
        stmt = select(func.count()).select_from(DejemAllocation).where(
            DejemAllocation.month_id == month_id,
        )
        return int(self.db.scalar(stmt) or 0)

    def delete_by_month(self, month_id: int) -> int:
        rows = list(
            self.db.scalars(
                select(DejemAllocation).where(DejemAllocation.month_id == month_id)
            ).all()
        )
        for row in rows:
            self.db.delete(row)
        self.db.commit()
        return len(rows)

    def add_many(self, rows: list[DejemAllocation]) -> list[DejemAllocation]:
        self.db.add_all(rows)
        self.db.commit()
        for row in rows:
            self.db.refresh(row)
        return rows
