"""API do Centro de Publicação Operacional."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_approved_user, require_scale_editor
from database.session import get_db
from models.user import User
from schemas.operational_publication import (
    OperationalPublicationCenterDay,
    OperationalPublicationCreateDraft,
    OperationalPublicationDetail,
    OperationalPublicationHistoryResponse,
    OperationalPublicationPublic,
    OperationalPublicationPublishRequest,
)
from services import operational_publication_service as op_svc
from services.operational_publication_service import OperationalPublicationError, to_public

router = APIRouter(prefix="/operational-publications", tags=["operational-publications"])


@router.get("/center", response_model=OperationalPublicationCenterDay)
def get_center(
    day: date = Query(...),
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> OperationalPublicationCenterDay:
    data = op_svc.get_center_for_date(db, current, day)
    return OperationalPublicationCenterDay.model_validate(data)


@router.get("/history", response_model=OperationalPublicationHistoryResponse)
def history(
    scale_date: date | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> OperationalPublicationHistoryResponse:
    return op_svc.list_history(db, scale_date=scale_date, limit=limit, offset=offset)


@router.post("/draft", response_model=OperationalPublicationPublic, status_code=status.HTTP_201_CREATED)
def create_draft(
    body: OperationalPublicationCreateDraft,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> OperationalPublicationPublic:
    try:
        row = op_svc.create_or_refresh_draft(
            db,
            current,
            service_scale_id=body.service_scale_id,
            scale_date=body.scale_date,
        )
    except OperationalPublicationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return to_public(row)


@router.post("/draft/by-date/{scale_date}", response_model=OperationalPublicationPublic)
def create_draft_by_date(
    scale_date: date,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> OperationalPublicationPublic:
    try:
        row = op_svc.create_or_refresh_draft(db, current, scale_date=scale_date)
    except OperationalPublicationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return to_public(row)


@router.get("/{publication_id}", response_model=OperationalPublicationDetail)
def get_publication(
    publication_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> OperationalPublicationDetail:
    try:
        return op_svc.get_detail(db, publication_id)
    except OperationalPublicationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{publication_id}/validate", response_model=OperationalPublicationPublic)
def validate_publication(
    publication_id: int,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> OperationalPublicationPublic:
    try:
        row = op_svc.validate_publication(db, publication_id, current)
    except OperationalPublicationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return to_public(row)


@router.post("/{publication_id}/publish", response_model=OperationalPublicationPublic)
def publish_publication(
    publication_id: int,
    body: OperationalPublicationPublishRequest | None = None,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> OperationalPublicationPublic:
    payload = body or OperationalPublicationPublishRequest()
    try:
        row = op_svc.publish_publication(
            db,
            publication_id,
            current,
            acknowledge_risks=payload.acknowledge_risks,
            reason=payload.reason,
        )
    except OperationalPublicationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return to_public(row)


@router.post("/{publication_id}/archive", response_model=OperationalPublicationPublic)
def archive_publication(
    publication_id: int,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> OperationalPublicationPublic:
    try:
        row = op_svc.archive_publication(db, publication_id, current)
    except OperationalPublicationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return to_public(row)


@router.post("/{publication_id}/refresh", response_model=OperationalPublicationPublic)
def refresh_publication(
    publication_id: int,
    current: User = Depends(require_scale_editor),
    db: Session = Depends(get_db),
) -> OperationalPublicationPublic:
    from repositories.operational_publication_repository import OperationalPublicationRepository

    repo = OperationalPublicationRepository(db)
    existing = repo.get(publication_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publicação não encontrada")
    try:
        refreshed = op_svc.create_or_refresh_draft(
            db, current, service_scale_id=existing.service_scale_id
        )
    except OperationalPublicationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return to_public(refreshed)
