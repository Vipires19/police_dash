"""Schemas — planejamento operacional (C9)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from operations.dejem.models.enums import AssignmentRole, TeamStatus, TeamType


class OperationalTeamCreate(BaseModel):
    campaign_id: int
    shift_slot_id: int
    team_type: TeamType
    max_members: int = Field(default=4, ge=1, le=50)
    vehicle_id: int | None = None
    commander_id: int | None = None
    notes: str | None = Field(default=None, max_length=2000)
    status: TeamStatus = TeamStatus.DRAFT


class OperationalTeamUpdate(BaseModel):
    team_type: TeamType | None = None
    max_members: int | None = Field(default=None, ge=1, le=50)
    notes: str | None = Field(default=None, max_length=2000)
    status: TeamStatus | None = None


class TeamMemberCreate(BaseModel):
    credit_id: int
    role: AssignmentRole = AssignmentRole.MEMBER


class TeamVehicleUpdate(BaseModel):
    vehicle_id: int | None = None


class TeamCommanderUpdate(BaseModel):
    commander_id: int | None = None


class AssignmentResponse(BaseModel):
    id: int
    operational_team_id: int
    credit_id: int
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
