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
