from datetime import date as Date
from datetime import datetime, time as Time
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
    READY_FOR_MAP = "READY_FOR_MAP"
    INTEGRATED = "INTEGRATED"
    FINISHED = "FINISHED"


class DejemShiftTypeEnum(str, Enum):
    FT = "FT"
    ROCAM = "ROCAM"
    OUTROS = "OUTROS"


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


# --- Shifts ---


class DejemShiftCreate(BaseModel):
    month_id: int
    date: Date
    start_time: Time
    end_time: Time
    shift_type: DejemShiftTypeEnum = DejemShiftTypeEnum.FT
    capacity: int = Field(ge=0)
    status: DejemShiftStatusEnum = DejemShiftStatusEnum.OPEN
    vehicle_id: int | None = None


class DejemShiftUpdate(BaseModel):
    date: Date | None = None
    start_time: Time | None = None
    end_time: Time | None = None
    shift_type: DejemShiftTypeEnum | None = None
    capacity: int | None = Field(default=None, ge=0)
    status: DejemShiftStatusEnum | None = None
    vehicle_id: int | None = None


class DejemShiftPublic(BaseModel):
    id: int
    month_id: int
    date: Date
    start_time: Time
    end_time: Time
    shift_type: DejemShiftTypeEnum
    capacity: int
    filled_slots: int = 0
    available_slots: int = 0
    status: DejemShiftStatusEnum
    vehicle_id: int | None = None
    vehicle_prefixo: str | None = None
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DejemShiftCalendarDay(BaseModel):
    date: Date
    shift_count: int
    total_capacity: int
    total_filled: int
    has_open: bool
    has_closed: bool
    has_finished: bool


class DejemShiftCalendarResponse(BaseModel):
    year: int
    month: int
    month_id: int | None
    days: list[DejemShiftCalendarDay]


class DejemShiftDayDetail(BaseModel):
    date: Date
    month_id: int | None
    shifts: list[DejemShiftPublic]


class DejemShiftDashboard(BaseModel):
    month_id: int
    year: int
    month: int
    total_shifts: int
    open_shifts: int
    closed_shifts: int
    finished_shifts: int
    integrated_shifts: int = 0
    total_capacity: int
    total_filled: int
    total_available: int
    avg_remaining_slots: float = 0.0


# --- Enrollment (fase 4.5) ---


class DejemAdminAddParticipant(BaseModel):
    user_id: int
    participation_type: ParticipationTypeEnum = ParticipationTypeEnum.NORMAL


class DejemParticipantAdminRow(BaseModel):
    id: int
    shift_id: int
    user_id: int
    participation_type: ParticipationTypeEnum
    status: ParticipantStatusEnum
    consumes_balance: bool
    created_at: datetime
    enrolled_by_id: int | None = None
    patente: str
    nome_guerra: str
    full_name: str | None = None
    remaining_slots: int = 0


class DejemEnrollmentResult(BaseModel):
    participant_id: int
    shift_id: int
    user_id: int
    participation_type: ParticipationTypeEnum
    status: ParticipantStatusEnum
    consumes_balance: bool
    remaining_slots: int | None = None
    created_at: datetime


class DejemMyShiftCard(BaseModel):
    id: int
    month_id: int
    date: Date
    start_time: Time
    end_time: Time
    shift_type: DejemShiftTypeEnum
    capacity: int
    filled_slots: int
    available_slots: int
    status: DejemShiftStatusEnum
    i_am_enrolled: bool = False
    my_participation_type: ParticipationTypeEnum | None = None


class DejemMyDayDetail(BaseModel):
    date: Date
    month_id: int | None
    shifts: list[DejemMyShiftCard]


class DejemMapMember(BaseModel):
    user_id: int
    patente: str
    nome_guerra: str
    display_order: int = 0


class DejemMapBlock(BaseModel):
    shift_id: int
    title: str
    shift_type: DejemShiftTypeEnum
    start_time: Time
    end_time: Time
    status: DejemShiftStatusEnum
    vehicle_prefixo: str | None = None
    members: list[DejemMapMember]


class DejemShiftTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    shift_type: DejemShiftTypeEnum = DejemShiftTypeEnum.FT
    start_time: Time
    end_time: Time
    default_capacity: int = Field(ge=0)
    is_active: bool = True


class DejemShiftTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    shift_type: DejemShiftTypeEnum | None = None
    start_time: Time | None = None
    end_time: Time | None = None
    default_capacity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class DejemShiftTemplatePublic(BaseModel):
    id: int
    name: str
    shift_type: DejemShiftTypeEnum
    start_time: Time
    end_time: Time
    default_capacity: int
    is_active: bool
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Geração automática (fase 4.4.1) ---


class DejemMonthGenerateRequest(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    weekdays: list[int] = Field(
        min_length=1,
        description="Dias da semana: 0=segunda … 6=domingo (igual a date.weekday()).",
    )
    template_ids: list[int] = Field(min_length=1)
    replace_existing: bool = False
    ignore_holidays: bool = False  # reservado para fase futura


class DejemMonthGenerateResult(BaseModel):
    year: int
    month: int
    month_id: int
    created: int
    ignored: int
    replaced: int
    elapsed_ms: int


class DejemMonthGeneratePreviewItem(BaseModel):
    date: Date
    start_time: Time
    end_time: Time
    shift_type: DejemShiftTypeEnum
    capacity: int
    template_id: int
    template_name: str
    action: str  # CREATE | IGNORE | REPLACE
    status_label: str
    existing_shift_id: int | None = None


class DejemMonthGeneratePreview(BaseModel):
    year: int
    month: int
    month_id: int
    days_in_month: int
    selected_days_count: int
    weekdays: list[int]
    weekday_labels: list[str]
    template_names: list[str]
    replace_existing: bool
    planned_shifts: int
    planned_capacity: int
    create_count: int
    ignore_count: int
    replace_count: int
    create_capacity: int
    replace_capacity: int
    existing_conflicts: int
    items: list[DejemMonthGeneratePreviewItem]
    elapsed_ms: int
