"""Router publicação DEJEM (Sprint C10)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_approved_user, require_dejem_admin
from database.session import get_db
from operations.dejem.api.http_errors import domain_http_error
from models.user import User
from operations.dejem.schemas.publication import (
    PublishRequest,
    PublishedScheduleResponse,
    RepublishRequest,
    SnapshotResponse,
)
from operations.dejem.services.publication_service import PublicationError, PublicationService

router = APIRouter(tags=["operations-dejem-publication"])

@router.post("/publish", response_model=PublishedScheduleResponse)
def publish_schedule(
    body: PublishRequest,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> PublishedScheduleResponse:
    try:
        return PublicationService(db).publish(current, body)
    except PublicationError as e:
        raise domain_http_error(e) from e

@router.post("/republish")
def republish_schedule(
    body: RepublishRequest,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> PublishedScheduleResponse | dict[str, Any]:
    try:
        return PublicationService(db).republish(current, body)
    except PublicationError as e:
        raise domain_http_error(e) from e

@router.get("/published", response_model=list[PublishedScheduleResponse])
def list_published(
    campaign_id: int = Query(...),
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[PublishedScheduleResponse]:
    try:
        return PublicationService(db).list_published(campaign_id)
    except PublicationError as e:
        raise domain_http_error(e) from e

@router.get("/published/{publication_id}", response_model=PublishedScheduleResponse)
def get_published(
    publication_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> PublishedScheduleResponse:
    try:
        return PublicationService(db).get(publication_id)
    except PublicationError as e:
        raise domain_http_error(e) from e

@router.get("/published/{publication_id}/snapshot", response_model=SnapshotResponse)
def get_snapshot(
    publication_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> SnapshotResponse:
    try:
        svc = PublicationService(db)
        row = svc.get(publication_id)
        return SnapshotResponse(
            publication_id=publication_id,
            version=row.version,
            snapshot=svc.get_snapshot(publication_id),
        )
    except PublicationError as e:
        raise domain_http_error(e) from e

@router.get("/published/{publication_id}/mapa-force")
def get_mapa_force(
    publication_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    try:
        return PublicationService(db).get_mapa_payload(publication_id)
    except PublicationError as e:
        raise domain_http_error(e) from e

@router.get("/published/{publication_id}/export.json")
def export_json(
    publication_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> Response:
    try:
        content = PublicationService(db).export_json(publication_id)
    except PublicationError as e:
        raise domain_http_error(e) from e
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="dejem-pub-{publication_id}.json"'
        },
    )

@router.get("/published/{publication_id}/export.csv")
def export_csv(
    publication_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> Response:
    try:
        content = PublicationService(db).export_csv(publication_id)
    except PublicationError as e:
        raise domain_http_error(e) from e
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="dejem-pub-{publication_id}.csv"'
        },
    )

@router.get("/published/{publication_id}/whatsapp-draft")
def whatsapp_draft(
    publication_id: int,
    body: str | None = Query(default=None),
    recipient: str | None = Query(default=None),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        return PublicationService(db).prepare_whatsapp_draft(
            publication_id,
            body=body,
            recipient=recipient,
        )
    except PublicationError as e:
        raise domain_http_error(e) from e
