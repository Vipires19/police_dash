"""Geração automática e pré-visualização de escalas DEJEM (fases 4.4.1 / 4.4.2).

Preview e geração usam o mesmo algoritmo de planejamento.
A prévia NUNCA persiste dados.
"""

from __future__ import annotations

import calendar
import time as time_mod
from dataclasses import dataclass
from datetime import date, time
from typing import Literal

from sqlalchemy.orm import Session

from models.dejem import (
    DejemMonth,
    DejemMonthStatus,
    DejemShift,
    DejemShiftStatus,
    DejemShiftTemplate,
)
from models.user import User
from repositories.dejem_repository import (
    DejemMonthRepository,
    DejemShiftRepository,
    DejemShiftTemplateRepository,
)
from schemas.dejem import (
    DejemMonthGeneratePreview,
    DejemMonthGeneratePreviewItem,
    DejemMonthGenerateRequest,
    DejemMonthGenerateResult,
)
from services.dejem_service import DejemError

PlanAction = Literal["CREATE", "IGNORE", "REPLACE"]

WEEKDAY_LABELS = {
    0: "Segunda",
    1: "Terça",
    2: "Quarta",
    3: "Quinta",
    4: "Sexta",
    5: "Sábado",
    6: "Domingo",
}


@dataclass(frozen=True)
class PlannedShift:
    date: date
    start_time: time
    end_time: time
    shift_type: str
    capacity: int
    template_id: int
    template_name: str
    action: PlanAction
    existing_shift_id: int | None = None


def _prepare_context(
    db: Session,
    body: DejemMonthGenerateRequest,
) -> tuple[DejemMonth, list[DejemShiftTemplate], list[int]]:
    weekdays = sorted(set(body.weekdays))
    if any(d < 0 or d > 6 for d in weekdays):
        raise DejemError("Dias da semana inválidos (use 0=segunda … 6=domingo).")
    if not weekdays:
        raise DejemError("Selecione ao menos um dia da semana.")

    template_ids = list(dict.fromkeys(body.template_ids))
    if not template_ids:
        raise DejemError("Selecione ao menos um template.")

    month = DejemMonthRepository(db).get_by_year_month(body.year, body.month)
    if not month:
        raise DejemError(
            f"Não existe mês DEJEM cadastrado para {body.month:02d}/{body.year}."
        )
    if month.status not in {
        DejemMonthStatus.DISTRIBUTED,
        DejemMonthStatus.OPEN_SHIFTS,
    }:
        raise DejemError(
            "A geração automática só é permitida após a distribuição "
            "(status DISTRIBUTED ou OPEN_SHIFTS)."
        )

    templates = DejemShiftTemplateRepository(db).list_by_ids(template_ids)
    found_ids = {t.id for t in templates}
    missing = [i for i in template_ids if i not in found_ids]
    if missing:
        raise DejemError(f"Templates não encontrados: {missing}.")

    by_id = {t.id: t for t in templates}
    ordered = [by_id[i] for i in template_ids]
    inactive = [t.name for t in ordered if not t.is_active]
    if inactive:
        raise DejemError(
            "Não é possível usar templates inativos: " + ", ".join(inactive)
        )

    # ignore_holidays reservado — ainda sem calendário de feriados.
    return month, ordered, weekdays


def build_generation_plan(
    db: Session,
    body: DejemMonthGenerateRequest,
) -> tuple[DejemMonth, list[DejemShiftTemplate], list[int], list[PlannedShift]]:
    """Algoritmo único compartilhado por preview e geração. Não persiste."""
    month, ordered_templates, weekdays = _prepare_context(db, body)
    shift_repo = DejemShiftRepository(db)
    plan: list[PlannedShift] = []

    days_in_month = calendar.monthrange(body.year, body.month)[1]
    for day_n in range(1, days_in_month + 1):
        day = date(body.year, body.month, day_n)
        if day.weekday() not in weekdays:
            continue

        for tmpl in ordered_templates:
            existing = shift_repo.find_exact(
                month.id,
                day,
                tmpl.shift_type,
                tmpl.start_time,
                tmpl.end_time,
            )

            action: PlanAction = "CREATE"
            existing_id: int | None = None

            if existing is not None:
                existing_id = existing.id
                filled = shift_repo.count_filled(existing.id)
                if filled > 0 or not body.replace_existing:
                    action = "IGNORE"
                else:
                    action = "REPLACE"

            plan.append(
                PlannedShift(
                    date=day,
                    start_time=tmpl.start_time,
                    end_time=tmpl.end_time,
                    shift_type=tmpl.shift_type.value
                    if hasattr(tmpl.shift_type, "value")
                    else str(tmpl.shift_type),
                    capacity=tmpl.default_capacity,
                    template_id=tmpl.id,
                    template_name=tmpl.name,
                    action=action,
                    existing_shift_id=existing_id,
                )
            )

    return month, ordered_templates, weekdays, plan


