"""Testes do EnrollmentService DEJEM (fase 4.5)."""

from __future__ import annotations

from datetime import date, datetime, time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from models.dejem import (
    DejemMonthStatus,
    DejemShiftStatus,
    DejemShiftType,
    ParticipantStatus,
    ParticipationType,
)
from models.user import User  # noqa: F401 — registry SQLAlchemy
from schemas.dejem import DejemAdminAddParticipant
from services.dejem_enrollment_service import (
    _consumes_balance,
    _shift_window,
    cancel_self,
    close_shift,
    enroll_self,
)
from services.dejem_service import DejemError

_BR = ZoneInfo("America/Sao_Paulo")


def test_consumes_balance_only_normal():
    assert _consumes_balance(ParticipationType.NORMAL) is True
    assert _consumes_balance(ParticipationType.EXTRAORDINARY) is False
    assert _consumes_balance(ParticipationType.SUBSTITUTION) is False


def test_shift_window_overnight():
    start, end = _shift_window(date(2026, 7, 1), time(18, 30), time(2, 30))
    assert end.day == 2
    assert (end - start).total_seconds() == 8 * 3600


def _user(uid: int = 7):
    return SimpleNamespace(id=uid)


def _shift(**kwargs):
    defaults = {
        "id": 1,
        "month_id": 10,
        "date": date(2026, 7, 6),
        "start_time": time(4, 55),
        "end_time": time(12, 55),
        "shift_type": DejemShiftType.FT,
        "capacity": 4,
        "status": DejemShiftStatus.OPEN,
        "closed_at": None,
        "closed_by_id": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _month(**kwargs):
    defaults = {
        "id": 10,
        "status": DejemMonthStatus.OPEN_SHIFTS,
        "year": 2026,
        "month": 7,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _alloc(remaining=3, used=2, allocated=5):
    return SimpleNamespace(
        remaining_slots=remaining,
        used_slots=used,
        allocated_slots=allocated,
    )


def test_enroll_self_happy_path():
    db = MagicMock()
    current = _user()
    shift = _shift()
    month = _month()
    alloc = _alloc()

    with (
        patch("services.dejem_enrollment_service.DejemShiftRepository") as ShiftRepo,
        patch("services.dejem_enrollment_service.DejemParticipantRepository") as PartRepo,
        patch("services.dejem_enrollment_service.DejemAllocationRepository") as AllocRepo,
        patch("services.dejem_enrollment_service.DejemMonthRepository") as MonthRepo,
        patch("services.dejem_enrollment_service.DejemEnrollmentAuditRepository") as AuditRepo,
        patch("services.dejem_enrollment_service._assert_no_operational_overlap"),
    ):
        ShiftRepo.return_value.get_by_id.return_value = shift
        ShiftRepo.return_value.count_filled.return_value = 1
        MonthRepo.return_value.get_by_id.return_value = month
        PartRepo.return_value.get_by_shift_and_user.return_value = None
        PartRepo.return_value.list_active_for_user_on_dates.return_value = []
        AllocRepo.return_value.get_by_month_and_user.return_value = alloc
        created = SimpleNamespace(
            id=99,
            shift_id=1,
            user_id=7,
            participation_type=ParticipationType.NORMAL,
            status=ParticipantStatus.REGISTERED,
            consumes_balance=True,
            created_at=datetime.now(tz=_BR),
        )
        PartRepo.return_value.add_flush.return_value = created

        result = enroll_self(db, current, 1)

        assert result.participant_id == 99
        assert result.remaining_slots == 2  # 3-1
        assert alloc.used_slots == 3
        PartRepo.return_value.commit.assert_called_once()
        AuditRepo.return_value.add_flush.assert_called_once()


def test_enroll_rejects_when_full():
    db = MagicMock()
    with (
        patch("services.dejem_enrollment_service.DejemShiftRepository") as ShiftRepo,
        patch("services.dejem_enrollment_service.DejemParticipantRepository"),
        patch("services.dejem_enrollment_service.DejemAllocationRepository"),
        patch("services.dejem_enrollment_service.DejemMonthRepository") as MonthRepo,
    ):
        ShiftRepo.return_value.get_by_id.return_value = _shift(capacity=2)
        ShiftRepo.return_value.count_filled.return_value = 2
        MonthRepo.return_value.get_by_id.return_value = _month()

        with pytest.raises(DejemError, match="lotada"):
            enroll_self(db, _user(), 1)


def test_cancel_returns_balance():
    db = MagicMock()
    shift = _shift()
    alloc = _alloc(remaining=2, used=3, allocated=5)
    row = SimpleNamespace(
        id=5,
        shift_id=1,
        user_id=7,
        status=ParticipantStatus.REGISTERED,
        consumes_balance=True,
        participation_type=ParticipationType.NORMAL,
        created_at=datetime.now(tz=_BR),
        cancelled_at=None,
        cancelled_by_id=None,
    )

    with (
        patch("services.dejem_enrollment_service.DejemShiftRepository") as ShiftRepo,
        patch("services.dejem_enrollment_service.DejemParticipantRepository") as PartRepo,
        patch("services.dejem_enrollment_service.DejemAllocationRepository") as AllocRepo,
        patch("services.dejem_enrollment_service.DejemEnrollmentAuditRepository"),
    ):
        ShiftRepo.return_value.get_by_id.return_value = shift
        PartRepo.return_value.get_by_shift_and_user.return_value = row
        AllocRepo.return_value.get_by_month_and_user.return_value = alloc

        result = cancel_self(db, _user(), 1)

        assert row.status == ParticipantStatus.CANCELLED
        assert alloc.remaining_slots == 3
        assert result.remaining_slots == 3


def test_close_requires_participant():
    db = MagicMock()
    with patch("services.dejem_enrollment_service.DejemShiftRepository") as ShiftRepo:
        ShiftRepo.return_value.get_by_id.return_value = _shift()
        ShiftRepo.return_value.count_filled.return_value = 0
        with pytest.raises(DejemError, match="ao menos um participante"):
            close_shift(db, _user(), 1)


def test_admin_add_payload_default_normal():
    body = DejemAdminAddParticipant(user_id=3)
    assert body.participation_type.value == "NORMAL"
