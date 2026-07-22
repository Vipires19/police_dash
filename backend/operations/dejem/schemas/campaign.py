"""Schemas de Campaign."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from operations.dejem.models.enums import CampaignStatus


class CampaignCreate(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)


class CampaignUpdate(BaseModel):
    """Reservado para metadados futuros (sem status — use transition)."""

    pass


class CampaignStatusChange(BaseModel):
    status: CampaignStatus


class CampaignAuditResponse(BaseModel):
    id: int
    campaign_id: int
    actor_id: int
    from_status: str | None
    to_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignResponse(BaseModel):
    id: int
    month: int
    year: int
    status: CampaignStatus
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    total_available_slots: int = 0
    monthly_limit_per_officer: int = 0
    undistributed_slots: int = 0
    offer_excess_slots: int = 0

    model_config = {"from_attributes": True, "use_enum_values": True}
