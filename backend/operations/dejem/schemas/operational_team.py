"""Schemas — planejamento operacional (C9)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from operations.dejem.models.enums import AssignmentRole, TeamStatus, TeamType


class OperationalTeamCreate(BaseModel):
    campaign_id: int
    shift_slot_id: int
    team_type: TeamType
    max_members: int = Field(default=4, ge=1, le=50)
    vehicle_id: int | None = None
    commander_id: int | None = None
    mission_name: str | None = Field(default=None, max_length=256)
    notes: str | None = Field(default=None, max_length=2000)
    status: TeamStatus = TeamStatus.DRAFT


class OperationalTeamUpdate(BaseModel):
    team_type: TeamType | None = None
    max_members: int | None = Field(default=None, ge=1, le=50)
    mission_name: str | None = Field(default=None, max_length=256)
    notes: str | None = Field(default=None, max_length=2000)
    status: TeamStatus | None = None


class TeamMemberCreate(BaseModel):
    """Inclui membro via crédito (fluxo normal) ou user_id (God Mode)."""

    credit_id: int | None = None
    user_id: int | None = None
    role: AssignmentRole = AssignmentRole.MEMBER

    @model_validator(mode="after")
    def _require_identity(self) -> TeamMemberCreate:
        if self.credit_id is None and self.user_id is None:
            raise ValueError("Informe credit_id ou user_id (God Mode).")
        return self


class TeamMemberRoleUpdate(BaseModel):
    role: AssignmentRole


class TeamRoleAssignment(BaseModel):
    user_id: int
    role: AssignmentRole


class TeamRolesUpdate(BaseModel):
    """Atribuição em lote no padrão Escala Operacional (função → policial)."""

    assignments: list[TeamRoleAssignment] = Field(default_factory=list)


class TeamVehicleUpdate(BaseModel):
    vehicle_id: int | None = None


class TeamCommanderUpdate(BaseModel):
    commander_id: int | None = None


class AssignmentResponse(BaseModel):
    id: int
    operational_team_id: int
    credit_id: int | None
    user_id: int
    role: AssignmentRole
    created_at: datetime

    model_config = {"from_attributes": True, "use_enum_values": True}


class OperationalTeamResponse(BaseModel):
    id: int
    campaign_id: int
    shift_slot_id: int
    team_type: TeamType
    vehicle_id: int | None
    commander_id: int | None
    status: TeamStatus
    max_members: int
    mission_name: str | None = None
    notes: str | None
    member_count: int = 0
    members: list[AssignmentResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "use_enum_values": True}


class OperationalTeamAuditResponse(BaseModel):
    id: int
    team_id: int | None
    campaign_id: int
    actor_id: int
    action: str
    user_id: int | None = None
    credit_id: int | None = None
    vehicle_id: int | None = None
    commander_id: int | None = None
    details: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
