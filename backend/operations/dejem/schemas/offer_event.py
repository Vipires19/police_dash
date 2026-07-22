"""Schemas de OfferEvent."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from operations.dejem.models.enums import OfferEventType


class OfferEventCreate(BaseModel):
    campaign_id: int
    event_type: OfferEventType
    quantity: int = Field(..., description="Magnitude; sinal aplicado conforme event_type")
    reason: str | None = Field(default=None, max_length=512)


class OfferEventUpdate(BaseModel):
    """Quantity/type são imutáveis; apenas motivo pode ser corrigido."""

    reason: str | None = Field(default=None, max_length=512)


class OfferEventResponse(BaseModel):
    id: int
    campaign_id: int
    event_type: OfferEventType
    quantity: int
    reason: str | None
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True, "use_enum_values": True}


class OfferAvailableResponse(BaseModel):
    campaign_id: int
    available_slots: int
    events_count: int
