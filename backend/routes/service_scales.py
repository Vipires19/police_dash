from datetime import date, datetime

#from sqlalchemy.sql.functions import current_user

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from auth.dependencies import get_current_approved_user, require_scale_editor
from database.session import get_db
from models.service_scale import ScaleLog, ScaleStatus, ScaleTeam, ScaleTeamMember, ServiceScale
from models.user import User, UserRole
from models.vehicle import Vehicle
from schemas.service_scale import (
    FT_MISSION_PRESETS,
    ROCAM_MISSION_PRESETS,
    ScaleCalendarResponse,
    ScaleDayDetailResponse,
    ScaleExportResponse,
    ScaleHistoryEntry,
    ScaleHistoryResponse,
    ScaleLogFeedItem,
    ScaleTeamCreate,
    ScaleTeamMembersUpdate,
    ScaleTeamMemberPublic,
    ScaleTeamPublic,
    ScaleTeamUpdate,
    ScaleVehicleOption,
    ServiceScaleCreate,
    ServiceScalePublic,
    ServiceScaleUpdate,
    StaffRosterEntry,
)
from services import scale_export_service as export_svc
from services import service_scale_service as scale_svc

router = APIRouter(prefix="/service-scales", tags=["service-scales"])
_BR = ZoneInfo("America/Sao_Paulo")


def _can_edit_scale(user: User) -> bool:
    return user.role in {UserRole.N90, UserRole.ADMIN}


def _can_view_scale(scale: ServiceScale | None, user: User) -> bool:
    if scale is None:
        return True
    if scale.status == ScaleStatus.PUBLISHED:
        return True
    return _can_edit_scale(user)


def _member_public(m: ScaleTeamMember) -> ScaleTeamMemberPublic:
    u = m.user
    av = m.assigned_vehicle
    return ScaleTeamMemberPublic(
        id=m.id,
        user_id=m.user_id,
        patente=u.patente if u else "",
        nome_guerra=u.nome_guerra if u else "",
        display_order=u.display_order if u else 0,
        assigned_vehicle_id=m.assigned_vehicle_id,
        assigned_vehicle_prefixo=av.prefixo if av else None,
        role_label=m.role_label,
    )


def _team_public(t: ScaleTeam) -> ScaleTeamPublic:
    v = t.vehicle
    return ScaleTeamPublic(
        id=t.id,
        modality=t.modality,
        vehicle_id=t.vehicle_id,
        vehicle_prefixo=v.prefixo if v else None,
        vehicle_placa=v.placa if v else None,
        start_datetime=t.start_datetime,
        end_datetime=t.end_datetime,
        mission_name=t.mission_name,
        notes=t.notes,
        members=[_member_public(m) for m in t.members],
    )


def _scale_public(row: ServiceScale) -> ServiceScalePublic:
    cb = row.created_by
    return ServiceScalePublic(
        id=row.id,
        scale_date=row.scale_date,
        title=row.title,
        description=row.description,
        status=row.status,
        created_by_id=row.created_by_id,
        created_by_label=f"{cb.patente} {cb.nome_guerra}" if cb else None,
        published_at=row.published_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
        teams=[_team_public(t) for t in row.teams],
    )


def _vehicle_option(v: Vehicle) -> ScaleVehicleOption:
    return ScaleVehicleOption(
        id=v.id,
        prefixo=v.prefixo,
        placa=v.placa,
        modalidade=v.modalidade.value,
    )


