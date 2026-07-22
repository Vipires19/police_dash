"""Router Interests — manifestação de interesse (Sprint C3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_approved_user, require_dejem_admin
from database.session import get_db
from operations.dejem.api.http_errors import domain_http_error
from models.user import OrganizationalUnit, User
from operations.dejem.schemas.interest import (
    InterestAdminListResponse,
    InterestCreate,
    InterestMyResponse,
    InterestResponse,
    InterestStatisticsResponse,
    InterestUpdate,
)
from operations.dejem.services.interest_service import InterestError, InterestService

router = APIRouter(prefix="/interests", tags=["operations-dejem-interests"])

@router.get("/me", response_model=InterestMyResponse | None)
def get_my_interest(
    campaign_id: int = Query(..., description="ID da campanha"),
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> InterestMyResponse | None:
    try:
        return InterestService(db).get_mine(current, campaign_id)
    except InterestError as e:
        raise domain_http_error(e) from e

@router.get("/admin", response_model=InterestAdminListResponse)
def list_interests_admin(
    campaign_id: int = Query(..., description="ID da campanha"),
    organizational_unit: OrganizationalUnit | None = Query(
        default=None,
        description="Filtro por pelotão (organizational_unit)",
    ),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> InterestAdminListResponse:
    """Lista interessados. Filtro `equipe` não se aplica (sem vínculo permanente no User)."""
    try:
        return InterestService(db).list_admin(
            campaign_id,
            organizational_unit=organizational_unit,
        )
    except InterestError as e:
        raise domain_http_error(e) from e

@router.get("/statistics", response_model=InterestStatisticsResponse)
def interest_statistics(
    campaign_id: int = Query(..., description="ID da campanha"),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> InterestStatisticsResponse:
    try:
        return InterestService(db).statistics(campaign_id)
    except InterestError as e:
        raise domain_http_error(e) from e

@router.post("/", response_model=InterestResponse, status_code=status.HTTP_201_CREATED)
def register_interest(
    body: InterestCreate,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> InterestResponse:
    """Registra interesse; se já existir, atualiza (upsert)."""
    try:
        return InterestService(db).upsert(current, body)
    except InterestError as e:
        raise domain_http_error(e) from e

@router.put("/", response_model=InterestResponse)
def update_interest(
    body: InterestUpdate,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> InterestResponse:
    try:
        return InterestService(db).update(current, body)
    except InterestError as e:
        raise domain_http_error(e) from e

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def cancel_interest(
    campaign_id: int = Query(..., description="ID da campanha"),
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        InterestService(db).cancel(current, campaign_id)
    except InterestError as e:
        raise domain_http_error(e) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)
