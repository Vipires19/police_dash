"""Repositório do módulo DEJEM."""

from __future__ import annotations

from datetime import date, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.dejem import (
    DejemAllocation,
    DejemEnrollmentAudit,
    DejemInterest,
    DejemMonth,
    DejemParticipant,
    DejemShift,
    DejemShiftTemplate,
    DejemShiftType,
    ParticipantStatus,
)


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

    def save(self, row: DejemAllocation) -> DejemAllocation:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save_flush(self, row: DejemAllocation) -> DejemAllocation:
        self.db.add(row)
        self.db.flush()
        return row

    def average_remaining(self, month_id: int) -> float:
        stmt = select(func.avg(DejemAllocation.remaining_slots)).where(
            DejemAllocation.month_id == month_id,
        )
        value = self.db.scalar(stmt)
        return float(value) if value is not None else 0.0


class DejemShiftRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, shift_id: int) -> DejemShift | None:
        return self.db.scalars(
            select(DejemShift)
            .where(DejemShift.id == shift_id)
            .options(joinedload(DejemShift.vehicle))
        ).first()

    def list_by_month(self, month_id: int) -> list[DejemShift]:
        stmt = (
            select(DejemShift)
            .where(DejemShift.month_id == month_id)
            .options(joinedload(DejemShift.vehicle))
            .order_by(DejemShift.date.asc(), DejemShift.start_time.asc(), DejemShift.id.asc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def list_by_month_and_date(self, month_id: int, day: date) -> list[DejemShift]:
        stmt = (
            select(DejemShift)
            .where(DejemShift.month_id == month_id, DejemShift.date == day)
            .options(joinedload(DejemShift.vehicle))
            .order_by(DejemShift.start_time.asc(), DejemShift.id.asc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def list_same_type_on_date(
        self,
        month_id: int,
        day: date,
        shift_type: DejemShiftType,
        *,
        exclude_id: int | None = None,
    ) -> list[DejemShift]:
        stmt = select(DejemShift).where(
            DejemShift.month_id == month_id,
            DejemShift.date == day,
            DejemShift.shift_type == shift_type,
        )
        if exclude_id is not None:
            stmt = stmt.where(DejemShift.id != exclude_id)
        return list(self.db.scalars(stmt).all())

    def count_filled(self, shift_id: int) -> int:
        stmt = select(func.count()).select_from(DejemParticipant).where(
            DejemParticipant.shift_id == shift_id,
            DejemParticipant.status != ParticipantStatus.CANCELLED,
        )
        return int(self.db.scalar(stmt) or 0)

    def add(self, row: DejemShift) -> DejemShift:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save(self, row: DejemShift) -> DejemShift:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: DejemShift) -> None:
        self.db.delete(row)
        self.db.commit()

    def find_exact(
        self,
        month_id: int,
        day: date,
        shift_type: DejemShiftType,
        start_time: time,
        end_time: time,
    ) -> DejemShift | None:
        stmt = select(DejemShift).where(
            DejemShift.month_id == month_id,
            DejemShift.date == day,
            DejemShift.shift_type == shift_type,
            DejemShift.start_time == start_time,
            DejemShift.end_time == end_time,
        )
        return self.db.scalars(stmt).first()

    def add_flush(self, row: DejemShift) -> DejemShift:
        self.db.add(row)
        self.db.flush()
        return row

    def delete_flush(self, row: DejemShift) -> None:
        self.db.delete(row)
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()


class DejemParticipantRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, participant_id: int) -> DejemParticipant | None:
        return self.db.get(DejemParticipant, participant_id)

    def get_by_shift_and_user(self, shift_id: int, user_id: int) -> DejemParticipant | None:
        stmt = select(DejemParticipant).where(
            DejemParticipant.shift_id == shift_id,
            DejemParticipant.user_id == user_id,
        )
        return self.db.scalars(stmt).first()

    def list_active_by_shift(self, shift_id: int) -> list[DejemParticipant]:
        stmt = (
            select(DejemParticipant)
            .options(joinedload(DejemParticipant.user))
            .where(
                DejemParticipant.shift_id == shift_id,
                DejemParticipant.status != ParticipantStatus.CANCELLED,
            )
            .order_by(DejemParticipant.created_at.asc(), DejemParticipant.id.asc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def list_active_for_user_on_dates(
        self,
        user_id: int,
        dates: list[date],
        *,
        exclude_shift_id: int | None = None,
    ) -> list[DejemParticipant]:
        if not dates:
            return []
        stmt = (
            select(DejemParticipant)
            .options(joinedload(DejemParticipant.shift))
            .join(DejemShift, DejemParticipant.shift_id == DejemShift.id)
            .where(
                DejemParticipant.user_id == user_id,
                DejemParticipant.status != ParticipantStatus.CANCELLED,
                DejemShift.date.in_(dates),
            )
        )
        if exclude_shift_id is not None:
            stmt = stmt.where(DejemParticipant.shift_id != exclude_shift_id)
        return list(self.db.scalars(stmt).unique().all())

    def add_flush(self, row: DejemParticipant) -> DejemParticipant:
        self.db.add(row)
        self.db.flush()
        return row

    def save_flush(self, row: DejemParticipant) -> DejemParticipant:
        self.db.add(row)
        self.db.flush()
        return row

    def commit(self) -> None:
        self.db.commit()


class DejemEnrollmentAuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_flush(self, row: DejemEnrollmentAudit) -> DejemEnrollmentAudit:
        self.db.add(row)
        self.db.flush()
        return row


class DejemShiftTemplateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, template_id: int) -> DejemShiftTemplate | None:
        return self.db.get(DejemShiftTemplate, template_id)

    def list_by_ids(self, template_ids: list[int]) -> list[DejemShiftTemplate]:
        if not template_ids:
            return []
        stmt = select(DejemShiftTemplate).where(DejemShiftTemplate.id.in_(template_ids))
        return list(self.db.scalars(stmt).all())

    def list_all(self, *, active_only: bool = False) -> list[DejemShiftTemplate]:
        stmt = select(DejemShiftTemplate).order_by(
            DejemShiftTemplate.shift_type.asc(),
            DejemShiftTemplate.name.asc(),
        )
        if active_only:
            stmt = stmt.where(DejemShiftTemplate.is_active.is_(True))
        return list(self.db.scalars(stmt).all())

    def add(self, row: DejemShiftTemplate) -> DejemShiftTemplate:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save(self, row: DejemShiftTemplate) -> DejemShiftTemplate:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: DejemShiftTemplate) -> None:
        self.db.delete(row)
        self.db.commit()
