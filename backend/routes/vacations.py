from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from auth.acting import ActingContext
from auth.dependencies import APPROVER_ROLES, get_acting_context, require_approver
from database.session import get_db
from models.user import User
from models.vacation import VacationRequest, VacationStatus, VacationType
from schemas.vacation import (
    VacationCalendarResponse,
    VacationDecisionBody,
    VacationRejectBody,
    VacationRequestCreate,
    VacationRequestPublic,
    VacationRequestUpdate,
)
from services import vacation_service as vacation_svc

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
        notes=row.notes,
        decision_reason=row.decision_reason,
        approved_by_id=row.approved_by_id,
        approved_at=row.approved_at,
        created_at=row.created_at,
        patente=u.patente if u else None,
        nome_guerra=u.nome_guerra if u else None,
        display_order=u.display_order if u else None,
    )


def _register_absence_routes(router: APIRouter) -> None:
    @router.get("/calendar", response_model=VacationCalendarResponse)
    def calendar(
        year: int | None = Query(default=None, ge=2000, le=2100),
        month: int | None = Query(default=None, ge=1, le=12),
        ctx: ActingContext = Depends(get_acting_context),
        db: Session = Depends(get_db),
    ) -> VacationCalendarResponse:
        now = datetime.now(_BR)
        y = year if year is not None else now.year
        m = month if month is not None else now.month
        data = vacation_svc.build_calendar(
            db,
            year=y,
            month=m,
            viewer=ctx.target,
            is_command=_is_command(ctx.actor),
        )
        return VacationCalendarResponse.model_validate(data)

    @router.get("/", response_model=list[VacationRequestPublic])
    def list_absences(
        status: VacationStatus | None = None,
        absence_type: VacationType | None = Query(default=None, alias="type"),
        user_id: int | None = None,
        year: int | None = Query(default=None, ge=2000, le=2100),
        month: int | None = Query(default=None, ge=1, le=12),
        ctx: ActingContext = Depends(get_acting_context),
        db: Session = Depends(get_db),
    ) -> list[VacationRequestPublic]:
        scope_user_id = user_id
        if ctx.is_acting_as:
            scope_user_id = ctx.target.id
        elif scope_user_id is None and ctx.actor.role not in APPROVER_ROLES:
            scope_user_id = ctx.actor.id
        y, m = year, month
        if y is None or m is None:
            now = datetime.now(_BR)
            y = y or now.year
            m = m or now.month
        rows = vacation_svc.list_absence_requests(
            db,
            status=status,
            absence_type=absence_type,
            user_id=scope_user_id,
            year=y,
            month=m,
        )
        return [_to_public(r) for r in rows]

    @router.get("/pending", response_model=list[VacationRequestPublic])
    def pending_absences(
        _: User = Depends(require_approver),
        db: Session = Depends(get_db),
    ) -> list[VacationRequestPublic]:
        rows = vacation_svc.list_pending_vacations(db)
        return [_to_public(r) for r in rows]

    @router.post("/request", response_model=VacationRequestPublic, status_code=status.HTTP_201_CREATED)
    def request_absence(
        body: VacationRequestCreate,
        ctx: ActingContext = Depends(get_acting_context),
        db: Session = Depends(get_db),
    ) -> VacationRequestPublic:
        try:
            row = vacation_svc.create_vacation_request(db, ctx.target, body, actor=ctx.actor)
        except ValueError as e:
            msg = str(e)
            code = status.HTTP_409_CONFLICT if "Já existe" in msg else status.HTTP_400_BAD_REQUEST
            raise HTTPException(status_code=code, detail=msg) from e
        return _to_public(row)

    @router.patch("/{absence_id}", response_model=VacationRequestPublic)
    def update_absence(
        absence_id: int,
        body: VacationRequestUpdate,
        ctx: ActingContext = Depends(get_acting_context),
        db: Session = Depends(get_db),
    ) -> VacationRequestPublic:
        try:
            row = vacation_svc.update_vacation_request(
                db, absence_id, ctx.target, body, actor=ctx.actor
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        return _to_public(row)

    @router.patch("/{absence_id}/approve", response_model=VacationRequestPublic)
    def approve_absence(
        absence_id: int,
        body: VacationDecisionBody,
        current: User = Depends(require_approver),
        db: Session = Depends(get_db),
    ) -> VacationRequestPublic:
        try:
            row = vacation_svc.approve_vacation(db, absence_id, current, body.reason)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        return _to_public(row)

    @router.patch("/{absence_id}/reject", response_model=VacationRequestPublic)
    def reject_absence(
        absence_id: int,
        body: VacationRejectBody,
        current: User = Depends(require_approver),
        db: Session = Depends(get_db),
    ) -> VacationRequestPublic:
        try:
            row = vacation_svc.reject_vacation(db, absence_id, current, body.reason)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        return _to_public(row)

    @router.patch("/{absence_id}/cancel", response_model=VacationRequestPublic)
    def cancel_absence(
        absence_id: int,
        body: VacationDecisionBody,
        ctx: ActingContext = Depends(get_acting_context),
        db: Session = Depends(get_db),
    ) -> VacationRequestPublic:
        try:
            row = vacation_svc.cancel_vacation(
                db, absence_id, ctx.target, body.reason, actor=ctx.actor
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        return _to_public(row)

    @router.patch("/{absence_id}/revert", response_model=VacationRequestPublic)
    def revert_absence(
        absence_id: int,
        body: VacationRejectBody,
        current: User = Depends(require_approver),
        db: Session = Depends(get_db),
    ) -> VacationRequestPublic:
        try:
            row = vacation_svc.revert_vacation(db, absence_id, current, body.reason)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        return _to_public(row)


router = APIRouter(prefix="/vacations", tags=["vacations"])
absences_router = APIRouter(prefix="/absences", tags=["afastamentos"])
_register_absence_routes(router)
_register_absence_routes(absences_router)
