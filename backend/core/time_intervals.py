"""Utilitários de intervalos de tempo (sobreposição e turnos overnight)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

_BR = ZoneInfo("America/Sao_Paulo")


def intervals_overlap(
    start_a: datetime,
    end_a: datetime,
    start_b: datetime,
    end_b: datetime,
) -> bool:
    """True se [start_a, end_a) e [start_b, end_b) se sobrepõem.

    Convenção: start < end_b and end > start_b.
    """
    return start_a < end_b and end_a > start_b


def overlap_interval(
    start_a: datetime,
    end_a: datetime,
    start_b: datetime,
    end_b: datetime,
) -> tuple[datetime, datetime] | None:
    """Retorna (início, fim) da interseção, ou None se não houver sobreposição."""
    if not intervals_overlap(start_a, end_a, start_b, end_b):
        return None
    return max(start_a, start_b), min(end_a, end_b)


def combine_shift_window(
    day: date,
    start: time,
    end: time,
    *,
    tz: ZoneInfo = _BR,
) -> tuple[datetime, datetime]:
    """Monta janela datetime a partir de data + horários.

    Se end <= start, o término é no dia seguinte (turno que atravessa a meia-noite).
    Ex.: 18:30 → 02:30.
    """
    start_dt = datetime.combine(day, start, tzinfo=tz)
    end_dt = datetime.combine(day, end, tzinfo=tz)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return start_dt, end_dt


def ensure_aware(value: datetime, *, tz: ZoneInfo = _BR) -> datetime:
    """Garante datetime timezone-aware (assume `tz` se naive)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value


def format_hhmm(value: datetime, *, tz: ZoneInfo = _BR) -> str:
    local = value.astimezone(tz) if value.tzinfo is not None else value
    return f"{local.hour:02d}:{local.minute:02d}"
