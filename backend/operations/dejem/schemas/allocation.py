"""Schemas de Allocation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AllocationCreate(BaseModel):
    campaign_id: int
    police_officer_id: int
    allocated_slots: int = Field(default=0, ge=0)


class AllocationUpdate(BaseModel):
    allocated_slots: int = Field(ge=0)


class AllocationResponse(BaseModel):
    id: int
    campaign_id: int
    police_officer_id: int
    allocated_slots: int
    used_slots: int = 0
    remaining_slots: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class AllocationAuditResponse(BaseModel):
    id: int
    allocation_id: int | None
    campaign_id: int
    actor_id: int
    action: str
    details: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
