"""Schemas do Incremental Allocation Engine (C6)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class IncrementalRequest(BaseModel):
    campaign_id: int
    reason: str | None = Field(default=None, max_length=512)


class IncrementalPreviewResponse(BaseModel):
    campaign_id: int
    available_slots: int
    distributed_slots: int
    undistributed_slots: int
    unaccounted_slots: int
    offer_excess_slots: int
    interested_without_allocation: int
    would_distribute: int
    would_remain: int
    has_inconsistency: bool


class IncrementalResultResponse(BaseModel):
    campaign_id: int
    reason: str | None
    available_slots: int
    slots_processed: int
    credits_created: int
    allocations_updated: int
    allocations_created: int
    undistributed_slots: int
    offer_excess_slots: int
    credits_released: int = 0
    noop: bool = False
    message: str | None = None


class IncrementalAuditResponse(BaseModel):
    id: int
    allocation_id: int | None
    campaign_id: int
    actor_id: int
    action: str
    details: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
