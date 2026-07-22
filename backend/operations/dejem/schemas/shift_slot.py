"""Schemas ShiftSlot + reserva (C8)."""

from __future__ import annotations

from datetime import date as DateValue
from datetime import datetime, time

from pydantic import BaseModel, Field, model_validator

from operations.dejem.models.enums import ShiftSlotStatus


class ShiftSlotCreate(BaseModel):
    campaign_id: int
    date: DateValue
    start_time: time
    end_time: time
    total_slots: int = Field(..., ge=1)
    status: ShiftSlotStatus = ShiftSlotStatus.OPEN

    @model_validator(mode="after")
    def _validate_interval(self) -> ShiftSlotCreate:
        if self.end_time <= self.start_time:
            raise ValueError("end_time deve ser posterior a start_time.")
        return self


class ShiftSlotUpdate(BaseModel):
    date: DateValue | None = None
    start_time: time | None = None
    end_time: time | None = None
    total_slots: int | None = Field(default=None, ge=1)
    status: ShiftSlotStatus | None = None


class ShiftSlotResponse(BaseModel):
    id: int
    campaign_id: int
    date: DateValue
    start_time: time
    end_time: time
    total_slots: int
    reserved_slots: int
    remaining_slots: int
    status: ShiftSlotStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "use_enum_values": True}


class ShiftSlotAvailabilityResponse(BaseModel):
    campaign_id: int
    slots: list[ShiftSlotResponse]
    total_remaining: int


class ReserveSlotRequest(BaseModel):
    shift_slot_id: int
    reason: str | None = Field(default=None, max_length=512)


class ChangeSlotRequest(BaseModel):
    shift_slot_id: int
    reason: str | None = Field(default=None, max_length=512)


class ReservationAuditResponse(BaseModel):
    id: int
    credit_id: int
    campaign_id: int
    actor_id: int
    from_shift_slot_id: int | None
    to_shift_slot_id: int | None
    action: str
    reason: str | None = None
    origin: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
