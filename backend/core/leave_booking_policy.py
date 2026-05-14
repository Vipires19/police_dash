"""Regras de janela para solicitação de folgas (mês corrente / próximo após dia 25)."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

_BR = ZoneInfo("America/Sao_Paulo")

BOOKING_HINT = "Folgas do próximo mês liberadas a partir do dia 25"


def today_br() -> date:
    return datetime.now(_BR).date()


def allowed_booking_month_keys(reference: date | None = None) -> set[tuple[int, int]]:
    """Meses em que é permitido registrar folga nova, relativos à data de referência (hoje BR)."""
    ref = reference if reference is not None else today_br()
    y, m = ref.year, ref.month
    allowed: set[tuple[int, int]] = {(y, m)}
    if ref.day >= 25:
        if m == 12:
            allowed.add((y + 1, 1))
        else:
            allowed.add((y, m + 1))
    return allowed


def can_request_for_month(leave_on: date, *, reference: date | None = None) -> bool:
    ref = reference if reference is not None else today_br()
    return (leave_on.year, leave_on.month) in allowed_booking_month_keys(ref)


def assert_leave_booking_allowed(leave_on: date, *, reference: date | None = None) -> None:
    """Levanta ValueError se a data estiver fora da janela operacional."""
    ref = reference if reference is not None else today_br()
    if leave_on < ref:
        raise ValueError("Não é permitido solicitar folga para data retroativa")
    if not can_request_for_month(leave_on, reference=ref):
        raise ValueError(
            "Solicitação fora da janela: folgas do próximo mês liberadas somente a partir do dia 25 do mês atual."
        )
