"""Schemas — publicação DEJEM (C10)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from operations.dejem.models.enums import PublishedScheduleStatus


class PublishRequest(BaseModel):
    campaign_id: int
    notes: str | None = Field(default=None, max_length=512)
    reason: str | None = Field(default=None, max_length=512)


class RepublishRequest(BaseModel):
    campaign_id: int
    notes: str | None = Field(default=None, max_length=512)
    reason: str | None = Field(default=None, max_length=512)
    unlock_for_revision: bool = False


class PublishedScheduleResponse(BaseModel):
    id: int
    campaign_id: int
    published_by: int
    published_at: datetime
    version: int
    status: PublishedScheduleStatus
    notes: str | None = None
    change_summary: str | None = None
    previous_publication_id: int | None = None
    team_count: int = 0
    member_count: int = 0

    model_config = {"from_attributes": True, "use_enum_values": True}


class SnapshotResponse(BaseModel):
    publication_id: int
    version: int
    snapshot: dict[str, Any]


class UnlockResponse(BaseModel):
    campaign_id: int
    unlocked: bool
    superseded_version: int
    message: str
