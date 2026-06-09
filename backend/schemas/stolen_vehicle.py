from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class StolenVehicleTypeEnum(str, Enum):
    CARRO = "CARRO"
    MOTO = "MOTO"


class StolenOccurrenceTypeEnum(str, Enum):
    FURTO = "FURTO"
    ROUBO = "ROUBO"


class StolenVehicleCreate(BaseModel):
    vehicle_type: StolenVehicleTypeEnum
    plate: str = Field(min_length=1, max_length=16)
    vehicle_model: str = Field(min_length=1, max_length=128)
    color: str = Field(min_length=1, max_length=64)
    year: int = Field(ge=1900, le=2100)
    occurrence_type: StolenOccurrenceTypeEnum
    observation: str | None = Field(default=None, max_length=4000)


class StolenVehicleRecoverBody(BaseModel):
    recovered_notes: str | None = Field(default=None, max_length=4000)


class StolenVehiclePublic(BaseModel):
    id: int
    vehicle_type: StolenVehicleTypeEnum
    plate: str
    vehicle_model: str
    color: str
    year: int
    occurrence_type: StolenOccurrenceTypeEnum
    plate_group: int = Field(ge=0, le=9)
    observation: str | None
    is_recovered: bool
    recovered_at: datetime | None
    recovered_by_id: int | None
    recovered_notes: str | None
    created_at: datetime
    created_by_id: int

    model_config = {"from_attributes": True}


class StolenVehicleSheetEntry(BaseModel):
    id: int | None = None
    plate: str | None = None
    vehicle_model: str | None = None
    color: str | None = None
    year: int | None = None
    occurrence_type: StolenOccurrenceTypeEnum | None = None


class StolenVehicleSheetGroup(BaseModel):
    group: int
    slots: list[StolenVehicleSheetEntry]


class StolenVehicleSheetResponse(BaseModel):
    carros: list[StolenVehicleSheetGroup]
    motos: list[StolenVehicleSheetGroup]
