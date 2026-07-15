"""Serviço de escalas e templates DEJEM (fase 4.4)."""

from __future__ import annotations

import calendar
from datetime import date, time

from sqlalchemy.orm import Session

from models.dejem import (
    DejemMonth,
    DejemMonthStatus,
    DejemShift,
    DejemShiftStatus,
    DejemShiftTemplate,
    DejemShiftType,
)
from models.user import User
from repositories.dejem_repository import (
    DejemAllocationRepository,
    DejemMonthRepository,
    DejemShiftRepository,
    DejemShiftTemplateRepository,
)
from schemas.dejem import (
    DejemShiftCalendarDay,
    DejemShiftCalendarResponse,
    DejemShiftCreate,
    DejemShiftDashboard,
    DejemShiftDayDetail,
    DejemShiftPublic,
    DejemShiftTemplateCreate,
    DejemShiftTemplatePublic,
    DejemShiftTemplateUpdate,
    DejemShiftUpdate,
)
from services.dejem_service import DejemError


def _time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _interval_bounds(start: time, end: time) -> tuple[int, int]:
    """Retorna [start, end) em minutos; se overnight, end += 24h."""
    s = _time_to_minutes(start)
    e = _time_to_minutes(end)
    if e <= s:
        e += 24 * 60
    return s, e


def _intervals_overlap(a_start: time, a_end: time, b_start: time, b_end: time) -> bool:
    a0, a1 = _interval_bounds(a_start, a_end)
    b0, b1 = _interval_bounds(b_start, b_end)
    return a0 < b1 and b0 < a1


