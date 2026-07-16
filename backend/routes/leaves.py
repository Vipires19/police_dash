from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from auth.acting import ActingContext
from auth.dependencies import APPROVER_ROLES, get_acting_context, require_approver
from database.session import get_db
from models.leaves import LeaveRequest
from models.user import User
from schemas.leaves import (
    LeaveCalendarResponse,
    LeaveDecisionBody,
    LeaveRejectBody,
    LeaveRequestCreate,
    LeaveRequestPublic,
)
from services import leave_service as leave_svc

router = APIRouter(prefix="/leaves", tags=["leaves"])
_BR = ZoneInfo("America/Sao_Paulo")


def _is_command(user: User) -> bool:
    return user.role in APPROVER_ROLES


def _to_public(row: LeaveRequest) -> LeaveRequestPublic:
    u = row.user
    return LeaveRequestPublic(
        id=row.id,
        user_id=row.user_id,
        leave_on=row.leave_on,
        leave_type=row.leave_type,
        user_compensation_id=row.user_compensation_id,
        status=row.status,
        review_reason=row.review_reason,
        decision_motivo=row.decision_motivo,
        decided_by_id=row.decided_by_id,
        decided_at=row.decided_at,
        created_at=row.created_at,
        patente=u.patente,
        nome_guerra=u.nome_guerra,
        display_order=u.display_order,
    )


@router.get("/calendar", response_model=LeaveCalendarResponse)
def calendar(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    ctx: ActingContext = Depends(get_acting_context),
    db: Session = Depends(get_db),
) -> LeaveCalendarResponse:
    now = datetime.now(_BR)
    y = year if year is not None else now.year
    m = month if month is not None else now.month
    data = leave_svc.build_calendar(
        db,
        year=y,
        month=m,
        viewer=ctx.target,
        is_command=_is_command(ctx.actor),
    )
    return LeaveCalendarResponse.model_validate(data)


@router.get("/pending", response_model=list[LeaveRequestPublic])
def pending_leaves(
    _: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> list[LeaveRequestPublic]:
    rows = leave_svc.list_pending_leaves(db)
    return [_to_public(r) for r in rows]


@router.post("/request", response_model=LeaveRequestPublic, status_code=status.HTTP_201_CREATED)
def request_leave(
    body: LeaveRequestCreate,
    ctx: ActingContext = Depends(get_acting_context),
    db: Session = Depends(get_db),
) -> LeaveRequestPublic:
    try:
        row = leave_svc.create_leave_request(db, ctx.target, body, actor=ctx.actor)
    except ValueError as e:
        msg = str(e)
        code = status.HTTP_409_CONFLICT if "Já existe" in msg else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=msg) from e
    return _to_public(row)


@router.patch("/{leave_id}/approve", response_model=LeaveRequestPublic)
def approve_leave(
    leave_id: int,
    body: LeaveDecisionBody,
    current: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> LeaveRequestPublic:
    try:
        row = leave_svc.approve_leave(db, leave_id, current, body.motivo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _to_public(row)


@router.patch("/{leave_id}/reject", response_model=LeaveRequestPublic)
def reject_leave(
    leave_id: int,
    body: LeaveRejectBody,
    current: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> LeaveRequestPublic:
    try:
        row = leave_svc.reject_leave(db, leave_id, current, body.motivo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _to_public(row)


@router.patch("/{leave_id}/cancel", response_model=LeaveRequestPublic)
def cancel_leave(
    leave_id: int,
    body: LeaveDecisionBody,
    ctx: ActingContext = Depends(get_acting_context),
    db: Session = Depends(get_db),
) -> LeaveRequestPublic:
    try:
        row = leave_svc.cancel_leave(db, leave_id, ctx.target, body.motivo, actor=ctx.actor)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _to_public(row)
