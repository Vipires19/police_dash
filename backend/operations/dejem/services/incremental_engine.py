"""Algoritmo puro de distribuição incremental (Sprint C6).

Distribui N vagas 1-a-1 por ordem de antiguidade.
Não recalcula a campanha inteira.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.ranks import patente_sort_key


@dataclass(frozen=True)
class PriorityCandidate:
    police_officer_id: int
    patente: str
    display_order: int
    nome_guerra: str


@dataclass(frozen=True)
class IncrementalDistributeResult:
    grants: dict[int, int]  # officer_id -> slots granted
    distributed: int
    remaining: int


def seniority_key(c: PriorityCandidate) -> tuple[int, int, str, int]:
    rank, _ = patente_sort_key(c.patente)
    return (rank, c.display_order, c.nome_guerra.casefold(), c.police_officer_id)


def order_by_seniority(candidates: list[PriorityCandidate]) -> list[PriorityCandidate]:
    """Ordem de antiguidade do efetivo; fallback determinístico por id."""
    return sorted(candidates, key=seniority_key)


def distribute_by_seniority(
    slots: int,
    candidates: list[PriorityCandidate],
) -> IncrementalDistributeResult:
    """
    Atribui ``slots`` vagas em rodadas 1-a-1 na ordem de antiguidade.
    Sobras (se lista vazia) permanecem em ``remaining``.
    """
    if slots < 0:
        raise ValueError("slots não pode ser negativo")

    ordered = order_by_seniority(candidates)
    if slots == 0 or not ordered:
        return IncrementalDistributeResult(grants={}, distributed=0, remaining=slots)

    grants: dict[int, int] = {c.police_officer_id: 0 for c in ordered}
    remaining = slots
    while remaining > 0:
        for c in ordered:
            if remaining <= 0:
                break
            grants[c.police_officer_id] += 1
            remaining -= 1

    return IncrementalDistributeResult(
        grants={oid: n for oid, n in grants.items() if n > 0},
        distributed=slots - remaining,
        remaining=remaining,
    )