def _shift_to_public(row: DejemShift, filled: int) -> DejemShiftPublic:
    return DejemShiftPublic(
        id=row.id,
        month_id=row.month_id,
        date=row.date,
        start_time=row.start_time,
        end_time=row.end_time,
        shift_type=row.shift_type,  # type: ignore[arg-type]
        capacity=row.capacity,
        filled_slots=filled,
        available_slots=max(0, row.capacity - filled),
        status=row.status,  # type: ignore[arg-type]
        created_by_id=row.created_by_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _template_to_public(row: DejemShiftTemplate) -> DejemShiftTemplatePublic:
    return DejemShiftTemplatePublic.model_validate(row)


def _ensure_month_allows_shifts(month: DejemMonth) -> None:
    allowed = {
        DejemMonthStatus.DISTRIBUTED,
        DejemMonthStatus.OPEN_SHIFTS,
        DejemMonthStatus.FINISHED,
    }
    if month.status not in allowed:
        raise DejemError(
            "Só é possível gerenciar escalas após a distribuição das vagas (status DISTRIBUTED)."
        )


def _validate_capacity(capacity: int) -> None:
    if capacity < 0:
        raise DejemError("A capacidade não pode ser negativa.")


def _assert_no_overlap(
    repo: DejemShiftRepository,
    *,
    month_id: int,
    day: date,
    shift_type: DejemShiftType,
    start_time: time,
    end_time: time,
    exclude_id: int | None = None,
) -> None:
    others = repo.list_same_type_on_date(month_id, day, shift_type, exclude_id=exclude_id)
    for other in others:
        if _intervals_overlap(start_time, end_time, other.start_time, other.end_time):
            raise DejemError(
                f"Horário sobreposto com outra escala {shift_type.value} no mesmo dia "
                f"({other.start_time.strftime('%H:%M')}–{other.end_time.strftime('%H:%M')})."
            )


# --- Shifts CRUD ---


def create_shift(db: Session, current: User, body: DejemShiftCreate) -> DejemShiftPublic:
    month_repo = DejemMonthRepository(db)
    month = month_repo.get_by_id(body.month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    _ensure_month_allows_shifts(month)
    if month.status == DejemMonthStatus.FINISHED:
        raise DejemError("Não é possível criar escalas em um mês finalizado.")
    if body.date.year != month.year or body.date.month != month.month:
        raise DejemError("A data da escala deve pertencer ao mês DEJEM selecionado.")
    _validate_capacity(body.capacity)

    shift_type = DejemShiftType(body.shift_type.value)
    shift_repo = DejemShiftRepository(db)
    _assert_no_overlap(
        shift_repo,
        month_id=month.id,
        day=body.date,
        shift_type=shift_type,
        start_time=body.start_time,
        end_time=body.end_time,
    )

    row = DejemShift(
        month_id=month.id,
        date=body.date,
        start_time=body.start_time,
        end_time=body.end_time,
        shift_type=shift_type,
        capacity=body.capacity,
        status=DejemShiftStatus(body.status.value),
        created_by_id=current.id,
    )
    saved = shift_repo.add(row)

    if month.status == DejemMonthStatus.DISTRIBUTED:
        month.status = DejemMonthStatus.OPEN_SHIFTS
        month_repo.save(month)

    return _shift_to_public(saved, 0)


def update_shift(db: Session, shift_id: int, body: DejemShiftUpdate) -> DejemShiftPublic:
    shift_repo = DejemShiftRepository(db)
    row = shift_repo.get_by_id(shift_id)
    if not row:
        raise DejemError("Escala DEJEM não encontrada.")
    if row.status != DejemShiftStatus.OPEN:
        raise DejemError("Somente escalas OPEN podem ser editadas.")

    month = DejemMonthRepository(db).get_by_id(row.month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    if month.status == DejemMonthStatus.FINISHED:
        raise DejemError("Não é possível editar escalas de um mês finalizado.")

    new_date = body.date if body.date is not None else row.date
    new_start = body.start_time if body.start_time is not None else row.start_time
    new_end = body.end_time if body.end_time is not None else row.end_time
    new_type = DejemShiftType(body.shift_type.value) if body.shift_type is not None else row.shift_type
    new_capacity = body.capacity if body.capacity is not None else row.capacity
    new_status = DejemShiftStatus(body.status.value) if body.status is not None else row.status

    if new_date.year != month.year or new_date.month != month.month:
        raise DejemError("A data da escala deve pertencer ao mês DEJEM selecionado.")
    _validate_capacity(new_capacity)

    filled = shift_repo.count_filled(row.id)
    if new_capacity < filled:
        raise DejemError(
            f"A capacidade não pode ser menor que as vagas já preenchidas ({filled})."
        )

    _assert_no_overlap(
        shift_repo,
        month_id=row.month_id,
        day=new_date,
        shift_type=new_type,
        start_time=new_start,
        end_time=new_end,
        exclude_id=row.id,
    )

    row.date = new_date
    row.start_time = new_start
    row.end_time = new_end
    row.shift_type = new_type
    row.capacity = new_capacity
    row.status = new_status
    saved = shift_repo.save(row)
    return _shift_to_public(saved, filled)


def delete_shift(db: Session, shift_id: int) -> None:
    shift_repo = DejemShiftRepository(db)
    row = shift_repo.get_by_id(shift_id)
    if not row:
        raise DejemError("Escala DEJEM não encontrada.")
    if row.status != DejemShiftStatus.OPEN:
        raise DejemError("Não é permitido excluir escalas fechadas ou finalizadas.")
    filled = shift_repo.count_filled(row.id)
    if filled > 0:
        raise DejemError("Não é possível excluir uma escala com participantes.")
    shift_repo.delete(row)


def get_shift(db: Session, shift_id: int) -> DejemShiftPublic:
    shift_repo = DejemShiftRepository(db)
    row = shift_repo.get_by_id(shift_id)
    if not row:
        raise DejemError("Escala DEJEM não encontrada.")
    return _shift_to_public(row, shift_repo.count_filled(row.id))


def list_month_shifts(db: Session, month_id: int) -> list[DejemShiftPublic]:
    month = DejemMonthRepository(db).get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    shift_repo = DejemShiftRepository(db)
    rows = shift_repo.list_by_month(month_id)
    return [_shift_to_public(r, shift_repo.count_filled(r.id)) for r in rows]


def build_shift_calendar(db: Session, year: int, month: int) -> DejemShiftCalendarResponse:
    month_row = DejemMonthRepository(db).get_by_year_month(year, month)
    days_count = calendar.monthrange(year, month)[1]
    by_date: dict[date, list[DejemShift]] = {}
    if month_row:
        for s in DejemShiftRepository(db).list_by_month(month_row.id):
            by_date.setdefault(s.date, []).append(s)

    shift_repo = DejemShiftRepository(db)
    days: list[DejemShiftCalendarDay] = []
    for n in range(1, days_count + 1):
        d = date(year, month, n)
        shifts = by_date.get(d, [])
        total_cap = sum(s.capacity for s in shifts)
        total_filled = sum(shift_repo.count_filled(s.id) for s in shifts) if shifts else 0
        days.append(
            DejemShiftCalendarDay(
                date=d,
                shift_count=len(shifts),
                total_capacity=total_cap,
                total_filled=total_filled,
                has_open=any(s.status == DejemShiftStatus.OPEN for s in shifts),
                has_closed=any(
                    s.status
                    in {
                        DejemShiftStatus.CLOSED,
                        DejemShiftStatus.READY_FOR_MAP,
                        DejemShiftStatus.INTEGRATED,
                    }
                    for s in shifts
                ),
                has_finished=any(s.status == DejemShiftStatus.FINISHED for s in shifts),
            )
        )
    return DejemShiftCalendarResponse(
        year=year,
        month=month,
        month_id=month_row.id if month_row else None,
        days=days,
    )


def get_day_detail(db: Session, year: int, month: int, day: int) -> DejemShiftDayDetail:
    d = date(year, month, day)
    month_row = DejemMonthRepository(db).get_by_year_month(year, month)
    if not month_row:
        return DejemShiftDayDetail(date=d, month_id=None, shifts=[])
    shift_repo = DejemShiftRepository(db)
    rows = shift_repo.list_by_month_and_date(month_row.id, d)
    return DejemShiftDayDetail(
        date=d,
        month_id=month_row.id,
        shifts=[_shift_to_public(r, shift_repo.count_filled(r.id)) for r in rows],
    )


def get_shift_dashboard(db: Session, month_id: int) -> DejemShiftDashboard:
    month = DejemMonthRepository(db).get_by_id(month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    shift_repo = DejemShiftRepository(db)
    rows = shift_repo.list_by_month(month_id)
    total_filled = sum(shift_repo.count_filled(r.id) for r in rows)
    total_capacity = sum(r.capacity for r in rows)
    avg_remaining = DejemAllocationRepository(db).average_remaining(month_id)
    return DejemShiftDashboard(
        month_id=month.id,
        year=month.year,
        month=month.month,
        total_shifts=len(rows),
        open_shifts=sum(1 for r in rows if r.status == DejemShiftStatus.OPEN),
        closed_shifts=sum(
            1
            for r in rows
            if r.status
            in {
                DejemShiftStatus.CLOSED,
                DejemShiftStatus.READY_FOR_MAP,
            }
        ),
        finished_shifts=sum(1 for r in rows if r.status == DejemShiftStatus.FINISHED),
        integrated_shifts=sum(1 for r in rows if r.status == DejemShiftStatus.INTEGRATED),
        total_capacity=total_capacity,
        total_filled=total_filled,
        total_available=max(0, total_capacity - total_filled),
        avg_remaining_slots=round(avg_remaining, 2),
    )


# --- Templates ---


def list_templates(db: Session, *, active_only: bool = False) -> list[DejemShiftTemplatePublic]:
    rows = DejemShiftTemplateRepository(db).list_all(active_only=active_only)
    return [_template_to_public(r) for r in rows]


def create_template(
    db: Session,
    current: User,
    body: DejemShiftTemplateCreate,
) -> DejemShiftTemplatePublic:
    _validate_capacity(body.default_capacity)
    row = DejemShiftTemplate(
        name=body.name.strip(),
        shift_type=DejemShiftType(body.shift_type.value),
        start_time=body.start_time,
        end_time=body.end_time,
        default_capacity=body.default_capacity,
        is_active=body.is_active,
        created_by_id=current.id,
    )
    if not row.name:
        raise DejemError("O nome do template é obrigatório.")
    saved = DejemShiftTemplateRepository(db).add(row)
    return _template_to_public(saved)


def update_template(
    db: Session,
    template_id: int,
    body: DejemShiftTemplateUpdate,
) -> DejemShiftTemplatePublic:
    repo = DejemShiftTemplateRepository(db)
    row = repo.get_by_id(template_id)
    if not row:
        raise DejemError("Template não encontrado.")
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise DejemError("O nome do template é obrigatório.")
        row.name = name
    if body.shift_type is not None:
        row.shift_type = DejemShiftType(body.shift_type.value)
    if body.start_time is not None:
        row.start_time = body.start_time
    if body.end_time is not None:
        row.end_time = body.end_time
    if body.default_capacity is not None:
        _validate_capacity(body.default_capacity)
        row.default_capacity = body.default_capacity
    if body.is_active is not None:
        row.is_active = body.is_active
    return _template_to_public(repo.save(row))


def delete_template(db: Session, template_id: int) -> None:
    repo = DejemShiftTemplateRepository(db)
    row = repo.get_by_id(template_id)
    if not row:
        raise DejemError("Template não encontrado.")
    repo.delete(row)
