"""Router ShiftSlots — turnos disponíveis (Sprint C8)."""

from __future__ import annotations

from datetime import date as DateValue

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_approved_user, require_dejem_admin
from database.session import get_db
from operations.dejem.api.http_errors import domain_http_error
from models.user import User
from operations.dejem.models.enums import ShiftSlotStatus
from operations.dejem.schemas.shift_slot import (
    ShiftSlotAvailabilityResponse,
    ShiftSlotCreate,
    ShiftSlotResponse,
    ShiftSlotUpdate,
)
from operations.dejem.services.shift_slot_service import ShiftSlotError, ShiftSlotService

router = APIRouter(prefix="/shift-slots", tags=["operations-dejem-shift-slots"])

@router.get("/", response_model=list[ShiftSlotResponse])
def list_shift_slots(
    campaign_id: int = Query(...),
    on_date: DateValue | None = Query(default=None),
    status_filter: ShiftSlotStatus | None = Query(default=None, alias="status"),
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[ShiftSlotResponse]:
    try:
        return ShiftSlotService(db).list(
            campaign_id,
            on_date=on_date,
            status=status_filter,
        )
    except ShiftSlotError as e:
        raise domain_http_error(e) from e

@router.get("/availability", response_model=ShiftSlotAvailabilityResponse)
def shift_slots_availability(
    campaign_id: int = Query(...),
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> ShiftSlotAvailabilityResponse:
    try:
        return ShiftSlotService(db).availability(campaign_id)
    except ShiftSlotError as e:
        raise domain_http_error(e) from e

@router.get("/{slot_id}", response_model=ShiftSlotResponse)
def get_shift_slot(
    slot_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> ShiftSlotResponse:
    try:
        return ShiftSlotService(db).get(slot_id)
    except ShiftSlotError as e:
        raise domain_http_error(e) from e

@router.post("/", response_model=ShiftSlotResponse, status_code=status.HTTP_201_CREATED)
def create_shift_slot(
    body: ShiftSlotCreate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> ShiftSlotResponse:
    try:
        return ShiftSlotService(db).create(current, body)
    except ShiftSlotError as e:
        raise domain_http_error(e) from e

@router.put("/{slot_id}", response_model=ShiftSlotResponse)
def update_shift_slot(
    slot_id: int,
    body: ShiftSlotUpdate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> ShiftSlotResponse:
    try:
        return ShiftSlotService(db).update(slot_id, current, body)
    except ShiftSlotError as e:
        raise domain_http_error(e) from e

@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift_slot(
    slot_id: int,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> Response:
    try:
        ShiftSlotService(db).delete(slot_id, current)
    except ShiftSlotError as e:
        raise domain_http_error(e) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)
