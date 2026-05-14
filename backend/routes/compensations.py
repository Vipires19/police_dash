from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from auth.dependencies import get_current_approved_user, require_approver, require_compensation_creator
from database.session import get_db
from models.compensations import CompensationEvent
from models.user import User
from schemas.compensations import (
    CompensationDecisionBody,
    CompensationEventCreate,
    CompensationEventPublic,
    CompensationRejectBody,
    UserCompensationAvailablePublic,
)
from services import compensation_service as comp_svc
from services import leave_service as leave_svc

router = APIRouter(prefix="/compensations", tags=["compensations"])


def _to_event_public(ev: CompensationEvent) -> CompensationEventPublic:
    return CompensationEventPublic(
        id=ev.id,
        event_type=ev.event_type,
        motivo=ev.motivo,
        status=ev.status,
        created_by_id=ev.created_by_id,
        decided_by_id=ev.decided_by_id,
        decided_at=ev.decided_at,
        decision_motivo=ev.decision_motivo,
        created_at=ev.created_at,
        participant_user_ids=[p.user_id for p in ev.participants],
    )


@router.get("/pending", response_model=list[CompensationEventPublic])
def pending_compensations(
    _: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> list[CompensationEventPublic]:
    rows = comp_svc.list_pending_compensation_events(db)
    return [_to_event_public(r) for r in rows]


@router.get("/available", response_model=list[UserCompensationAvailablePublic])
def available_compensations(
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[UserCompensationAvailablePublic]:
    rows = leave_svc.list_available_compensation_credits(db, current.id)
    return [UserCompensationAvailablePublic.model_validate(r) for r in rows]


@router.post("/", response_model=CompensationEventPublic, status_code=status.HTTP_201_CREATED)
def create_compensation(
    body: CompensationEventCreate,
    current: User = Depends(require_compensation_creator),
    db: Session = Depends(get_db),
) -> CompensationEventPublic:
    try:
        ev = comp_svc.create_compensation_event(db, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    ev_full = db.scalars(
        select(CompensationEvent)
        .options(selectinload(CompensationEvent.participants))
        .where(CompensationEvent.id == ev.id)
    ).first()
    if not ev_full:
        raise HTTPException(status_code=500, detail="Erro interno")
    return _to_event_public(ev_full)


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
    return _to_event_public(ev)


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
    return _to_event_public(ev)
