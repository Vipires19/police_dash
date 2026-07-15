"""Testes da integração DEJEM ↔ Mapa Força (fase 4.6)."""

from __future__ import annotations

from datetime import date, time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from models.dejem import DejemShiftStatus, DejemShiftType, ParticipantStatus
from models.user import User  # noqa: F401
from models.compensations import UserCompensation  # noqa: F401 — registry
from models.vehicle import Vehicle  # noqa: F401
from services.dejem_map_service import (
    integrate_closed_shifts_for_scale,
    map_block_title,
    reopen_integrated_shifts_for_scale,
)


def test_map_titles():
    assert map_block_title(DejemShiftType.FT) == "APOIO TÁTICO"
    assert map_block_title(DejemShiftType.ROCAM) == "ROCAM EXTRA"
    assert map_block_title(DejemShiftType.OUTROS) == "DEJEM"


def test_integrate_only_closed_and_ready():
    db = MagicMock()
    actor = SimpleNamespace(id=1)

    closed = SimpleNamespace(
        id=10,
        status=DejemShiftStatus.CLOSED,
        shift_type=DejemShiftType.FT,
        start_time=time(4, 55),
        end_time=time(12, 55),
        service_scale_id=None,
        integrated_at=None,
        integrated_by_id=None,
        participants=[
            SimpleNamespace(
                status=ParticipantStatus.REGISTERED,
                user=SimpleNamespace(
                    id=2, patente="CB", nome_guerra="MORETTO", display_order=1
                ),
            )
        ],
    )
    open_shift = SimpleNamespace(
        id=11,
        status=DejemShiftStatus.OPEN,
        participants=[],
    )

    with (
        patch(
            "services.dejem_map_service.list_shifts_for_date",
            return_value=[closed],
        ),
        patch("services.dejem_map_service.DejemEnrollmentAuditRepository") as AuditRepo,
    ):
        count = integrate_closed_shifts_for_scale(
            db,
            scale_id=99,
            scale_date=date(2026, 7, 14),
            actor=actor,
        )

    assert count == 1
    assert closed.status == DejemShiftStatus.INTEGRATED
    assert closed.service_scale_id == 99
    assert closed.integrated_by_id == 1
    AuditRepo.return_value.add_flush.assert_called_once()
    assert open_shift.status == DejemShiftStatus.OPEN


def test_integrate_skips_empty_participants():
    db = MagicMock()
    actor = SimpleNamespace(id=1)
    empty = SimpleNamespace(
        id=10,
        status=DejemShiftStatus.CLOSED,
        shift_type=DejemShiftType.FT,
        participants=[],
    )
    with (
        patch("services.dejem_map_service.list_shifts_for_date", return_value=[empty]),
        patch("services.dejem_map_service.DejemEnrollmentAuditRepository"),
    ):
        count = integrate_closed_shifts_for_scale(
            db, scale_id=1, scale_date=date(2026, 7, 1), actor=actor
        )
    assert count == 0
    assert empty.status == DejemShiftStatus.CLOSED


def test_reopen_sets_ready_for_map():
    db = MagicMock()
    actor = SimpleNamespace(id=5)
    integrated = SimpleNamespace(
        id=3,
        status=DejemShiftStatus.INTEGRATED,
        service_scale_id=77,
        integrated_at="x",
        integrated_by_id=1,
    )
    db.scalars.return_value.all.return_value = [integrated]

    with patch("services.dejem_map_service.DejemEnrollmentAuditRepository"):
        n = reopen_integrated_shifts_for_scale(db, scale_id=77, actor=actor)

    assert n == 1
    assert integrated.status == DejemShiftStatus.READY_FOR_MAP
    assert integrated.service_scale_id is None
    assert integrated.integrated_at is None
    assert integrated.integrated_by_id is None
