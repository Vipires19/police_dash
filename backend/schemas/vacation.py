from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from core.absence_labels import is_restricted_absence
from models.vacation import VacationStatus, VacationType

ALLOWED_VACATION_DURATIONS = (15, 30)


class VacationRequestCreate(BaseModel):
    start_date: date
    end_date: date
    vacation_type: VacationType
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_range(self) -> "VacationRequestCreate":
        if self.end_date < self.start_date:
            raise ValueError("Data final deve ser igual ou posterior à inicial")
        total = (self.end_date - self.start_date).days + 1
        if is_restricted_absence(self.vacation_type):
            if total not in ALLOWED_VACATION_DURATIONS:
                raise ValueError("Férias e LP: período permitido apenas de 15 ou 30 dias corridos")
        elif total < 1:
            raise ValueError("Período inválido")
        return self


class VacationRequestUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    vacation_type: VacationType | None = None
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_partial_range(self) -> "VacationRequestUpdate":
        if self.start_date is not None and self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("Data final deve ser igual ou posterior à inicial")
        return self


class VacationDecisionBody(BaseModel):
    reason: str | None = Field(default=None, max_length=4000)


class VacationRejectBody(BaseModel):
    reason: str = Field(..., min_length=1, max_length=4000)


class CalendarVacationEntry(BaseModel):
    id: int
    user_id: int
    patente: str
    nome_guerra: str
    display_order: int
    vacation_type: VacationType
    status: VacationStatus
    start_date: date
    end_date: date
    total_days: int
    notes: str | None = None
    operational_rank: int

    model_config = {"from_attributes": False}


class CalendarDay(BaseModel):
    date: date
    entries: list[CalendarVacationEntry]
    active_count: int
    is_critical: bool


class VacationCalendarSummary(BaseModel):
    my_pending_count: int
    command_pending_vacations: int | None = None
    critical_days: list[date] | None = None
    currently_away_count: int | None = None


class VacationCalendarResponse(BaseModel):
    year: int
    month: int
    days: list[CalendarDay]
    summary: VacationCalendarSummary


class VacationRequestPublic(BaseModel):
    id: int
    user_id: int
    vacation_type: VacationType
    start_date: date
    end_date: date
    total_days: int
    status: VacationStatus
    review_reason: str | None
    notes: str | None
    decision_reason: str | None
    approved_by_id: int | None
    approved_at: datetime | None
    created_at: datetime
    patente: str | None = None
    nome_guerra: str | None = None
    display_order: int | None = None

    model_config = {"from_attributes": False}
