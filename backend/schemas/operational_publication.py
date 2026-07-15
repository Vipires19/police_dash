"""Schemas do domínio OperationalPublication."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field

from models.operational_publication import (
    OperationalPublicationAuditAction,
    OperationalPublicationStatus,
)


class ChecklistItemLevel(str, Enum):
    OK = "OK"
    WARN = "WARN"
    ERROR = "ERROR"
    PENDING = "PENDING"


class ChecklistItem(BaseModel):
    key: str
    title: str
    level: ChecklistItemLevel
    detail: str
    blocking: bool = False


class OperationalPublicationChecklist(BaseModel):
    items: list[ChecklistItem]
    ready: bool
    has_errors: bool
    has_warnings: bool
    can_publish_with_risk: bool


class OperationalPublicationCreateDraft(BaseModel):
    service_scale_id: int
    scale_date: date | None = None


class OperationalPublicationPublishRequest(BaseModel):
    acknowledge_risks: bool = False
    reason: str | None = Field(default=None, max_length=512)


class OperationalPublicationAuditPublic(BaseModel):
    id: int
    action: OperationalPublicationAuditAction
    actor_id: int
    actor_label: str | None = None
    details: str | None = None
    created_at: datetime


class OperationalPublicationPublic(BaseModel):
    id: int
    service_scale_id: int
    scale_date: date
    publication_number: int
    version: int
    status: OperationalPublicationStatus
    created_by_id: int
    created_by_label: str | None = None
    published_by_id: int | None = None
    published_by_label: str | None = None
    published_at: datetime | None = None
    generated_message: str | None = None
    generated_pdf: str | None = None
    change_summary: str | None = None
    publish_reason: str | None = None
    risk_acknowledged: bool = False
    previous_publication_id: int | None = None
    checklist: OperationalPublicationChecklist | None = None
    created_at: datetime
    updated_at: datetime


class OperationalPublicationDetail(OperationalPublicationPublic):
    snapshot: dict | None = None
    audits: list[OperationalPublicationAuditPublic] = Field(default_factory=list)


class OperationalPublicationHistoryItem(BaseModel):
    id: int
    service_scale_id: int
    scale_date: date
    publication_number: int
    version: int
    status: OperationalPublicationStatus
    published_by_label: str | None = None
    published_at: datetime | None = None
    publish_reason: str | None = None
    change_summary: str | None = None
    risk_acknowledged: bool = False


class OperationalPublicationHistoryResponse(BaseModel):
    items: list[OperationalPublicationHistoryItem]
    total: int


class OperationalPublicationCenterDay(BaseModel):
    scale_date: date
    service_scale_id: int | None
    scale_title: str | None
    scale_status: str | None
    active_publication: OperationalPublicationPublic | None
    checklist: OperationalPublicationChecklist | None
    latest_published: OperationalPublicationHistoryItem | None