@router.get("/calendar", response_model=ScaleCalendarResponse)
def calendar(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> ScaleCalendarResponse:
    now = datetime.now(_BR)
    y = year if year is not None else now.year
    m = month if month is not None else now.month

    data = scale_svc.build_calendar(
        db,
        y,
        m,
        hide_drafts=not _can_edit_scale(current),
    )

    return ScaleCalendarResponse.model_validate(data)

@router.get("/history", response_model=ScaleHistoryResponse)
def history(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    status_filter: ScaleStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> ScaleHistoryResponse:
    rows, total = scale_svc.list_history(
        db,
        from_date=from_date,
        to_date=to_date,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    items = [
        ScaleHistoryEntry(
            id=r.id,
            scale_date=r.scale_date,
            title=r.title,
            status=r.status,
            team_count=len(r.teams),
            published_at=r.published_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]
    return ScaleHistoryResponse(items=items, total=total)


@router.get("/recent-events", response_model=list[ScaleLogFeedItem])
def recent_events(
    limit: int = Query(default=15, ge=1, le=50),
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[ScaleLogFeedItem]:
    rows = scale_svc.list_recent_events(db, limit=limit)
    out: list[ScaleLogFeedItem] = []
    for log in rows:
        scale = log.service_scale
        actor = log.actor
        out.append(
            ScaleLogFeedItem(
                id=log.id,
                service_scale_id=log.service_scale_id,
                scale_date=scale.scale_date if scale else date.today(),
                scale_title=scale.title if scale else "",
                action_type=log.action_type,
                description=log.description,
                created_at=log.created_at,
                actor_label=f"{actor.patente} {actor.nome_guerra}" if actor else "Sistema",
            )
        )
    return out


@router.get("/presets/missions")
def mission_presets(_: User = Depends(get_current_approved_user)) -> dict:
    return {"ft": list(FT_MISSION_PRESETS), "ro_cam": list(ROCAM_MISSION_PRESETS)}


@router.get("/{scale_date}", response_model=ScaleDayDetailResponse)
def get_by_date(
    scale_date: date,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> ScaleDayDetailResponse:
    detail = scale_svc.get_day_detail(db, scale_date, can_edit=_can_edit_scale(current))
    scale = detail["scale"]
    if scale and not _can_view_scale(scale, current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Escala em rascunho")
    return ScaleDayDetailResponse(
        scale=_scale_public(scale) if scale else None,
        staff_roster=[StaffRosterEntry.model_validate(r) for r in detail["staff_roster"]],
        vehicles_ft=[_vehicle_option(v) for v in detail["vehicles_ft"]],
        vehicles_ro_cam=[_vehicle_option(v) for v in detail["vehicles_ro_cam"]],
    )


@router.post("/", response_model=ServiceScalePublic, status_code=status.HTTP_201_CREATED)
def create_scale(
    body: ServiceScaleCreate,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> ServiceScalePublic:
    try:
        row = scale_svc.create_scale(db, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _scale_public(row)


@router.patch("/{scale_id}", response_model=ServiceScalePublic)
def patch_scale(
    scale_id: int,
    body: ServiceScaleUpdate,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> ServiceScalePublic:
    try:
        row = scale_svc.update_scale(db, scale_id, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _scale_public(row)


@router.post("/{scale_id}/teams", response_model=ServiceScalePublic)
def add_team(
    scale_id: int,
    body: ScaleTeamCreate,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> ServiceScalePublic:
    try:
        row = scale_svc.add_team(db, scale_id, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _scale_public(row)


@router.get("/{scale_id}/export", response_model=ScaleExportResponse)
def export_scale(
    scale_id: int,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> ScaleExportResponse:
    row = scale_svc._load_scale(db, scale_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escala não encontrada")
    if not _can_view_scale(row, current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Escala indisponível")
    try:
        text = export_svc.build_export_text(db, scale_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return ScaleExportResponse(text=text)


@router.post("/{scale_id}/publish", response_model=ServiceScalePublic)
def publish_scale(
    scale_id: int,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> ServiceScalePublic:
    try:
        row = scale_svc.publish_scale(db, scale_id, current)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _scale_public(row)


@router.patch("/team/{team_id}", response_model=ServiceScalePublic)
def patch_team(
    team_id: int,
    body: ScaleTeamUpdate,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> ServiceScalePublic:
    try:
        row = scale_svc.update_team(db, team_id, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _scale_public(row)


@router.patch("/team/{team_id}/members", response_model=ServiceScalePublic)
def patch_team_members(
    team_id: int,
    body: ScaleTeamMembersUpdate,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> ServiceScalePublic:
    try:
        row = scale_svc.update_team_members(db, team_id, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _scale_public(row)


@router.patch("/team/{team_id}/remove", response_model=ServiceScalePublic)
def remove_team(
    team_id: int,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> ServiceScalePublic:
    try:
        row = scale_svc.remove_team(db, team_id, current)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _scale_public(row)


@router.delete("/{scale_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scale(
    scale_id: int,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> None:
    try:
        scale_svc.delete_scale(db, scale_id, current)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
