"""Schemas do Allocation Engine (C5)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from operations.dejem.schemas.allocation import AllocationResponse
from operations.dejem.schemas.credit import CreditResponse


class AllocateRequest(BaseModel):
    campaign_id: int


class AllocateResponse(BaseModel):
    campaign_id: int
    available_slots: int
    interested_count: int
    slots_per_officer: int
    distributed_slots: int
    remaining_slots: int
    allocations_created: int
    credits_created: int
    allocations: list[AllocationResponse] = Field(default_factory=list)


class AllocationSummaryResponse(BaseModel):
    campaign_id: int
    available_slots: int
    interested_count: int
    allocations_count: int
    credits_count: int
    distributed_slots: int
    remaining_slots: int
    slots_per_officer: int | None = None
    is_distributed: bool


class RemainingSlotsResponse(BaseModel):
    campaign_id: int
    available_slots: int
    distributed_slots: int
    remaining_slots: int
