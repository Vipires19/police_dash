"""Router Campaigns — ciclo de vida (Sprint C2)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_approved_user, require_dejem_admin
from database.session import get_db
from operations.dejem.api.http_errors import domain_http_error
from models.user import User
from operations.dejem.schemas.campaign import (
    CampaignAuditResponse,
    CampaignCreate,
    CampaignResponse,
    CampaignStatusChange,
)
from operations.dejem.services.campaign_service import CampaignError, CampaignService

router = APIRouter(prefix="/campaigns", tags=["operations-dejem-campaigns"])

@router.get("/", response_model=list[CampaignResponse])
def list_campaigns(
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[CampaignResponse]:
    return CampaignService(db).list_campaigns()

@router.get("/open", response_model=list[CampaignResponse])
def list_open_campaigns(
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[CampaignResponse]:
    """Campanhas OPEN (equivalente legado: status OPEN_INTEREST)."""
    return CampaignService(db).list_open_campaigns()

@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CampaignResponse:
    try:
        return CampaignService(db).get_campaign(campaign_id)
    except CampaignError as e:
        raise domain_http_error(e) from e

@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    body: CampaignCreate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CampaignResponse:
    try:
        return CampaignService(db).create_campaign(current, body)
    except CampaignError as e:
        raise domain_http_error(e) from e

@router.post("/{campaign_id}/open", response_model=CampaignResponse)
def open_campaign(
    campaign_id: int,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CampaignResponse:
    try:
        return CampaignService(db).open_campaign(campaign_id, current)
    except CampaignError as e:
        raise domain_http_error(e) from e

@router.post("/{campaign_id}/close-registration", response_model=CampaignResponse)
def close_registration(
    campaign_id: int,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CampaignResponse:
    try:
        return CampaignService(db).close_registration(campaign_id, current)
    except CampaignError as e:
        raise domain_http_error(e) from e

@router.post("/{campaign_id}/mark-allocated", response_model=CampaignResponse)
def mark_allocated(
    campaign_id: int,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CampaignResponse:
    try:
        return CampaignService(db).mark_allocated(campaign_id, current)
    except CampaignError as e:
        raise domain_http_error(e) from e

@router.post("/{campaign_id}/start", response_model=CampaignResponse)
def start_campaign(
    campaign_id: int,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CampaignResponse:
    try:
        return CampaignService(db).start_campaign(campaign_id, current)
    except CampaignError as e:
        raise domain_http_error(e) from e

@router.post("/{campaign_id}/close", response_model=CampaignResponse)
def close_campaign(
    campaign_id: int,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CampaignResponse:
    try:
        return CampaignService(db).close_campaign(campaign_id, current)
    except CampaignError as e:
        raise domain_http_error(e) from e

@router.post("/{campaign_id}/status", response_model=CampaignResponse)
def change_status(
    campaign_id: int,
    body: CampaignStatusChange,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> CampaignResponse:
    try:
        return CampaignService(db).change_status(campaign_id, current, body.status)
    except CampaignError as e:
        raise domain_http_error(e) from e

@router.get("/{campaign_id}/audits", response_model=list[CampaignAuditResponse])
def list_campaign_audits(
    campaign_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[CampaignAuditResponse]:
    try:
        return CampaignService(db).list_audits(campaign_id)
    except CampaignError as e:
        raise domain_http_error(e) from e
