"""Testes de sobreposição de intervalos (turnos overnight inclusos)."""

from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from core.time_intervals import (
    combine_shift_window,
    intervals_overlap,
    overlap_interval,
)

_BR = ZoneInfo("America/Sao_Paulo")
_DAY = date(2026, 8, 19)


def test_intervals_overlap_partial():
    a0 = datetime(2026, 8, 19, 8, 0, tzinfo=_BR)
    a1 = datetime(2026, 8, 19, 12, 0, tzinfo=_BR)
    b0 = datetime(2026, 8, 19, 10, 0, tzinfo=_BR)
    b1 = datetime(2026, 8, 19, 14, 0, tzinfo=_BR)
    assert intervals_overlap(a0, a1, b0, b1)
    ov = overlap_interval(a0, a1, b0, b1)
    assert ov == (b0, a1)


def test_intervals_no_overlap_adjacent():
    a0 = datetime(2026, 8, 19, 8, 0, tzinfo=_BR)
    a1 = datetime(2026, 8, 19, 12, 0, tzinfo=_BR)
    b0 = datetime(2026, 8, 19, 12, 0, tzinfo=_BR)
    b1 = datetime(2026, 8, 19, 16, 0, tzinfo=_BR)
    assert not intervals_overlap(a0, a1, b0, b1)
    assert overlap_interval(a0, a1, b0, b1) is None


def test_intervals_same_person_different_shifts_no_overlap():
    """Mesmo policial em DEJEM manhã e Escala Operacional tarde → sem conflito."""
    dejem_start, dejem_end = combine_shift_window(_DAY, time(6, 0), time(14, 0))
    op_start = datetime(2026, 8, 19, 18, 0, tzinfo=_BR)
    op_end = datetime(2026, 8, 20, 2, 0, tzinfo=_BR)
    assert not intervals_overlap(dejem_start, dejem_end, op_start, op_end)


def test_overnight_dejem_overlaps_operational():
    dejem_start, dejem_end = combine_shift_window(_DAY, time(18, 30), time(2, 30))
    assert dejem_end.date() == date(2026, 8, 20)
    op_start = datetime(2026, 8, 19, 20, 0, tzinfo=_BR)
    op_end = datetime(2026, 8, 20, 4, 0, tzinfo=_BR)
    assert intervals_overlap(dejem_start, dejem_end, op_start, op_end)
    ov = overlap_interval(dejem_start, dejem_end, op_start, op_end)
    assert ov is not None
    assert ov[0] == op_start
    assert ov[1] == dejem_end


def test_overnight_no_overlap_when_disjoint():
    dejem_start, dejem_end = combine_shift_window(_DAY, time(18, 30), time(2, 30))
    op_start = datetime(2026, 8, 19, 6, 0, tzinfo=_BR)
    op_end = datetime(2026, 8, 19, 14, 0, tzinfo=_BR)
    assert not intervals_overlap(dejem_start, dejem_end, op_start, op_end)
