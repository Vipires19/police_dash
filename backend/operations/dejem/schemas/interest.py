"""Schemas de Interest."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from models.user import OrganizationalUnit
from operations.dejem.models.enums import CampaignStatus


class InterestCreate(BaseModel):
    """Registrar ou atualizar interesse (upsert)."""

    campaign_id: int
    desired_slots: int = Field(ge=1)


class InterestUpdate(BaseModel):
    """Editar quantidade desejada."""

    campaign_id: int
    desired_slots: int = Field(ge=1)


class InterestResponse(BaseModel):
    id: int
    campaign_id: int
    police_officer_id: int
    desired_slots: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InterestMyResponse(BaseModel):
    """Meu interesse com contexto da campanha."""

    id: int
    campaign_id: int
    campaign_month: int
    campaign_year: int
    campaign_status: CampaignStatus
    desired_slots: int
    created_at: datetime
    updated_at: datetime


class InterestAdminRow(BaseModel):
    id: int
    campaign_id: int
    police_officer_id: int
    desired_slots: int
    created_at: datetime
    updated_at: datetime
    patente: str
    nome_guerra: str
    full_name: str | None
    role: str
    organizational_unit: OrganizationalUnit


class InterestAdminListResponse(BaseModel):
    campaign_id: int
    participants_count: int
    total_desired_slots: int
    items: list[InterestAdminRow]


class InterestStatisticsResponse(BaseModel):
    campaign_id: int
    interested_officers: int
    total_desired_slots: int
    average_desired_slots: float
    max_desired_slots: int
    min_desired_slots: int
