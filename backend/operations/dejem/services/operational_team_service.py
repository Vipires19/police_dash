"""OperationalTeamService — planejamento operacional (Sprint C9).

Agrupa Credits reservados no mesmo ShiftSlot em equipes.
Não publica, não executa, não integra WhatsApp/Mapa Força.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.user import User
from models.vehicle import Vehicle, VehicleStatus
from operations.dejem.models.credit import Credit
from operations.dejem.models.enums import AssignmentRole, CreditStatus, TeamStatus
from operations.dejem.models.operational_team import (
    OperationalAssignment,
    OperationalTeam,
    OperationalTeamAudit,
)
from operations.dejem.repositories.campaign_repository import CampaignRepository
from operations.dejem.repositories.credit_repository import CreditRepository
from operations.dejem.repositories.operational_team_repository import (
    OperationalTeamRepository,
)
from operations.dejem.repositories.shift_slot_repository import ShiftSlotRepository
from operations.dejem.schemas.operational_team import (
    AssignmentResponse,
    OperationalTeamAuditResponse,
    OperationalTeamCreate,
    OperationalTeamResponse,
    OperationalTeamUpdate,
    TeamCommanderUpdate,
    TeamMemberCreate,
    TeamVehicleUpdate,
)
from operations.dejem.services.publication_lock import raise_if_campaign_locked

class OperationalTeamError(ValueError):
    pass

class OperationalTeamService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = OperationalTeamRepository(db)
        self.campaigns = CampaignRepository(db)
        self.slots = ShiftSlotRepository(db)
        self.credits = CreditRepository(db)

    def list(
        self,
        actor: User,
        *,
        campaign_id: int | None = None,
        shift_slot_id: int | None = None,
        admin: bool,
    ) -> list[OperationalTeamResponse]:
        if shift_slot_id is not None:
            rows = self.repo.list_by_shift_slot(shift_slot_id)
        elif campaign_id is not None:
            rows = self.repo.list_by_campaign(campaign_id)
        else:
            raise OperationalTeamError("Informe campaign_id ou shift_slot_id.")

        if not admin:
            rows = [
                t
                for t in rows
                if any(a.user_id == actor.id for a in t.assignments)
            ]
        return [self._to_response(t) for t in rows]

    def get(self, team_id: int, actor: User, *, admin: bool) -> OperationalTeamResponse:
        team = self._get_or_raise(team_id)
        if not admin and not any(a.user_id == actor.id for a in team.assignments):
            raise OperationalTeamError("Sem permissão para consultar esta equipe.")
        return self._to_response(team)

    def create(self, actor: User, body: OperationalTeamCreate) -> OperationalTeamResponse:
        self._require_campaign(body.campaign_id)
        raise_if_campaign_locked(self.db, body.campaign_id, OperationalTeamError)
        slot = self.slots.get(body.shift_slot_id)
        if not slot:
            raise OperationalTeamError("ShiftSlot não encontrado.")
        if slot.campaign_id != body.campaign_id:
            raise OperationalTeamError("ShiftSlot não pertence à campanha informada.")

        if body.vehicle_id is not None:
            self._require_vehicle(body.vehicle_id)
            self._assert_vehicle_free(body.shift_slot_id, body.vehicle_id)

        if body.commander_id is not None:
            self._require_user(body.commander_id)

        team = OperationalTeam(
            campaign_id=body.campaign_id,
            shift_slot_id=body.shift_slot_id,
            team_type=body.team_type,
            vehicle_id=body.vehicle_id,
            commander_id=body.commander_id,
            status=body.status,
            max_members=body.max_members,
            notes=body.notes,
        )
        self.repo.add(team)
        self._audit(
            team=team,
            actor=actor,
            action="CREATE",
            vehicle_id=body.vehicle_id,
            commander_id=body.commander_id,
            details=f"type={body.team_type.value} max={body.max_members}",
        )
        self.db.commit()
        team = self._get_or_raise(team.id)
        return self._to_response(team)

    def update(
        self,
        team_id: int,
        actor: User,
        body: OperationalTeamUpdate,
    ) -> OperationalTeamResponse:
        team = self._get_or_raise(team_id)
        raise_if_campaign_locked(self.db, team.campaign_id, OperationalTeamError)
        if body.max_members is not None:
            if body.max_members < len(team.assignments):
                raise OperationalTeamError(
                    f"max_members ({body.max_members}) menor que "
                    f"integrantes atuais ({len(team.assignments)})."
                )
            team.max_members = body.max_members
        if body.team_type is not None:
            team.team_type = body.team_type
        if body.notes is not None:
            team.notes = body.notes
        if body.status is not None:
            if body.status not in {TeamStatus.DRAFT, TeamStatus.READY}:
                raise OperationalTeamError("Status de publicação não permitido nesta sprint.")
            team.status = body.status

        self.repo.save(team)
        self._audit(
            team=team,
            actor=actor,
            action="UPDATE",
            details=f"type={team.team_type.value} status={team.status.value}",
        )
        self.db.commit()
        return self._to_response(self._get_or_raise(team_id))

    def delete(self, team_id: int, actor: User) -> None:
        team = self._get_or_raise(team_id)
        raise_if_campaign_locked(self.db, team.campaign_id, OperationalTeamError)
        self._audit(
            team=team,
            actor=actor,
            action="DELETE",
            details=f"members={len(team.assignments)}",
        )
        self.repo.delete(team)
        self.db.commit()

    def add_member(
        self,
        team_id: int,
        actor: User,
        body: TeamMemberCreate,
    ) -> OperationalTeamResponse:
        team = self._get_or_raise(team_id)
        raise_if_campaign_locked(self.db, team.campaign_id, OperationalTeamError)
        if len(team.assignments) >= team.max_members:
            raise OperationalTeamError(
                f"Capacidade da equipe atingida (max={team.max_members})."
            )

        credit = self._require_credit_for_team(body.credit_id, team)
        existing = self.repo.get_assignment_by_credit(credit.id)
        if existing:
            raise OperationalTeamError(
                f"Credit {credit.id} já está alocado na equipe {existing.operational_team_id}."
            )
        if any(a.user_id == credit.police_officer_id for a in team.assignments):
            raise OperationalTeamError("Policial já é membro desta equipe.")

        role = body.role
        assignment = OperationalAssignment(
            operational_team_id=team.id,
            credit_id=credit.id,
            user_id=credit.police_officer_id,
            role=role,
        )
        self.repo.add_assignment(assignment)

        if role == AssignmentRole.COMMANDER:
            team.commander_id = credit.police_officer_id
            self.repo.save(team)

        self._audit(
            team=team,
            actor=actor,
            action="ADD_MEMBER",
            user_id=credit.police_officer_id,
            credit_id=credit.id,
            details=f"role={role.value}",
        )
        self.db.commit()
        return self._to_response(self._get_or_raise(team_id))

    def remove_member(
        self,
        team_id: int,
        member_id: int,
        actor: User,
    ) -> OperationalTeamResponse:
        team = self._get_or_raise(team_id)
        raise_if_campaign_locked(self.db, team.campaign_id, OperationalTeamError)
        assignment = self.repo.get_assignment(member_id)
        if not assignment or assignment.operational_team_id != team.id:
            raise OperationalTeamError("Membro não encontrado nesta equipe.")

        user_id = assignment.user_id
        credit_id = assignment.credit_id
        if team.commander_id == user_id:
            team.commander_id = None
            self.repo.save(team)

        self.repo.delete_assignment(assignment)
        self._audit(
            team=team,
            actor=actor,
            action="REMOVE_MEMBER",
            user_id=user_id,
            credit_id=credit_id,
        )
        self.db.commit()
        return self._to_response(self._get_or_raise(team_id))

    def set_vehicle(
        self,
        team_id: int,
        actor: User,
        body: TeamVehicleUpdate,
    ) -> OperationalTeamResponse:
        team = self._get_or_raise(team_id)
        raise_if_campaign_locked(self.db, team.campaign_id, OperationalTeamError)
        if body.vehicle_id is not None:
            self._require_vehicle(body.vehicle_id)
            self._assert_vehicle_free(
                team.shift_slot_id,
                body.vehicle_id,
                exclude_team_id=team.id,
            )
        team.vehicle_id = body.vehicle_id
        self.repo.save(team)
        self._audit(
            team=team,
            actor=actor,
            action="SET_VEHICLE",
            vehicle_id=body.vehicle_id,
        )
        self.db.commit()
        return self._to_response(self._get_or_raise(team_id))

    def set_commander(
        self,
        team_id: int,
        actor: User,
        body: TeamCommanderUpdate,
    ) -> OperationalTeamResponse:
        team = self._get_or_raise(team_id)
        raise_if_campaign_locked(self.db, team.campaign_id, OperationalTeamError)
        if body.commander_id is not None:
            self._require_user(body.commander_id)
            # Preferencialmente membro; se não for, ainda permite (planejamento)
            member = next(
                (a for a in team.assignments if a.user_id == body.commander_id),
                None,
            )
            if member and member.role != AssignmentRole.COMMANDER:
                member.role = AssignmentRole.COMMANDER
            # Demote previous commander assignment roles
            for a in team.assignments:
                if (
                    a.user_id != body.commander_id
                    and a.role == AssignmentRole.COMMANDER
                ):
                    a.role = AssignmentRole.MEMBER

        team.commander_id = body.commander_id
        self.repo.save(team)
        self._audit(
            team=team,
            actor=actor,
            action="SET_COMMANDER",
            commander_id=body.commander_id,
            user_id=body.commander_id,
        )
        self.db.commit()
        return self._to_response(self._get_or_raise(team_id))

    def list_audits(self, team_id: int) -> list[OperationalTeamAuditResponse]:
        self._get_or_raise(team_id)
        return [
            OperationalTeamAuditResponse.model_validate(r)
            for r in self.repo.list_audits(team_id)
        ]

    def _require_credit_for_team(self, credit_id: int, team: OperationalTeam) -> Credit:
        credit = self.credits.get(credit_id)
        if not credit:
            raise OperationalTeamError("Crédito não encontrado.")
        if credit.campaign_id != team.campaign_id:
            raise OperationalTeamError("Crédito não pertence à campanha da equipe.")
        if credit.shift_slot_id is None:
            raise OperationalTeamError("Crédito sem reserva de ShiftSlot.")
        if credit.shift_slot_id != team.shift_slot_id:
            raise OperationalTeamError(
                "Crédito reservado em outro turno (ShiftSlot diferente)."
            )
        if credit.status not in {CreditStatus.APPROVED, CreditStatus.EXECUTED}:
            raise OperationalTeamError(
                f"Crédito deve estar APPROVED (atual={credit.status.value})."
            )
        if credit.status == CreditStatus.CANCELLED:
            raise OperationalTeamError("Crédito CANCELLED não pode ser alocado.")
        return credit

    def _require_vehicle(self, vehicle_id: int) -> Vehicle:
        vehicle = self.db.get(Vehicle, vehicle_id)
        if not vehicle:
            raise OperationalTeamError("Viatura não encontrada.")
        if vehicle.status == VehicleStatus.BAIXADA:
            raise OperationalTeamError("Viatura baixada não pode ser vinculada.")
        return vehicle

    def _assert_vehicle_free(
        self,
        shift_slot_id: int,
        vehicle_id: int,
        *,
        exclude_team_id: int | None = None,
    ) -> None:
        other = self.repo.find_vehicle_on_slot(
            shift_slot_id,
            vehicle_id,
            exclude_team_id=exclude_team_id,
        )
        if other:
            raise OperationalTeamError(
                f"Viatura já vinculada à equipe {other.id} neste turno."
            )

    def _require_user(self, user_id: int) -> User:
        user = self.db.get(User, user_id)
        if not user:
            raise OperationalTeamError("Usuário não encontrado.")
        return user

    def _require_campaign(self, campaign_id: int) -> None:
        if not self.campaigns.get(campaign_id):
            raise OperationalTeamError("Campanha DEJEM não encontrada.")

    def _get_or_raise(self, team_id: int) -> OperationalTeam:
        team = self.repo.get(team_id)
        if not team:
            raise OperationalTeamError("Equipe operacional não encontrada.")
        return team

    def _audit(
        self,
        *,
        team: OperationalTeam,
        actor: User,
        action: str,
        user_id: int | None = None,
        credit_id: int | None = None,
        vehicle_id: int | None = None,
        commander_id: int | None = None,
        details: str | None = None,
    ) -> None:
        self.repo.add_audit(
            OperationalTeamAudit(
                team_id=team.id,
                campaign_id=team.campaign_id,
                actor_id=actor.id,
                action=action,
                user_id=user_id,
                credit_id=credit_id,
                vehicle_id=vehicle_id if vehicle_id is not None else team.vehicle_id,
                commander_id=(
                    commander_id if commander_id is not None else team.commander_id
                ),
                details=details,
            )
        )

    def _to_response(self, team: OperationalTeam) -> OperationalTeamResponse:
        members = [
            AssignmentResponse.model_validate(a)
            for a in sorted(team.assignments, key=lambda x: x.id)
        ]
        return OperationalTeamResponse(
            id=team.id,
            campaign_id=team.campaign_id,
            shift_slot_id=team.shift_slot_id,
            team_type=team.team_type,
            vehicle_id=team.vehicle_id,
            commander_id=team.commander_id,
            status=team.status,
            max_members=team.max_members,
            notes=team.notes,
            member_count=len(members),
            members=members,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )
