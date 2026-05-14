from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from models.compensations import CompensationStatus, CompensationType, UserCompensationStatus


class CompensationEventCreate(BaseModel):
    event_type: CompensationType
    motivo: str = Field(..., min_length=3, max_length=8000)
    participant_user_ids: list[int] = Field(..., min_length=1)


class CompensationDecisionBody(BaseModel):
    motivo: str | None = Field(default=None, max_length=4000)


class CompensationRejectBody(BaseModel):
    motivo: str = Field(..., min_length=1, max_length=4000)


class CompensationEventPublic(BaseModel):
    id: int
    event_type: CompensationType
    motivo: str
    status: CompensationStatus
    created_by_id: int
    decided_by_id: int | None
    decided_at: datetime | None
    decision_motivo: str | None
    created_at: datetime
    participant_user_ids: list[int] = Field(default_factory=list)

    model_config = {"from_attributes": False}


class UserCompensationPublic(BaseModel):
    id: int
    user_id: int
    compensation_event_id: int
    status: UserCompensationStatus
    created_at: datetime
    display_label: str = ""

    model_config = {"from_attributes": True}


class UserCompensationAvailablePublic(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    compensation_type: CompensationType = Field(validation_alias="type", serialization_alias="type")
    label: str
    event_date: date
    description: str
