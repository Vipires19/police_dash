"""Algoritmo puro de distribuição automática de vagas DEJEM.

Regras:
1. Quantidade base = total // n (interessados), limitada por desejo e limite mensal.
2. Sobras redistribuídas 1 a 1, em rodadas, por ordem de antiguidade do efetivo.
3. Totalmente determinístico / reproduzível.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DistributionCandidate:
    """Entrada de um policial interessado."""

    user_id: int
    desired_slots: int
    patente_rank: int
    display_order: int
    nome_guerra: str


@dataclass(frozen=True)
class DistributionPreview:
    total_available_slots: int
    interested_count: int
    monthly_limit_per_officer: int
    base_quantity: int
    remaining_after_base: int


@dataclass(frozen=True)
class DistributionResult:
    allocations: dict[int, int]  # user_id -> allocated_slots
    base_quantity: int
    remaining_after_base: int
    leftover_slots: int  # vagas que sobraram sem quem pudesse receber


def _seniority_key(c: DistributionCandidate) -> tuple[int, int, str, int]:
    """Mesma ordem do efetivo: patente → display_order → nome_guerra (+ user_id)."""
    return (c.patente_rank, c.display_order, c.nome_guerra.casefold(), c.user_id)


def _cap_desired(desired_slots: int, monthly_limit: int) -> int:
    return max(0, min(desired_slots, monthly_limit))


def preview_distribution(
    total_slots: int,
    monthly_limit: int,
    candidates: list[DistributionCandidate],
) -> DistributionPreview:
    result = compute_distribution(total_slots, monthly_limit, candidates)
    return DistributionPreview(
        total_available_slots=total_slots,
        interested_count=len(candidates),
        monthly_limit_per_officer=monthly_limit,
        base_quantity=result.base_quantity,
        remaining_after_base=result.remaining_after_base,
    )


def compute_distribution(
    total_slots: int,
    monthly_limit: int,
    candidates: list[DistributionCandidate],
) -> DistributionResult:
    """Calcula alocações. Não persiste nada — função pura."""
    if total_slots < 0:
        raise ValueError("total_slots não pode ser negativo")
    if monthly_limit < 0:
        raise ValueError("monthly_limit não pode ser negativo")

    # Deduplicar por user_id mantendo a primeira ocorrência (determinístico).
    seen: set[int] = set()
    unique: list[DistributionCandidate] = []
    for c in candidates:
        if c.user_id in seen:
            continue
        seen.add(c.user_id)
        unique.append(c)

    ordered = sorted(unique, key=_seniority_key)
    n = len(ordered)

    if n == 0 or total_slots == 0:
        return DistributionResult(
            allocations={},
            base_quantity=0,
            remaining_after_base=total_slots,
            leftover_slots=total_slots,
        )

    max_by_user = {
        c.user_id: _cap_desired(c.desired_slots, monthly_limit) for c in ordered
    }
    # Filtrar quem não pode receber nada (desejo 0 após cap).
    eligible_ids = [c.user_id for c in ordered if max_by_user[c.user_id] > 0]
    if not eligible_ids:
        return DistributionResult(
            allocations={},
            base_quantity=0,
            remaining_after_base=total_slots,
            leftover_slots=total_slots,
        )

    base = total_slots // n
    allocated: dict[int, int] = {uid: 0 for uid in eligible_ids}

    # Etapa 1 — quantidade base (respeitando desejo/limite).
    for uid in eligible_ids:
        take = min(base, max_by_user[uid])
        allocated[uid] = take

    remaining = total_slots - sum(allocated.values())
    remaining_after_base = remaining

    # Etapa 2 — redistribuição 1 a 1 por antiguidade, em rodadas.
    seniority_order = [uid for uid in (c.user_id for c in ordered) if uid in allocated]

    while remaining > 0:
        round_receivers = [
            uid for uid in seniority_order if allocated[uid] < max_by_user[uid]
        ]
        if not round_receivers:
            break
        for uid in round_receivers:
            if remaining <= 0:
                break
            allocated[uid] += 1
            remaining -= 1

    return DistributionResult(
        allocations=allocated,
        base_quantity=base,
        remaining_after_base=remaining_after_base,
        leftover_slots=remaining,
    )
