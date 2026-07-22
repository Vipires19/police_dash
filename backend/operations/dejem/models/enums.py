"""Enums do domínio conceitual DEJEM."""

from __future__ import annotations

import enum


class CampaignStatus(str, enum.Enum):
    """Ciclo de vida da campanha mensal.

    Mapeamento com `DejemMonthStatus` (produção):
    - CREATED               ↔ CREATED
    - OPEN                  ↔ OPEN_INTEREST
    - REGISTRATION_CLOSED   ↔ DISTRIBUTED_PENDING
    - ALLOCATED             ↔ DISTRIBUTED
    - RUNNING               ↔ OPEN_SHIFTS
    - CLOSED                ↔ FINISHED
    """

    CREATED = "CREATED"
    OPEN = "OPEN"
    REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
    ALLOCATED = "ALLOCATED"
    RUNNING = "RUNNING"
    CLOSED = "CLOSED"


class CreditStatus(str, enum.Enum):
    """Ciclo de vida de um crédito individual DEJEM."""

    AVAILABLE = "AVAILABLE"
    DATE_SELECTED = "DATE_SELECTED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"


class OfferEventType(str, enum.Enum):
    """Tipo de evento de oferta (append-only)."""

    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    ADJUSTMENT = "ADJUSTMENT"


class ShiftSlotStatus(str, enum.Enum):
    """Disponibilidade operacional de um turno (ShiftSlot)."""

    OPEN = "OPEN"
    FULL = "FULL"
    CLOSED = "CLOSED"


class TeamType(str, enum.Enum):
    """Tipo de equipe operacional (expansível)."""

    FT = "FT"
    ROCAM = "ROCAM"
    APOIO = "APOIO"
    ADMINISTRATIVO = "ADMINISTRATIVO"


class TeamStatus(str, enum.Enum):
    """Status de planejamento (sem publicação nesta sprint)."""

    DRAFT = "DRAFT"
    READY = "READY"


class AssignmentRole(str, enum.Enum):
    """Papel do policial na equipe (paridade Escala Operacional)."""

    MEMBER = "MEMBER"
    COMMANDER = "COMMANDER"
    DRIVER = "DRIVER"
    THIRD_MAN = "THIRD_MAN"
    FOURTH_MAN = "FOURTH_MAN"
    MOTO_2 = "MOTO_2"
    MOTO_3 = "MOTO_3"


class PublishedScheduleStatus(str, enum.Enum):
    """Status de uma versão publicada."""

    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"

