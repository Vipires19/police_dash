from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class VehicleModalidadeEnum(str, Enum):
    FT = "FT"
    ROCAM = "ROCAM"


class VehicleStatusEnum(str, Enum):
    OPERANDO = "OPERANDO"
    BAIXADA = "BAIXADA"
    MANUTENCAO = "MANUTENCAO"
    RESERVA = "RESERVA"


class VehicleActionTypeEnum(str, Enum):
    CREATED = "CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    RETURNED = "RETURNED"
    UPDATED = "UPDATED"


class VehicleCreate(BaseModel):
    placa: str = Field(min_length=1, max_length=16)
    prefixo: str = Field(min_length=1, max_length=32)
    modelo: str = Field(min_length=1, max_length=128)
    modalidade: VehicleModalidadeEnum
    status: VehicleStatusEnum = VehicleStatusEnum.OPERANDO


class VehicleUpdate(BaseModel):
    placa: str | None = Field(default=None, min_length=1, max_length=16)
    prefixo: str | None = Field(default=None, min_length=1, max_length=32)
    modelo: str | None = Field(default=None, min_length=1, max_length=128)
    modalidade: VehicleModalidadeEnum | None = None


class VehicleStatusChange(BaseModel):
    new_status: VehicleStatusEnum
    motivo: str = Field(min_length=1, max_length=2000)


class VehiclePublic(BaseModel):
    id: int
    placa: str
    prefixo: str
    modelo: str
    modalidade: VehicleModalidadeEnum
    status: VehicleStatusEnum
    baixada_at: datetime | None
    retorno_operacao_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "use_enum_values": True}


class VehicleLogPublic(BaseModel):
    id: int
    vehicle_id: int
    user_id: int
    action_type: VehicleActionTypeEnum
    description: str
    motivo: str | None
    old_status: VehicleStatusEnum | None
    new_status: VehicleStatusEnum | None
    created_at: datetime

    model_config = {"from_attributes": True, "use_enum_values": True}


class VehicleLogFeedItem(VehicleLogPublic):
    """Log com dados extras para feed do dashboard."""

    vehicle_prefixo: str
    actor_label: str

    model_config = {"from_attributes": True, "use_enum_values": True}
