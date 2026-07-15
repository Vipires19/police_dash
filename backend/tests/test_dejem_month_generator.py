"""Testes do plano de geração DEJEM (preview e generate compartilham o algoritmo)."""

from __future__ import annotations

from datetime import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from models.dejem import DejemMonthStatus, DejemShiftType
from schemas.dejem import DejemMonthGenerateRequest
from services.dejem_month_generator_service import (
    build_generation_plan,
    preview_month_shifts,
)


def _month(**kwargs):
    defaults = {
        "id": 1,
        "year": 2026,
        "month": 7,
        "status": DejemMonthStatus.DISTRIBUTED,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _tmpl(id_: int, name: str, shift_type=DejemShiftType.FT, capacity=4):
    return SimpleNamespace(
        id=id_,
        name=name,
        shift_type=shift_type,
        start_time=time(4, 55),
        end_time=time(12, 55),
        default_capacity=capacity,
        is_active=True,
    )


@pytest.fixture
def body() -> DejemMonthGenerateRequest:
    return DejemMonthGenerateRequest(
        year=2026,
        month=7,
        weekdays=[0],  # apenas segundas
        template_ids=[10],
        replace_existing=False,
    )


def test_preview_never_calls_commit_or_flush(body: DejemMonthGenerateRequest):
    db = MagicMock()
    month = _month()
    tmpl = _tmpl(10, "FT Manhã")

    with (
        patch(
            "services.dejem_month_generator_service.DejemMonthRepository"
        ) as MonthRepo,
        patch(
            "services.dejem_month_generator_service.DejemShiftTemplateRepository"
        ) as TmplRepo,
        patch(
            "services.dejem_month_generator_service.DejemShiftRepository"
        ) as ShiftRepo,
    ):
        MonthRepo.return_value.get_by_year_month.return_value = month
        TmplRepo.return_value.list_by_ids.return_value = [tmpl]
        shift_repo = ShiftRepo.return_value
        shift_repo.find_exact.return_value = None
        shift_repo.count_filled.return_value = 0

        preview = preview_month_shifts(db, body)

        shift_repo.add_flush.assert_not_called()
        shift_repo.delete_flush.assert_not_called()
        shift_repo.commit.assert_not_called()
        db.commit.assert_not_called()
        db.flush.assert_not_called()

    # Jul/2026: segundas = 6, 13, 20, 27 → 4 dias × 1 template
    assert preview.create_count == 4
    assert preview.ignore_count == 0
    assert preview.replace_count == 0
    assert preview.planned_capacity == 16
    assert len(preview.items) == 4
    assert all(i.action == "CREATE" for i in preview.items)


def test_plan_marks_existing_as_ignore_when_not_replacing(
    body: DejemMonthGenerateRequest,
):
    db = MagicMock()
    month = _month()
    tmpl = _tmpl(10, "FT Manhã")
    existing = SimpleNamespace(id=99)

    with (
        patch(
            "services.dejem_month_generator_service.DejemMonthRepository"
        ) as MonthRepo,
        patch(
            "services.dejem_month_generator_service.DejemShiftTemplateRepository"
        ) as TmplRepo,
        patch(
            "services.dejem_month_generator_service.DejemShiftRepository"
        ) as ShiftRepo,
    ):
        MonthRepo.return_value.get_by_year_month.return_value = month
        TmplRepo.return_value.list_by_ids.return_value = [tmpl]
        shift_repo = ShiftRepo.return_value
        shift_repo.find_exact.return_value = existing
        shift_repo.count_filled.return_value = 0

        _m, _t, _w, plan = build_generation_plan(db, body)

    assert all(p.action == "IGNORE" for p in plan)
    assert all(p.existing_shift_id == 99 for p in plan)


def test_plan_marks_replace_when_empty_and_flag_on():
    body = DejemMonthGenerateRequest(
        year=2026,
        month=7,
        weekdays=[0],
        template_ids=[10],
        replace_existing=True,
    )
    db = MagicMock()
    month = _month()
    tmpl = _tmpl(10, "FT Manhã")
    existing = SimpleNamespace(id=99)

    with (
        patch(
            "services.dejem_month_generator_service.DejemMonthRepository"
        ) as MonthRepo,
        patch(
            "services.dejem_month_generator_service.DejemShiftTemplateRepository"
        ) as TmplRepo,
        patch(
            "services.dejem_month_generator_service.DejemShiftRepository"
        ) as ShiftRepo,
    ):
        MonthRepo.return_value.get_by_year_month.return_value = month
        TmplRepo.return_value.list_by_ids.return_value = [tmpl]
        shift_repo = ShiftRepo.return_value
        shift_repo.find_exact.return_value = existing
        shift_repo.count_filled.return_value = 0

        preview = preview_month_shifts(db, body)

    assert preview.replace_count == 4
    assert preview.create_count == 0
    assert preview.ignore_count == 0
    assert all(i.action == "REPLACE" for i in preview.items)


def test_plan_always_ignores_when_has_participants():
    body = DejemMonthGenerateRequest(
        year=2026,
        month=7,
        weekdays=[0],
        template_ids=[10],
        replace_existing=True,
    )
    db = MagicMock()
    month = _month()
    tmpl = _tmpl(10, "FT Manhã")
    existing = SimpleNamespace(id=99)

    with (
        patch(
            "services.dejem_month_generator_service.DejemMonthRepository"
        ) as MonthRepo,
        patch(
            "services.dejem_month_generator_service.DejemShiftTemplateRepository"
        ) as TmplRepo,
        patch(
            "services.dejem_month_generator_service.DejemShiftRepository"
        ) as ShiftRepo,
    ):
        MonthRepo.return_value.get_by_year_month.return_value = month
        TmplRepo.return_value.list_by_ids.return_value = [tmpl]
        shift_repo = ShiftRepo.return_value
        shift_repo.find_exact.return_value = existing
        shift_repo.count_filled.return_value = 2

        preview = preview_month_shifts(db, body)

    assert preview.ignore_count == 4
    assert preview.replace_count == 0
