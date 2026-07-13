from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DejemMonthStatusEnum(str, Enum):
    OPEN_INTEREST = "OPEN_INTEREST"
    DISTRIBUTED_PENDING = "DISTRIBUTED_PENDING"
    DISTRIBUTED = "DISTRIBUTED"
    OPEN_SHIFTS = "OPEN_SHIFTS"
    FINISHED = "FINISHED"


class DejemShiftStatusEnum(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    FINISHED = "FINISHED"


class ParticipationTypeEnum(str, Enum):
    NORMAL = "NORMAL"
    EXTRAORDINARY = "EXTRAORDINARY"
    SUBSTITUTION = "SUBSTITUTION"


class ParticipantStatusEnum(str, Enum):
    REGISTERED = "REGISTERED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


# --- DejemMonth ---


class DejemMonthCreate(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    total_available_slots: int = Field(ge=0)
    monthly_limit_per_officer: int = Field(ge=1)


class DejemMonthUpdate(BaseModel):
    total_available_slots: int | None = Field(default=None, ge=0)
    monthly_limit_per_officer: int | None = Field(default=None, ge=1)


class DejemMonthPublic(BaseModel):
    id: int
    year: int
    month: int
    total_available_slots: int
    monthly_limit_per_officer: int
    status: DejemMonthStatusEnum
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    interested_count: int = 0

    model_config = {"from_attributes": True}


# --- DejemInterest ---


class DejemInterestUpsert(BaseModel):
    interested: bool
    desired_slots: int = Field(default=0, ge=0)


class DejemInterestPublic(BaseModel):
    id: int
    month_id: int
    user_id: int
    interested: bool
    desired_slots: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DejemInterestAdminRow(BaseModel):
    id: int
    month_id: int
    user_id: int
    interested: bool
    desired_slots: int
    created_at: datetime
    patente: str
    nome_guerra: str
    full_name: str | None
    role: str
    organizational_unit: str

    model_config = {"from_attributes": True}


# --- Distribution / Allocation ---


class DejemDistributionPreview(BaseModel):
    month_id: int
    total_available_slots: int
    interested_count: int
    monthly_limit_per_officer: int
    base_quantity: int
    remaining_after_base: int


class DejemAllocationPublic(BaseModel):
    id: int
    month_id: int
    user_id: int
    allocated_slots: int
    used_slots: int
    remaining_slots: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DejemAllocationAdminRow(BaseModel):
    id: int
    month_id: int
    user_id: int
    allocated_slots: int
    used_slots: int
    remaining_slots: int
    created_at: datetime
    desired_slots: int
    patente: str
    nome_guerra: str
    full_name: str | None
    role: str
    organizational_unit: str
    display_order: int


class DejemDistributeResponse(BaseModel):
    month: DejemMonthPublic
    preview: DejemDistributionPreview
    leftover_slots: int
    allocations: list[DejemAllocationAdminRow]
