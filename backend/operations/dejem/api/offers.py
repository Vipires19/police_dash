"""Router Offers — oferta via OfferEvents (Sprint C4)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from auth.dependencies import require_dejem_admin
from database.session import get_db
from operations.dejem.api.http_errors import domain_http_error
from models.user import User
from operations.dejem.schemas.offer_event import (
    OfferAvailableResponse,
    OfferEventCreate,
    OfferEventResponse,
    OfferEventUpdate,
)
from operations.dejem.services.offer_service import OfferError, OfferService

router = APIRouter(prefix="/offers", tags=["operations-dejem-offers"])

@router.get("/history", response_model=list[OfferEventResponse])
def offer_history(
    campaign_id: int = Query(...),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[OfferEventResponse]:
    try:
        return OfferService(db).history(campaign_id)
    except OfferError as e:
        raise domain_http_error(e) from e

@router.get("/available", response_model=OfferAvailableResponse)
def offer_available(
    campaign_id: int = Query(...),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OfferAvailableResponse:
    try:
        return OfferService(db).available(campaign_id)
    except OfferError as e:
        raise domain_http_error(e) from e

@router.get("/", response_model=list[OfferEventResponse])
def list_offers(
    campaign_id: int = Query(...),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[OfferEventResponse]:
    try:
        return OfferService(db).list_by_campaign(campaign_id)
    except OfferError as e:
        raise domain_http_error(e) from e

@router.get("/{offer_id}", response_model=OfferEventResponse)
def get_offer(
    offer_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OfferEventResponse:
    try:
        return OfferService(db).get(offer_id)
    except OfferError as e:
        raise domain_http_error(e) from e

@router.post("/", response_model=OfferEventResponse, status_code=status.HTTP_201_CREATED)
def create_offer(
    body: OfferEventCreate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OfferEventResponse:
    try:
        return OfferService(db).create(current, body)
    except OfferError as e:
        raise domain_http_error(e) from e

@router.put("/{offer_id}", response_model=OfferEventResponse)
def update_offer(
    offer_id: int,
    body: OfferEventUpdate,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> OfferEventResponse:
    try:
        return OfferService(db).update_reason(offer_id, body)
    except OfferError as e:
        raise domain_http_error(e) from e

@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offer(
    offer_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> Response:
    try:
        OfferService(db).delete(offer_id)
    except OfferError as e:
        raise domain_http_error(e) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)
