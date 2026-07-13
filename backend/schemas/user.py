from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


class RoleEnum(str, Enum):
    ADMIN = "ADMIN"
    CMD_TATICO = "CMD_TATICO"
    TAT_CMD = "TAT_CMD"
    ADM = "ADM"
    N90 = "N90"
    BRACAL = "BRACAL"
    ESTAGIO = "ESTAGIO"


class OrganizationalUnitEnum(str, Enum):
    FIRST_PLATOON = "FIRST_PLATOON"
    SECOND_PLATOON = "SECOND_PLATOON"
    COMPANY_ADMIN = "COMPANY_ADMIN"


class StatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    patente: str = Field(min_length=1, max_length=64)
    nome_guerra: str = Field(min_length=1, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    patente: str
    nome_guerra: str
    full_name: str | None
    re: str | None
    address: str | None
    phone: str | None
    birth_date: date | None
    blood_type: str | None
    display_order: int
    is_active: bool
    role: RoleEnum
    organizational_unit: OrganizationalUnitEnum
    status: StatusEnum
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    re: str | None = Field(default=None, max_length=32)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=32)
    birth_date: date | None = None
    blood_type: str | None = Field(default=None, max_length=8)
    patente: str | None = Field(default=None, min_length=1, max_length=64)
    nome_guerra: str | None = Field(default=None, min_length=1, max_length=128)
    is_active: bool | None = None
    role: RoleEnum | None = None
    organizational_unit: OrganizationalUnitEnum | None = None


class EfetivoReorderBody(BaseModel):
    patente: str = Field(min_length=1, max_length=64)
    ordered_user_ids: list[int] = Field(min_length=1)


class ApproveUserBody(BaseModel):
    decision: Literal["approve", "reject"]
    role: RoleEnum | None = None
    organizational_unit: OrganizationalUnitEnum | None = None

    @model_validator(mode="after")
    def require_role_and_unit_on_approve(self):
        if self.decision == "approve":
            if self.role is None:
                raise ValueError("role é obrigatório quando decision=approve")
            if self.organizational_unit is None:
                raise ValueError("organizational_unit é obrigatório quando decision=approve")
        return self
