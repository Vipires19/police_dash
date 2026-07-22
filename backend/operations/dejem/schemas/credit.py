"""Schemas de Credit + lifecycle (C7)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from operations.dejem.models.enums import CreditStatus


class CreditCreate(BaseModel):
    allocation_id: int
    campaign_id: int
    police_officer_id: int
    status: CreditStatus = CreditStatus.AVAILABLE


class CreditUpdate(BaseModel):
    status: CreditStatus
    reason: str | None = Field(default=None, max_length=512)


class CreditActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=512)


class CreditResponse(BaseModel):
    id: int
    allocation_id: int
    campaign_id: int
    police_officer_id: int
    status: CreditStatus
    shift_slot_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True, "use_enum_values": True}


class CreditAuditResponse(BaseModel):
    id: int
    credit_id: int
    campaign_id: int
    actor_id: int
    from_status: str | None
    to_status: str
    reason: str | None = None
    origin: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
