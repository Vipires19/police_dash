from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from auth.dependencies import APPROVER_ROLES, get_current_approved_user, require_approver
from database.session import get_db
from models.user import User
from models.vacation import VacationRequest
from schemas.vacation import (
    VacationCalendarResponse,
    VacationDecisionBody,
    VacationRejectBody,
    VacationRequestCreate,
    VacationRequestPublic,
)
from services import vacation_service as vacation_svc

router = APIRouter(prefix="/vacations", tags=["vacations"])
_BR = ZoneInfo("America/Sao_Paulo")


def _is_command(user: User) -> bool:
    return user.role in APPROVER_ROLES


def _to_public(row: VacationRequest) -> VacationRequestPublic:
    u = row.user
    return VacationRequestPublic(
        id=row.id,
        user_id=row.user_id,
        vacation_type=row.vacation_type,
        start_date=row.start_date,
        end_date=row.end_date,
        total_days=row.total_days,
        status=row.status,
        review_reason=row.review_reason,
        decision_reason=row.decision_reason,
        approved_by_id=row.approved_by_id,
        approved_at=row.approved_at,
        created_at=row.created_at,
        patente=u.patente if u else None,
        nome_guerra=u.nome_guerra if u else None,
        display_order=u.display_order if u else None,
    )


@router.get("/calendar", response_model=VacationCalendarResponse)
def calendar(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> VacationCalendarResponse:
    now = datetime.now(_BR)
    y = year if year is not None else now.year
    m = month if month is not None else now.month
    data = vacation_svc.build_calendar(db, year=y, month=m, viewer=current, is_command=_is_command(current))
    return VacationCalendarResponse.model_validate(data)


@router.get("/pending", response_model=list[VacationRequestPublic])
def pending_vacations(
    _: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> list[VacationRequestPublic]:
    rows = vacation_svc.list_pending_vacations(db)
    return [_to_public(r) for r in rows]


@router.post("/request", response_model=VacationRequestPublic, status_code=status.HTTP_201_CREATED)
def request_vacation(
    body: VacationRequestCreate,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> VacationRequestPublic:
    try:
        row = vacation_svc.create_vacation_request(db, current, body)
    except ValueError as e:
        msg = str(e)
        code = status.HTTP_409_CONFLICT if "Já existe" in msg else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=msg) from e
    return _to_public(row)


@router.patch("/{vacation_id}/approve", response_model=VacationRequestPublic)
def approve_vacation(
    vacation_id: int,
    body: VacationDecisionBody,
    current: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> VacationRequestPublic:
    try:
        row = vacation_svc.approve_vacation(db, vacation_id, current, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _to_public(row)


@router.patch("/{vacation_id}/reject", response_model=VacationRequestPublic)
def reject_vacation(
    vacation_id: int,
    body: VacationRejectBody,
    current: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> VacationRequestPublic:
    try:
        row = vacation_svc.reject_vacation(db, vacation_id, current, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _to_public(row)


@router.patch("/{vacation_id}/cancel", response_model=VacationRequestPublic)
def cancel_vacation(
    vacation_id: int,
    body: VacationDecisionBody,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> VacationRequestPublic:
    try:
        row = vacation_svc.cancel_vacation(db, vacation_id, current, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _to_public(row)
