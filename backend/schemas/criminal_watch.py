from datetime import datetime

from pydantic import BaseModel, Field


class VehicleQruCodeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    description: str = Field(min_length=1, max_length=256)


class VehicleQruCodeUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=16)
    description: str | None = Field(default=None, min_length=1, max_length=256)


class VehicleQruCodePublic(BaseModel):
    id: int
    code: str
    description: str
    is_active: bool
    created_at: datetime
    created_by_id: int

    model_config = {"from_attributes": True}


class CriminalWatchVehicleCreate(BaseModel):
    plate: str = Field(min_length=1, max_length=16)
    vehicle_model: str = Field(min_length=1, max_length=128)
    color: str = Field(min_length=1, max_length=64)
    year: int = Field(ge=1900, le=2100)
    qru_code_id: int
    initial_note: str = Field(min_length=1, max_length=4000)


class CriminalWatchNoteCreate(BaseModel):
    note: str = Field(min_length=1, max_length=4000)


class CriminalWatchNotePublic(BaseModel):
    id: int
    vehicle_id: int
    note: str
    created_at: datetime
    created_by_id: int
    created_by_label: str | None = None

    model_config = {"from_attributes": True}


class CriminalWatchVehiclePublic(BaseModel):
    id: int
    plate: str
    vehicle_model: str
    color: str
    year: int
    qru_code_id: int
    qru_code: str
    qru_description: str
    created_at: datetime
    created_by_id: int
    created_by_label: str | None = None

    model_config = {"from_attributes": True}


class CriminalWatchVehicleDetail(CriminalWatchVehiclePublic):
    notes: list[CriminalWatchNotePublic]


class CriminalWatchSheetEntry(BaseModel):
    id: int | None = None
    plate_numeric: str | None = None
    plate_letters: str | None = None
    vehicle_model: str | None = None
    color_abbr: str | None = None
    year_short: str | None = None
    qru_code: str | None = None


class CriminalWatchSheetResponse(BaseModel):
    slots: list[CriminalWatchSheetEntry]
