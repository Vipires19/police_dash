"""Testes de vinculação de viatura em Escala DEJEM."""

from __future__ import annotations

from datetime import datetime, time, timezone
from types import SimpleNamespace

import pytest

from models.dejem import DejemShiftStatus, DejemShiftType
from models.vehicle import VehicleStatus
from services.dejem_map_service import map_block_title
from services.dejem_shift_service import _resolve_vehicle_id, _shift_to_public


def test_shift_to_public_includes_vehicle_prefixo():
    now = datetime.now(tz=timezone.utc)
    row = SimpleNamespace(
        id=1,
        month_id=2,
        date="2026-07-15",
        start_time=time(4, 55),
        end_time=time(12, 55),
        shift_type=DejemShiftType.FT,
        capacity=4,
        status=DejemShiftStatus.OPEN,
        vehicle_id=10,
        vehicle=SimpleNamespace(prefixo="I-03024"),
        created_by_id=1,
        created_at=now,
        updated_at=now,
    )
    pub = _shift_to_public(row, filled=2)  # type: ignore[arg-type]
    assert pub.vehicle_id == 10
    assert pub.vehicle_prefixo == "I-03024"
    assert pub.filled_slots == 2
    assert pub.available_slots == 2


def test_resolve_vehicle_rejects_baixada():
    vehicle = SimpleNamespace(id=1, prefixo="I-1", status=VehicleStatus.BAIXADA)
    db = SimpleNamespace(get=lambda *_a, **_k: vehicle)
    with pytest.raises(Exception) as exc:
        _resolve_vehicle_id(db, 1)  # type: ignore[arg-type]
    assert "não está ativa" in str(exc.value)


def test_resolve_vehicle_allows_operando():
    vehicle = SimpleNamespace(id=3, prefixo="I-03024", status=VehicleStatus.OPERANDO)
    db = SimpleNamespace(get=lambda *_a, **_k: vehicle)
    assert _resolve_vehicle_id(db, 3) == 3  # type: ignore[arg-type]


def test_resolve_vehicle_none_ok():
    db = SimpleNamespace(get=lambda *_a, **_k: None)
    assert _resolve_vehicle_id(db, None) is None  # type: ignore[arg-type]


def test_map_block_title_ft():
    assert map_block_title(DejemShiftType.FT) == "APOIO TÁTICO"


def test_assert_unique_timeslot_message():
    from datetime import date

    from services.dejem_service import DejemError
    from services.dejem_shift_service import _assert_unique_timeslot

    existing = SimpleNamespace(id=9, start_time=time(4, 55), end_time=time(12, 55))
    repo = SimpleNamespace(
        find_by_date_and_times=lambda *_a, **_k: existing,
    )
    with pytest.raises(DejemError) as exc:
        _assert_unique_timeslot(
            repo,  # type: ignore[arg-type]
            month_id=1,
            day=date(2026, 7, 16),
            start_time=time(4, 55),
            end_time=time(12, 55),
        )
    assert "mesmo horário" in str(exc.value)


def test_dejem_block_vehicle_reaches_message():
    from services.message_generation_service import build_equipes_from_snapshot
    from services.scale_publish_pipeline import _normalize_dejem_block

    raw = {
        "shift_id": 1,
        "title": "APOIO TÁTICO",
        "shift_type": "FT",
        "vehicle_id": 10,
        "vehicle_prefixo": "I-03024",
        "start_time": "04:55:00",
        "end_time": "12:55:00",
        "members": [{"patente": "CB", "nome_guerra": "X", "display_order": 0}],
    }
    block = _normalize_dejem_block(raw)
    assert block["vehicle_prefixo"] == "I-03024"
    assert block["start_time"] == "04:55"
    text = build_equipes_from_snapshot({"teams": [], "dejem_blocks": [block]})
    assert "*🚔 FORÇA TÁTICA DEJEM*" in text
    assert "*I-03024*" in text
    assert "*🕘 QTR* Das 04:55 às 12:55" in text
