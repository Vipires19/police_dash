"""OperationalTeamRepository — equipes e assignments (C9)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from operations.dejem.models.operational_team import (
    OperationalAssignment,
    OperationalTeam,
    OperationalTeamAudit,
)


class OperationalTeamRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, team_id: int) -> OperationalTeam | None:
        stmt = (
            select(OperationalTeam)
            .where(OperationalTeam.id == team_id)
            .options(selectinload(OperationalTeam.assignments))
        )
        return self.db.scalars(stmt).first()

    def list_by_campaign(self, campaign_id: int) -> list[OperationalTeam]:
        stmt = (
            select(OperationalTeam)
            .where(OperationalTeam.campaign_id == campaign_id)
            .options(selectinload(OperationalTeam.assignments))
            .order_by(OperationalTeam.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_shift_slot(self, shift_slot_id: int) -> list[OperationalTeam]:
        stmt = (
            select(OperationalTeam)
            .where(OperationalTeam.shift_slot_id == shift_slot_id)
            .options(selectinload(OperationalTeam.assignments))
            .order_by(OperationalTeam.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_for_user(self, user_id: int, campaign_id: int | None = None) -> list[OperationalTeam]:
        stmt = (
            select(OperationalTeam)
            .join(OperationalAssignment)
            .where(OperationalAssignment.user_id == user_id)
            .options(selectinload(OperationalTeam.assignments))
            .order_by(OperationalTeam.id.asc())
        )
        if campaign_id is not None:
            stmt = stmt.where(OperationalTeam.campaign_id == campaign_id)
        return list(self.db.scalars(stmt).unique().all())

    def get_assignment(self, assignment_id: int) -> OperationalAssignment | None:
        return self.db.get(OperationalAssignment, assignment_id)

    def get_assignment_by_credit(self, credit_id: int) -> OperationalAssignment | None:
        stmt = select(OperationalAssignment).where(
            OperationalAssignment.credit_id == credit_id
        )
        return self.db.scalars(stmt).first()

    def find_vehicle_on_slot(
        self,
        shift_slot_id: int,
        vehicle_id: int,
        *,
        exclude_team_id: int | None = None,
    ) -> OperationalTeam | None:
        stmt = select(OperationalTeam).where(
            OperationalTeam.shift_slot_id == shift_slot_id,
            OperationalTeam.vehicle_id == vehicle_id,
        )
        if exclude_team_id is not None:
            stmt = stmt.where(OperationalTeam.id != exclude_team_id)
        return self.db.scalars(stmt).first()

    def add(self, row: OperationalTeam) -> OperationalTeam:
        self.db.add(row)
        self.db.flush()
        return row

    def save(self, row: OperationalTeam) -> OperationalTeam:
        self.db.add(row)
        self.db.flush()
        return row

    def delete(self, row: OperationalTeam) -> None:
        self.db.delete(row)
        self.db.flush()

    def add_assignment(self, row: OperationalAssignment) -> OperationalAssignment:
        self.db.add(row)
        self.db.flush()
        return row

    def delete_assignment(self, row: OperationalAssignment) -> None:
        self.db.delete(row)
        self.db.flush()

    def add_audit(self, row: OperationalTeamAudit) -> OperationalTeamAudit:
        self.db.add(row)
        self.db.flush()
        return row

    def list_audits(self, team_id: int) -> list[OperationalTeamAudit]:
        stmt = (
            select(OperationalTeamAudit)
            .where(OperationalTeamAudit.team_id == team_id)
            .order_by(OperationalTeamAudit.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())