def _status_label(action: PlanAction, replace_existing: bool) -> str:
    if action == "CREATE":
        return "Será criada"
    if action == "REPLACE":
        return "Será substituída"
    if replace_existing:
        # ignored despite replace (ex.: tem participantes)
        return "Já existe — será ignorada"
    return "Já existe — será ignorada"


def preview_month_shifts(
    db: Session,
    body: DejemMonthGenerateRequest,
) -> DejemMonthGeneratePreview:
    """Simula a geração sem alterar o banco."""
    started = time_mod.perf_counter()
    month, ordered_templates, weekdays, plan = build_generation_plan(db, body)

    to_create = [p for p in plan if p.action == "CREATE"]
    to_replace = [p for p in plan if p.action == "REPLACE"]
    to_ignore = [p for p in plan if p.action == "IGNORE"]

    selected_days = calendar.monthrange(body.year, body.month)[1]
    matching_days = sum(
        1
        for d in range(1, selected_days + 1)
        if date(body.year, body.month, d).weekday() in weekdays
    )

    items = [
        DejemMonthGeneratePreviewItem(
            date=p.date,
            start_time=p.start_time,
            end_time=p.end_time,
            shift_type=p.shift_type,  # type: ignore[arg-type]
            capacity=p.capacity,
            template_id=p.template_id,
            template_name=p.template_name,
            action=p.action,
            status_label=_status_label(p.action, body.replace_existing),
            existing_shift_id=p.existing_shift_id,
        )
        for p in plan
    ]

    elapsed_ms = int((time_mod.perf_counter() - started) * 1000)
    return DejemMonthGeneratePreview(
        year=body.year,
        month=body.month,
        month_id=month.id,
        days_in_month=selected_days,
        selected_days_count=matching_days,
        weekdays=weekdays,
        weekday_labels=[WEEKDAY_LABELS[d] for d in weekdays],
        template_names=[t.name for t in ordered_templates],
        replace_existing=body.replace_existing,
        planned_shifts=len(plan),
        planned_capacity=sum(p.capacity for p in plan if p.action in {"CREATE", "REPLACE"}),
        create_count=len(to_create),
        ignore_count=len(to_ignore),
        replace_count=len(to_replace),
        create_capacity=sum(p.capacity for p in to_create),
        replace_capacity=sum(p.capacity for p in to_replace),
        existing_conflicts=len(to_ignore) + len(to_replace),
        items=items,
        elapsed_ms=elapsed_ms,
    )


def generate_month_shifts(
    db: Session,
    current: User,
    body: DejemMonthGenerateRequest,
) -> DejemMonthGenerateResult:
    """Persiste o plano calculado pelo mesmo algoritmo do preview."""
    started = time_mod.perf_counter()
    month, _templates, _weekdays, plan = build_generation_plan(db, body)
    shift_repo = DejemShiftRepository(db)

    from models.dejem import DejemShiftType

    created = 0
    ignored = 0
    replaced = 0

    for item in plan:
        if item.action == "IGNORE":
            ignored += 1
            continue

        is_replace = item.action == "REPLACE"
        if is_replace and item.existing_shift_id is not None:
            existing = shift_repo.get_by_id(item.existing_shift_id)
            if existing is not None:
                # Revalida participantes no momento da escrita.
                if shift_repo.count_filled(existing.id) > 0:
                    ignored += 1
                    continue
                shift_repo.delete_flush(existing)
            else:
                # Sumiu entre preview e confirmação — trata como criação.
                is_replace = False

        row = DejemShift(
            month_id=month.id,
            date=item.date,
            start_time=item.start_time,
            end_time=item.end_time,
            shift_type=DejemShiftType(item.shift_type),
            capacity=item.capacity,
            status=DejemShiftStatus.OPEN,
            created_by_id=current.id,
        )
        shift_repo.add_flush(row)
        if is_replace:
            replaced += 1
        else:
            created += 1

    if month.status == DejemMonthStatus.DISTRIBUTED and created > 0:
        month.status = DejemMonthStatus.OPEN_SHIFTS
        db.add(month)

    shift_repo.commit()

    elapsed_ms = int((time_mod.perf_counter() - started) * 1000)
    return DejemMonthGenerateResult(
        year=body.year,
        month=body.month,
        month_id=month.id,
        created=created,
        ignored=ignored,
        replaced=replaced,
        elapsed_ms=elapsed_ms,
    )
