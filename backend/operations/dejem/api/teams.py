"""Router Operational Teams — planejamento (Sprint C9)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from auth.dependencies import (
    DEJEM_ADMIN_ROLES,
    get_current_approved_user,
    require_dejem_admin,
)
from database.session import get_db
from operations.dejem.api.http_errors import domain_http_error
from models.user import User
from operations.dejem.schemas.operational_team import (
    OperationalTeamAuditResponse,
    OperationalTeamCreate,
    OperationalTeamResponse,
    OperationalTeamUpdate,
    TeamCommanderUpdate,
    TeamMemberCreate,
    TeamMemberRoleUpdate,
    TeamRolesUpdate,
    TeamVehicleUpdate,
)
from operations.dejem.services.operational_team_service import (
    OperationalTeamError,
    OperationalTeamService,
)

router = APIRouter(prefix="/teams", tags=["operations-dejem-teams"])

def _is_admin(user: User) -> bool:
    return user.role in DEJEM_ADMIN_ROLES

@router.get("/", response_model=list[OperationalTeamResponse])
def list_teams(
    campaign_id: int | None = Query(default=None),
    shift_slot_id: int | None = Query(default=None),
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[OperationalTeamResponse]:
    try:
        return OperationalTeamService(db).list(
            current,
            campaign_id=campaign_id,
            shift_slot_id=shift_slot_id,
            admin=_is_admin(current),
        )
    except OperationalTeamError as e:
        raise domain_http_error(e) from e

@router.get("/{team_id}/audits", response_model=list[OperationalTeamAuditResponse])
def list_team_audits(
    team_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[OperationalTeamAuditResponse]:
    try:
        return OperationalTeamService(db).list_audits(team_id)
    except OperationalTeamError as e:
        raise domain_http_error(e) from e

@router.get("/{team_id}", response_model=OperationalTeamResponse)
def get_team(
    team_id: int,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> OperationalTeamResponse:
    try:
        return OperationalTeamService(db).get(
            team_id,
            current,
            admin=_is_admin(current),
        )
    except OperationalTeamError as e:
        raise domain_http_error(e) from e

@router.post("/", response_model=OperationalTeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    body: OperationalTeamCreate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OperationalTeamResponse:
    try:
        return OperationalTeamService(db).create(current, body)
    except OperationalTeamError as e:
        raise domain_http_error(e) from e

@router.put("/{team_id}", response_model=OperationalTeamResponse)
def update_team(
    team_id: int,
    body: OperationalTeamUpdate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OperationalTeamResponse:
    try:
        return OperationalTeamService(db).update(team_id, current, body)
    except OperationalTeamError as e:
        raise domain_http_error(e) from e

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> Response:
    try:
        OperationalTeamService(db).delete(team_id, current)
    except OperationalTeamError as e:
        raise domain_http_error(e) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{team_id}/members", response_model=OperationalTeamResponse)
def add_member(
    team_id: int,
    body: TeamMemberCreate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OperationalTeamResponse:
    try:
        return OperationalTeamService(db).add_member(team_id, current, body)
    except OperationalTeamError as e:
        raise domain_http_error(e) from e

@router.delete(
    "/{team_id}/members/{member_id}",
    response_model=OperationalTeamResponse,
)
def remove_member(
    team_id: int,
    member_id: int,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OperationalTeamResponse:
    try:
        return OperationalTeamService(db).remove_member(team_id, member_id, current)
    except OperationalTeamError as e:
        raise domain_http_error(e) from e

@router.put(
    "/{team_id}/members/{member_id}/role",
    response_model=OperationalTeamResponse,
)
def set_member_role(
    team_id: int,
    member_id: int,
    body: TeamMemberRoleUpdate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OperationalTeamResponse:
    try:
        return OperationalTeamService(db).set_member_role(
            team_id, member_id, current, body
        )
    except OperationalTeamError as e:
        raise domain_http_error(e) from e

@router.put("/{team_id}/roles", response_model=OperationalTeamResponse)
def set_team_roles(
    team_id: int,
    body: TeamRolesUpdate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OperationalTeamResponse:
    try:
        return OperationalTeamService(db).set_roles(team_id, current, body)
    except OperationalTeamError as e:
        raise domain_http_error(e) from e

@router.put("/{team_id}/vehicle", response_model=OperationalTeamResponse)
def set_vehicle(
    team_id: int,
    body: TeamVehicleUpdate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OperationalTeamResponse:
    try:
        return OperationalTeamService(db).set_vehicle(team_id, current, body)
    except OperationalTeamError as e:
        raise domain_http_error(e) from e

@router.put("/{team_id}/commander", response_model=OperationalTeamResponse)
def set_commander(
    team_id: int,
    body: TeamCommanderUpdate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OperationalTeamResponse:
    try:
        return OperationalTeamService(db).set_commander(team_id, current, body)
    except OperationalTeamError as e:
        raise domain_http_error(e) from e
