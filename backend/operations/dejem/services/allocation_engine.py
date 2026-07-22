"""Algoritmo puro do Allocation Engine (Sprint C5).

Distribuição igualitária. Sobras NÃO são redistribuídas (C6).
Função pura — sem I/O.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EqualDistributionResult:
    """Resultado determinístico da divisão igualitária."""

    allocations: dict[int, int]  # police_officer_id -> slots
    slots_per_officer: int
    interested_count: int
    available_slots: int
    distributed_slots: int
    remaining_slots: int


def equal_distribute(
    available_slots: int,
    officer_ids: list[int],
) -> EqualDistributionResult:
    """
    Cada policial recebe ``available // n`` vagas.
    O resto ``available % n`` permanece em ``remaining_slots``.
    """
    if available_slots < 0:
        raise ValueError("available_slots não pode ser negativo")

    # Ordem estável / determinística
    unique: list[int] = []
    seen: set[int] = set()
    for oid in officer_ids:
        if oid in seen:
            continue
        seen.add(oid)
        unique.append(oid)
    unique.sort()

    n = len(unique)
    if n == 0 or available_slots == 0:
        return EqualDistributionResult(
            allocations={},
            slots_per_officer=0,
            interested_count=n,
            available_slots=available_slots,
            distributed_slots=0,
            remaining_slots=available_slots,
        )

    per = available_slots // n
    remaining = available_slots % n
    allocations = {oid: per for oid in unique}
    # Se per == 0, ninguém recebe; tudo fica em remaining
    if per == 0:
        return EqualDistributionResult(
            allocations={},
            slots_per_officer=0,
            interested_count=n,
            available_slots=available_slots,
            distributed_slots=0,
            remaining_slots=available_slots,
        )

    return EqualDistributionResult(
        allocations=allocations,
        slots_per_officer=per,
        interested_count=n,
        available_slots=available_slots,
        distributed_slots=per * n,
        remaining_slots=remaining,
    )
