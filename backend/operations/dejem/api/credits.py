"""Router Credits — infraestrutura (C4) + lifecycle (C7)."""

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
from operations.dejem.schemas.credit import (
    CreditActionRequest,
    CreditAuditResponse,
    CreditCreate,
    CreditResponse,
    CreditUpdate,
)
from operations.dejem.schemas.shift_slot import (
    ChangeSlotRequest,
    ReserveSlotRequest,
)
from operations.dejem.services.credit_service import CreditError, CreditService

router = APIRouter(prefix="/credits", tags=["operations-dejem-credits"])

def _is_dejem_admin(user: User) -> bool:
    return user.role in DEJEM_ADMIN_ROLES

@router.get("/", response_model=list[CreditResponse])
def list_credits(
    campaign_id: int | None = Query(default=None),
    police_officer_id: int | None = Query(default=None),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[CreditResponse]:
    svc = CreditService(db)
    try:
        if campaign_id is not None:
            return svc.list_by_campaign(campaign_id)
        if police_officer_id is not None:
            return svc.list_by_officer(police_officer_id)
        raise CreditError("Informe campaign_id ou police_officer_id.")
    except CreditError as e:
        raise domain_http_error(e) from e

@router.get("/{credit_id}/history", response_model=list[CreditAuditResponse])
def credit_history(
    credit_id: int,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[CreditAuditResponse]:
    try:
        svc = CreditService(db)
        svc.get_for_actor(credit_id, current, admin=_is_dejem_admin(current))
        return svc.history(credit_id)
    except CreditError as e:
        raise domain_http_error(e) from e

@router.get("/{credit_id}/audits", response_model=list[CreditAuditResponse])
def list_credit_audits(
    credit_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[CreditAuditResponse]:
    try:
        return CreditService(db).list_audits(credit_id)
    except CreditError as e:
        raise domain_http_error(e) from e

@router.get("/{credit_id}", response_model=CreditResponse)
def get_credit(
    credit_id: int,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).get_for_actor(
            credit_id,
            current,
            admin=_is_dejem_admin(current),
        )
    except CreditError as e:
        raise domain_http_error(e) from e

@router.post("/", response_model=CreditResponse, status_code=status.HTTP_201_CREATED)
def create_credit(
    body: CreditCreate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).create(current, body)
    except CreditError as e:
        raise domain_http_error(e) from e

@router.put("/{credit_id}", response_model=CreditResponse)
def update_credit(
    credit_id: int,
    body: CreditUpdate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).update_status(credit_id, current, body)
    except CreditError as e:
        raise domain_http_error(e) from e

@router.post("/{credit_id}/select-date", response_model=CreditResponse)
def select_date(
    credit_id: int,
    body: CreditActionRequest | None = None,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).select_date(
            credit_id,
            current,
            reason=(body.reason if body else None),
        )
    except CreditError as e:
        raise domain_http_error(e) from e

@router.post("/{credit_id}/release", response_model=CreditResponse)
def release_credit(
    credit_id: int,
    body: CreditActionRequest | None = None,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).release(
            credit_id,
            current,
            reason=(body.reason if body else None),
        )
    except CreditError as e:
        raise domain_http_error(e) from e

@router.post("/{credit_id}/request-approval", response_model=CreditResponse)
def request_approval(
    credit_id: int,
    body: CreditActionRequest | None = None,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).request_approval(
            credit_id,
            current,
            reason=(body.reason if body else None),
        )
    except CreditError as e:
        raise domain_http_error(e) from e

@router.post("/{credit_id}/approve", response_model=CreditResponse)
def approve_credit(
    credit_id: int,
    body: CreditActionRequest | None = None,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).approve(
            credit_id,
            current,
            reason=(body.reason if body else None),
        )
    except CreditError as e:
        raise domain_http_error(e) from e

@router.post("/{credit_id}/cancel", response_model=CreditResponse)
def cancel_credit(
    credit_id: int,
    body: CreditActionRequest | None = None,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).cancel(
            credit_id,
            current,
            reason=(body.reason if body else None),
        )
    except CreditError as e:
        raise domain_http_error(e) from e

@router.post("/{credit_id}/execute", response_model=CreditResponse)
def execute_credit(
    credit_id: int,
    body: CreditActionRequest | None = None,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).execute(
            credit_id,
            current,
            reason=(body.reason if body else None),
        )
    except CreditError as e:
        raise domain_http_error(e) from e

@router.post("/{credit_id}/reserve", response_model=CreditResponse)
def reserve_slot(
    credit_id: int,
    body: ReserveSlotRequest,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).reserve(
            credit_id,
            current,
            body.shift_slot_id,
            reason=body.reason,
        )
    except CreditError as e:
        raise domain_http_error(e) from e

@router.post("/{credit_id}/change-slot", response_model=CreditResponse)
def change_slot(
    credit_id: int,
    body: ChangeSlotRequest,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).change_slot(
            credit_id,
            current,
            body.shift_slot_id,
            reason=body.reason,
        )
    except CreditError as e:
        raise domain_http_error(e) from e

@router.post("/{credit_id}/cancel-reservation", response_model=CreditResponse)
def cancel_reservation(
    credit_id: int,
    body: CreditActionRequest | None = None,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CreditResponse:
    try:
        return CreditService(db).cancel_reservation(
            credit_id,
            current,
            reason=(body.reason if body else None),
        )
    except CreditError as e:
        raise domain_http_error(e) from e

@router.delete("/{credit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credit(
    credit_id: int,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> Response:
    try:
        CreditService(db).delete(credit_id, current)
    except CreditError as e:
        raise domain_http_error(e) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)
