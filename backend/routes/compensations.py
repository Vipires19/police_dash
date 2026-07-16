from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth.acting import ActingContext
from auth.dependencies import (
    APPROVER_ROLES,
    get_acting_context,
    get_current_approved_user,
    require_approver,
    require_compensation_creator,
)
from database.session import get_db
from models.compensations import CompensationStatus, CompensationType
from models.user import User
from schemas.compensations import (
    CompensationActionBody,
    CompensationDashboardSummary,
    CompensationDecisionBody,
    CompensationEventCreate,
    CompensationEventLogPublic,
    CompensationEventPublic,
    CompensationEventUpdate,
    CompensationRejectBody,
    DsUsagePublic,
    UserCompensationAvailablePublic,
)
from services import compensation_service as comp_svc
from services import leave_service as leave_svc

router = APIRouter(prefix="/compensations", tags=["compensations"])


@router.get("/summary", response_model=CompensationDashboardSummary)
def compensation_summary(
    year: int | None = Query(default=None, ge=2020, le=2100),
    ctx: ActingContext = Depends(get_acting_context),
    db: Session = Depends(get_db),
) -> CompensationDashboardSummary:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    y = year or datetime.now(ZoneInfo("America/Sao_Paulo")).year
    return comp_svc.get_dashboard_summary(db, ctx.target, y)


@router.get("/", response_model=list[CompensationEventPublic])
def list_compensations(
    status: CompensationStatus | None = None,
    event_type: CompensationType | None = None,
    user_id: int | None = None,
    year: int | None = Query(default=None, ge=2020, le=2100),
    ctx: ActingContext = Depends(get_acting_context),
    db: Session = Depends(get_db),
) -> list[CompensationEventPublic]:
    scope_user_id = user_id
    if ctx.is_acting_as:
        scope_user_id = ctx.target.id
    elif scope_user_id is None and ctx.actor.role not in APPROVER_ROLES:
        scope_user_id = ctx.actor.id
    rows = comp_svc.list_compensation_events(
        db,
        status=status,
        event_type=event_type,
        user_id=scope_user_id,
        year=year,
    )
    return [comp_svc.event_to_public(r, db) for r in rows]


@router.get("/pending", response_model=list[CompensationEventPublic])
def pending_compensations(
    _: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> list[CompensationEventPublic]:
    rows = comp_svc.list_pending_compensation_events(db)
    return [comp_svc.event_to_public(r, db) for r in rows]


@router.get("/available", response_model=list[UserCompensationAvailablePublic])
def available_compensations(
    ctx: ActingContext = Depends(get_acting_context),
    db: Session = Depends(get_db),
) -> list[UserCompensationAvailablePublic]:
    rows = leave_svc.list_available_compensation_credits(db, ctx.target.id)
    return [UserCompensationAvailablePublic.model_validate(r) for r in rows]


@router.get("/users/{user_id}/ds-usage", response_model=DsUsagePublic)
def ds_usage(
    user_id: int,
    year: int | None = Query(default=None, ge=2020, le=2100),
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> DsUsagePublic:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    y = year or datetime.now(ZoneInfo("America/Sao_Paulo")).year
    return comp_svc.count_ds_usage(db, user_id, y)


@router.get("/{event_id}/logs", response_model=list[CompensationEventLogPublic])
def event_logs(
    event_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[CompensationEventLogPublic]:
    ev = comp_svc.get_compensation_event(db, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return comp_svc.list_event_logs(db, event_id)


@router.post("/", response_model=CompensationEventPublic, status_code=status.HTTP_201_CREATED)
def create_compensation(
    body: CompensationEventCreate,
    ctx: ActingContext = Depends(get_acting_context),
    current: User = Depends(require_compensation_creator),
    db: Session = Depends(get_db),
) -> CompensationEventPublic:
    if ctx.is_acting_as and not body.participant_user_ids:
        body = body.model_copy(update={"participant_user_ids": [ctx.target.id]})
    elif ctx.is_acting_as and ctx.target.id not in body.participant_user_ids:
        body = body.model_copy(
            update={"participant_user_ids": list({*body.participant_user_ids, ctx.target.id})}
        )
    try:
        ev = comp_svc.create_compensation_event(db, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    ev_full = comp_svc.get_compensation_event(db, ev.id)
    if not ev_full:
        raise HTTPException(status_code=500, detail="Erro interno")
    return comp_svc.event_to_public(ev_full, db)


@router.patch("/{event_id}", response_model=CompensationEventPublic)
def update_compensation(
    event_id: int,
    body: CompensationEventUpdate,
    current: User = Depends(require_compensation_creator),
    db: Session = Depends(get_db),
) -> CompensationEventPublic:
    try:
        ev = comp_svc.update_compensation_event(db, event_id, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    ev_full = comp_svc.get_compensation_event(db, ev.id)
    return comp_svc.event_to_public(ev_full or ev, db)


@router.patch("/{event_id}/approve", response_model=CompensationEventPublic)
def approve_compensation(
    event_id: int,
    body: CompensationDecisionBody,
    current: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> CompensationEventPublic:
    try:
        ev = comp_svc.approve_compensation_event(db, event_id, current, body.motivo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return comp_svc.event_to_public(ev, db)


@router.patch("/{event_id}/reject", response_model=CompensationEventPublic)
def reject_compensation(
    event_id: int,
    body: CompensationRejectBody,
    current: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> CompensationEventPublic:
    try:
        ev = comp_svc.reject_compensation_event(db, event_id, current, body.motivo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return comp_svc.event_to_public(ev, db)


@router.patch("/{event_id}/cancel", response_model=CompensationEventPublic)
def cancel_compensation(
    event_id: int,
    body: CompensationActionBody,
    current: User = Depends(require_compensation_creator),
    db: Session = Depends(get_db),
) -> CompensationEventPublic:
    try:
        ev = comp_svc.cancel_compensation_event(db, event_id, current, body.motivo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return comp_svc.event_to_public(ev, db)


@router.patch("/{event_id}/revert", response_model=CompensationEventPublic)
def revert_compensation(
    event_id: int,
    body: CompensationActionBody,
    current: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> CompensationEventPublic:
    try:
        ev = comp_svc.revert_compensation_event(db, event_id, current, body.motivo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return comp_svc.event_to_public(ev, db)
