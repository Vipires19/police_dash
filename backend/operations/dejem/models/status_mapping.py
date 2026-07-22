"""Mapeamento CampaignStatus ↔ DejemMonthStatus + máquina de estados."""

from __future__ import annotations

from models.dejem import DejemMonthStatus
from operations.dejem.models.enums import CampaignStatus

# Transições válidas (grafo linear).
ALLOWED_TRANSITIONS: dict[CampaignStatus, frozenset[CampaignStatus]] = {
    CampaignStatus.CREATED: frozenset({CampaignStatus.OPEN}),
    CampaignStatus.OPEN: frozenset({CampaignStatus.REGISTRATION_CLOSED}),
    CampaignStatus.REGISTRATION_CLOSED: frozenset({CampaignStatus.ALLOCATED}),
    CampaignStatus.ALLOCATED: frozenset({CampaignStatus.RUNNING}),
    CampaignStatus.RUNNING: frozenset({CampaignStatus.CLOSED}),
    CampaignStatus.CLOSED: frozenset(),
}

_TO_LEGACY: dict[CampaignStatus, DejemMonthStatus] = {
    CampaignStatus.CREATED: DejemMonthStatus.CREATED,
    CampaignStatus.OPEN: DejemMonthStatus.OPEN_INTEREST,
    CampaignStatus.REGISTRATION_CLOSED: DejemMonthStatus.DISTRIBUTED_PENDING,
    CampaignStatus.ALLOCATED: DejemMonthStatus.DISTRIBUTED,
    CampaignStatus.RUNNING: DejemMonthStatus.OPEN_SHIFTS,
    CampaignStatus.CLOSED: DejemMonthStatus.FINISHED,
}

_FROM_LEGACY: dict[DejemMonthStatus, CampaignStatus] = {
    legacy: conceptual for conceptual, legacy in _TO_LEGACY.items()
}


def to_legacy(status: CampaignStatus) -> DejemMonthStatus:
    return _TO_LEGACY[status]


def from_legacy(status: DejemMonthStatus) -> CampaignStatus:
    try:
        return _FROM_LEGACY[status]
    except KeyError as exc:
        raise ValueError(f"Status legado sem mapeamento: {status}") from exc


def can_transition(current: CampaignStatus, target: CampaignStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def assert_transition(current: CampaignStatus, target: CampaignStatus) -> None:
    if current == target:
        raise ValueError(f"Campanha já está em {current.value}.")
    if not can_transition(current, target):
        allowed = ", ".join(sorted(s.value for s in ALLOWED_TRANSITIONS.get(current, frozenset())))
        hint = f" Permitidas a partir de {current.value}: {allowed}." if allowed else " Campanha encerrada."
        raise ValueError(
            f"Transição inválida: {current.value} → {target.value}.{hint}"
        )
