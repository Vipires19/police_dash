from datetime import date, datetime

from pydantic import BaseModel, Field

from models.leaves import LeaveStatus, LeaveType


class LeaveRequestCreate(BaseModel):
    leave_on: date
    leave_type: LeaveType
    user_compensation_id: int | None = None


class LeaveDecisionBody(BaseModel):
    motivo: str | None = Field(default=None, max_length=4000)


class LeaveRejectBody(BaseModel):
    motivo: str = Field(..., min_length=1, max_length=4000)


class CalendarLeaveEntry(BaseModel):
    id: int
    leave_on: date
    user_id: int
    patente: str
    nome_guerra: str
    display_order: int
    leave_type: LeaveType
    status: LeaveStatus
    operational_rank: int

    model_config = {"from_attributes": False}


class CalendarDay(BaseModel):
    date: date
    entries: list[CalendarLeaveEntry]
    active_count: int
    is_critical: bool


class LeaveCalendarSummary(BaseModel):
    my_pending_count: int
    command_pending_leaves: int | None = None
    command_pending_compensations: int | None = None
    critical_days: list[date] | None = None


class YearMonth(BaseModel):
    year: int
    month: int


class LeaveBookingPolicy(BaseModel):
    reference_date: date
    allowed_year_months: list[YearMonth]
    operational_hint: str


class LeaveCalendarResponse(BaseModel):
    year: int
    month: int
    days: list[CalendarDay]
    summary: LeaveCalendarSummary
    booking_policy: LeaveBookingPolicy


class LeaveRequestPublic(BaseModel):
    id: int
    user_id: int
    leave_on: date
    leave_type: LeaveType
    user_compensation_id: int | None
    status: LeaveStatus
    review_reason: str | None
    decision_motivo: str | None
    decided_by_id: int | None
    decided_at: datetime | None
    created_at: datetime
    patente: str | None = None
    nome_guerra: str | None = None
    display_order: int | None = None

    model_config = {"from_attributes": False}
