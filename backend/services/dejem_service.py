"""Serviço do módulo DEJEM — fases 4.2 (interesse) e 4.3 (distribuição)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from core.ranks import patente_sort_key
from models.dejem import DejemAllocation, DejemInterest, DejemMonth, DejemMonthStatus
from models.user import User
from repositories.dejem_repository import (
    DejemAllocationRepository,
    DejemInterestRepository,
    DejemMonthRepository,
)
from schemas.dejem import (
    DejemAllocationAdminRow,
    DejemAllocationPublic,
    DejemDistributeResponse,
    DejemDistributionPreview,
    DejemInterestAdminRow,
    DejemInterestPublic,
    DejemInterestUpsert,
    DejemMonthCreate,
    DejemMonthPublic,
    DejemMonthUpdate,
)
from services.dejem_distribution_service import (
    DistributionCandidate,
    compute_distribution,
)


class DejemError(ValueError):
    """Erro de regra de negócio do módulo DEJEM."""


def _month_to_public(month: DejemMonth, interested_count: int = 0) -> DejemMonthPublic:
    return DejemMonthPublic(
        id=month.id,
        year=month.year,
        month=month.month,
        total_available_slots=month.total_available_slots,
        monthly_limit_per_officer=month.monthly_limit_per_officer,
        status=month.status,  # type: ignore[arg-type]
        created_by_id=month.created_by_id,
        created_at=month.created_at,
        updated_at=month.updated_at,
        interested_count=interested_count,
    )


def _interest_to_public(row: DejemInterest) -> DejemInterestPublic:
    return DejemInterestPublic.model_validate(row)


def _interest_to_admin_row(row: DejemInterest) -> DejemInterestAdminRow:
    user = row.user
    return DejemInterestAdminRow(
        id=row.id,
        month_id=row.month_id,
        user_id=row.user_id,
        interested=row.interested,
        desired_slots=row.desired_slots,
        created_at=row.created_at,
        patente=user.patente,
        nome_guerra=user.nome_guerra,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        organizational_unit=(
            user.organizational_unit.value
            if hasattr(user.organizational_unit, "value")
            else str(user.organizational_unit)
        ),
    )


def _allocation_to_public(row: DejemAllocation) -> DejemAllocationPublic:
    return DejemAllocationPublic.model_validate(row)


def _allocation_to_admin_row(
    row: DejemAllocation,
    desired_slots: int,
) -> DejemAllocationAdminRow:
    user = row.user
    return DejemAllocationAdminRow(
        id=row.id,
        month_id=row.month_id,
        user_id=row.user_id,
        allocated_slots=row.allocated_slots,
        used_slots=row.used_slots,
        remaining_slots=row.remaining_slots,
        created_at=row.created_at,
        desired_slots=desired_slots,
        patente=user.patente,
        nome_guerra=user.nome_guerra,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        organizational_unit=(
            user.organizational_unit.value
            if hasattr(user.organizational_unit, "value")
            else str(user.organizational_unit)
        ),
        display_order=user.display_order,
    )


def _require_open_interest(month: DejemMonth) -> None:
    if month.status != DejemMonthStatus.OPEN_INTEREST:
        raise DejemError("A manifestação de interesse já foi encerrada para este mês.")


def _validate_desired_slots(
    interested: bool,
    desired_slots: int,
    monthly_limit: int,
) -> int:
    if not interested:
        return 0
    if desired_slots < 1:
        raise DejemError("A quantidade desejada deve ser no mínimo 1.")
    if desired_slots > monthly_limit:
        raise DejemError(
            f"A quantidade desejada não pode exceder o limite mensal ({monthly_limit})."
        )
    return desired_slots


def _build_candidates(interests: list[DejemInterest]) -> list[DistributionCandidate]:
    candidates: list[DistributionCandidate] = []
    for row in interests:
        user = row.user
        rank, _ = patente_sort_key(user.patente)
        candidates.append(
            DistributionCandidate(
                user_id=user.id,
                desired_slots=row.desired_slots,
                patente_rank=rank,
                display_order=user.display_order,
                nome_guerra=user.nome_guerra,
            )
        )
    return candidates


def _sorted_admin_allocations(
    rows: list[DejemAllocation],
    desired_by_user: dict[int, int],
) -> list[DejemAllocationAdminRow]:
    mapped = [
        _allocation_to_admin_row(r, desired_by_user.get(r.user_id, 0)) for r in rows
    ]
    return sorted(
        mapped,
        key=lambda r: (
            patente_sort_key(r.patente)[0],
            r.display_order,
            r.nome_guerra.casefold(),
            r.user_id,
        ),
    )


# --- Months ---


def list_months(db: Session) -> list[DejemMonthPublic]:
    repo = DejemMonthRepository(db)
    months = repo.list_all()
    return [_month_to_public(m, repo.count_interested(m.id)) for m in months]


def get_month(db: Session, month_id: int) -> DejemMonthPublic:
    repo = DejemMonthRepository(db)
    month = repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    return _month_to_public(month, repo.count_interested(month.id))


def create_month(db: Session, current: User, body: DejemMonthCreate) -> DejemMonthPublic:
    repo = DejemMonthRepository(db)
    existing = repo.get_by_year_month(body.year, body.month)
    if existing:
        raise DejemError(f"Já existe um mês DEJEM para {body.month:02d}/{body.year}.")
    row = DejemMonth(
        year=body.year,
        month=body.month,
        total_available_slots=body.total_available_slots,
        monthly_limit_per_officer=body.monthly_limit_per_officer,
        status=DejemMonthStatus.OPEN_INTEREST,
        created_by_id=current.id,
    )
    saved = repo.add(row)
    return _month_to_public(saved, 0)


def update_month(db: Session, month_id: int, body: DejemMonthUpdate) -> DejemMonthPublic:
    repo = DejemMonthRepository(db)
    month = repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    if month.status != DejemMonthStatus.OPEN_INTEREST:
        raise DejemError("Só é possível editar o mês enquanto a manifestação estiver aberta.")
    if body.total_available_slots is not None:
        month.total_available_slots = body.total_available_slots
    if body.monthly_limit_per_officer is not None:
        month.monthly_limit_per_officer = body.monthly_limit_per_officer
    saved = repo.save(month)
    return _month_to_public(saved, repo.count_interested(saved.id))


def close_interest(db: Session, month_id: int) -> DejemMonthPublic:
    repo = DejemMonthRepository(db)
    month = repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    if month.status != DejemMonthStatus.OPEN_INTEREST:
        raise DejemError("A manifestação deste mês já foi encerrada.")
    month.status = DejemMonthStatus.DISTRIBUTED_PENDING
    saved = repo.save(month)
    return _month_to_public(saved, repo.count_interested(saved.id))


# --- Interest (policial) ---


def get_my_interest(db: Session, month_id: int, current: User) -> DejemInterestPublic | None:
    month_repo = DejemMonthRepository(db)
    month = month_repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    row = DejemInterestRepository(db).get_by_month_and_user(month_id, current.id)
    return _interest_to_public(row) if row else None


def create_my_interest(
    db: Session,
    month_id: int,
    current: User,
    body: DejemInterestUpsert,
) -> DejemInterestPublic:
    month_repo = DejemMonthRepository(db)
    month = month_repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    _require_open_interest(month)

    interest_repo = DejemInterestRepository(db)
    existing = interest_repo.get_by_month_and_user(month_id, current.id)
    if existing:
        raise DejemError("Você já possui uma manifestação para este mês. Use a edição.")

    desired = _validate_desired_slots(
        body.interested,
        body.desired_slots,
        month.monthly_limit_per_officer,
    )
    row = DejemInterest(
        month_id=month_id,
        user_id=current.id,
        interested=body.interested,
        desired_slots=desired,
    )
    return _interest_to_public(interest_repo.add(row))


def update_my_interest(
    db: Session,
    month_id: int,
    current: User,
    body: DejemInterestUpsert,
) -> DejemInterestPublic:
    month_repo = DejemMonthRepository(db)
    month = month_repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    _require_open_interest(month)

    interest_repo = DejemInterestRepository(db)
    row = interest_repo.get_by_month_and_user(month_id, current.id)
    if not row:
        raise DejemError("Manifestação não encontrada. Crie uma nova.")

    desired = _validate_desired_slots(
        body.interested,
        body.desired_slots,
        month.monthly_limit_per_officer,
    )
    row.interested = body.interested
    row.desired_slots = desired
    return _interest_to_public(interest_repo.save(row))


def delete_my_interest(db: Session, month_id: int, current: User) -> None:
    month_repo = DejemMonthRepository(db)
    month = month_repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    _require_open_interest(month)

    interest_repo = DejemInterestRepository(db)
    row = interest_repo.get_by_month_and_user(month_id, current.id)
    if not row:
        raise DejemError("Manifestação não encontrada.")
    interest_repo.delete(row)


# --- Interest (admin) ---


def list_month_interests(db: Session, month_id: int) -> list[DejemInterestAdminRow]:
    month_repo = DejemMonthRepository(db)
    month = month_repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    rows = DejemInterestRepository(db).list_by_month_with_users(month_id)
    return [_interest_to_admin_row(r) for r in rows]


# --- Distribution ---


def get_distribution_preview(db: Session, month_id: int) -> DejemDistributionPreview:
    month_repo = DejemMonthRepository(db)
    month = month_repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")

    interests = DejemInterestRepository(db).list_interested_with_users(month_id)
    candidates = _build_candidates(interests)
    result = compute_distribution(
        month.total_available_slots,
        month.monthly_limit_per_officer,
        candidates,
    )
    return DejemDistributionPreview(
        month_id=month.id,
        total_available_slots=month.total_available_slots,
        interested_count=len(candidates),
        monthly_limit_per_officer=month.monthly_limit_per_officer,
        base_quantity=result.base_quantity,
        remaining_after_base=result.remaining_after_base,
    )


def distribute_month(db: Session, month_id: int) -> DejemDistributeResponse:
    month_repo = DejemMonthRepository(db)
    month = month_repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    if month.status != DejemMonthStatus.DISTRIBUTED_PENDING:
        raise DejemError(
            "A distribuição só pode ser executada quando o status for DISTRIBUTED_PENDING."
        )

    alloc_repo = DejemAllocationRepository(db)
    if alloc_repo.count_by_month(month_id) > 0:
        raise DejemError("Já existe distribuição para este mês. Reabra antes de redistribuir.")

    interests = DejemInterestRepository(db).list_interested_with_users(month_id)
    candidates = _build_candidates(interests)
    desired_by_user = {c.user_id: c.desired_slots for c in candidates}

    result = compute_distribution(
        month.total_available_slots,
        month.monthly_limit_per_officer,
        candidates,
    )

    rows = [
        DejemAllocation(
            month_id=month_id,
            user_id=uid,
            allocated_slots=slots,
            used_slots=0,
            remaining_slots=slots,
        )
        for uid, slots in result.allocations.items()
    ]
    if rows:
        alloc_repo.add_many(rows)

    month.status = DejemMonthStatus.DISTRIBUTED
    month = month_repo.save(month)

    saved_with_users = alloc_repo.list_by_month_with_users(month_id)
    preview = DejemDistributionPreview(
        month_id=month.id,
        total_available_slots=month.total_available_slots,
        interested_count=len(candidates),
        monthly_limit_per_officer=month.monthly_limit_per_officer,
        base_quantity=result.base_quantity,
        remaining_after_base=result.remaining_after_base,
    )
    return DejemDistributeResponse(
        month=_month_to_public(month, month_repo.count_interested(month.id)),
        preview=preview,
        leftover_slots=result.leftover_slots,
        allocations=_sorted_admin_allocations(saved_with_users, desired_by_user),
    )


def reopen_distribution(db: Session, month_id: int) -> DejemMonthPublic:
    month_repo = DejemMonthRepository(db)
    month = month_repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    if month.status != DejemMonthStatus.DISTRIBUTED:
        raise DejemError("Só é possível reabrir meses com status DISTRIBUTED.")

    DejemAllocationRepository(db).delete_by_month(month_id)
    month.status = DejemMonthStatus.DISTRIBUTED_PENDING
    saved = month_repo.save(month)
    return _month_to_public(saved, month_repo.count_interested(saved.id))


def list_month_allocations(db: Session, month_id: int) -> list[DejemAllocationAdminRow]:
    month_repo = DejemMonthRepository(db)
    month = month_repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")

    interests = DejemInterestRepository(db).list_interested_with_users(month_id)
    desired_by_user = {r.user_id: r.desired_slots for r in interests}
    rows = DejemAllocationRepository(db).list_by_month_with_users(month_id)
    return _sorted_admin_allocations(rows, desired_by_user)


def get_my_allocation(
    db: Session,
    month_id: int,
    current: User,
) -> DejemAllocationPublic | None:
    month_repo = DejemMonthRepository(db)
    month = month_repo.get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    row = DejemAllocationRepository(db).get_by_month_and_user(month_id, current.id)
    return _allocation_to_public(row) if row else None
