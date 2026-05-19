"""Formatação operacional de escala publicada para compartilhamento (ex.: WhatsApp)."""

from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.leaves import LeaveRequest, LeaveStatus, LeaveType
from models.service_scale import ScaleModality, ScaleStatus, ScaleTeam, ServiceScale
from models.vacation import VacationRequest, VacationStatus, VacationType
from services.service_scale_service import _BR, _load_scale

_MONTHS_PT = (
    "",
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
)

_PATENTE_SHORT: dict[str, str] = {
    "1° TEN": "Ten",
    "1º TEN": "Ten",
    "2° TEN": "Ten",
    "2º TEN": "Ten",
    "SUBTEN": "SubTen",
    "1° SGT": "Sgt",
    "1º SGT": "Sgt",
    "2° SGT": "Sgt",
    "2º SGT": "Sgt",
    "3° SGT": "Sgt",
    "3º SGT": "Sgt",
    "CB": "Cb",
    "SD": "Sd",
}

_DEFAULT_START = time(6, 0)
_DEFAULT_END = time(18, 0)


def _short_patente(patente: str) -> str:
    raw = patente.strip()
    hit = _PATENTE_SHORT.get(raw.upper())
    if hit:
        return hit
    for key, val in _PATENTE_SHORT.items():
        if key.upper() == raw.upper():
            return val
    return raw


def _member_line(patente: str, nome_guerra: str) -> str:
    return f"{_short_patente(patente)} {nome_guerra}"


def _format_date_header(scale_date: date) -> str:
    month = _MONTHS_PT[scale_date.month]
    return f"Dia {scale_date.day:02d} de {month} de {scale_date.year}"


def _format_qtr(published_at: datetime | None) -> str:
    if published_at is None:
        return "Qtr: —"
    local = published_at.astimezone(_BR)
    return f"Qtr: {local.hour:02d}:{local.minute:02d}hs"


def _format_time_range(start: datetime, end: datetime) -> str:
    s = start.astimezone(_BR)
    e = end.astimezone(_BR)
    return f"{s.hour:02d}:{s.minute:02d} às {e.hour:02d}:{e.minute:02d}"


def _is_default_shift(start: datetime, end: datetime, scale_date: date) -> bool:
    s = start.astimezone(_BR)
    e = end.astimezone(_BR)
    return (
        s.date() == scale_date
        and e.date() == scale_date
        and s.time() == _DEFAULT_START
        and e.time() == _DEFAULT_END
    )


def _sorted_members(team: ScaleTeam) -> list:
    return sorted(team.members, key=lambda m: (m.user.display_order if m.user else 0, m.user.nome_guerra if m.user else ""))


def _format_ft_team(team: ScaleTeam, scale_date: date) -> list[str]:
    lines: list[str] = []
    if not _is_default_shift(team.start_datetime, team.end_datetime, scale_date):
        lines.append(team.mission_name)
        lines.append(_format_time_range(team.start_datetime, team.end_datetime))
        lines.append("")
    prefix = team.vehicle.prefixo if team.vehicle else "—"
    lines.append(prefix)
    for m in _sorted_members(team):
        u = m.user
        if u:
            lines.append(_member_line(u.patente, u.nome_guerra))
    lines.append("")
    return lines


def _format_ro_cam_team(team: ScaleTeam, scale_date: date) -> list[str]:
    lines: list[str] = []
    lines.append(team.mission_name)
    if not _is_default_shift(team.start_datetime, team.end_datetime, scale_date):
        lines.append(_format_time_range(team.start_datetime, team.end_datetime))
    for m in _sorted_members(team):
        u = m.user
        moto = m.assigned_vehicle.prefixo if m.assigned_vehicle else "—"
        if u:
            lines.append(f"{_member_line(u.patente, u.nome_guerra)} -> Moto {moto}")
    lines.append("")
    return lines


def _collect_absences(db: Session, scale_date: date) -> dict[str, list[str]]:
    folga_mes: list[str] = []
    folga_comp: list[str] = []
    folga_ds: list[str] = []
    ferias: list[str] = []
    lp: list[str] = []
    afastamentos: list[str] = []

    leaves = db.scalars(
        select(LeaveRequest)
        .options(joinedload(LeaveRequest.user))
        .where(
            LeaveRequest.leave_on == scale_date,
            LeaveRequest.status == LeaveStatus.APPROVED,
        )
        .order_by(LeaveRequest.leave_type)
    ).all()

    for row in leaves:
        u = row.user
        if not u:
            continue
        line = _member_line(u.patente, u.nome_guerra)
        if row.leave_type == LeaveType.MONTHLY:
            folga_mes.append(line)
        elif row.leave_type == LeaveType.DS:
            folga_ds.append(line)
        else:
            folga_comp.append(line)

    vacations = db.scalars(
        select(VacationRequest)
        .options(joinedload(VacationRequest.user))
        .where(
            VacationRequest.start_date <= scale_date,
            VacationRequest.end_date >= scale_date,
            VacationRequest.status == VacationStatus.APPROVED,
        )
    ).all()

    for row in vacations:
        u = row.user
        if not u:
            continue
        line = _member_line(u.patente, u.nome_guerra)
        if row.vacation_type == VacationType.FERIAS:
            ferias.append(line)
        elif row.vacation_type == VacationType.LP:
            lp.append(line)
        else:
            label = row.vacation_type.value.replace("_", " ")
            afastamentos.append(f"{line} ({label})")

    for bucket in (folga_mes, folga_comp, folga_ds, ferias, lp, afastamentos):
        bucket.sort(key=str.lower)

    return {
        "folga_mes": folga_mes,
        "folga_comp": folga_comp,
        "folga_ds": folga_ds,
        "ferias": ferias,
        "lp": lp,
        "afastamentos": afastamentos,
    }


def _append_section(lines: list[str], title: str, items: list[str]) -> None:
    if not items:
        return
    lines.append(title)
    lines.extend(items)
    lines.append("")


def format_published_scale(db: Session, scale: ServiceScale) -> str:
    if scale.status != ScaleStatus.PUBLISHED:
        msg = "Somente escalas publicadas podem ser exportadas"
        raise ValueError(msg)

    lines: list[str] = [
        "💀 ESCALA DE SERVIÇO 💀",
        "1° PELOTÃO DE FORÇA TÁTICA",
        "",
        _format_date_header(scale.scale_date),
        _format_qtr(scale.published_at),
        "",
    ]

    ft_teams = sorted(
        [t for t in scale.teams if t.modality == ScaleModality.FT],
        key=lambda t: t.start_datetime,
    )
    ro_teams = sorted(
        [t for t in scale.teams if t.modality == ScaleModality.ROCAM],
        key=lambda t: t.start_datetime,
    )

    for team in ft_teams:
        lines.extend(_format_ft_team(team, scale.scale_date))
    for team in ro_teams:
        lines.extend(_format_ro_cam_team(team, scale.scale_date))

    absences = _collect_absences(db, scale.scale_date)
    _append_section(lines, "Folga do mês:", absences["folga_mes"])
    _append_section(lines, "Folga compensação:", absences["folga_comp"])
    _append_section(lines, "DS:", absences["folga_ds"])
    _append_section(lines, "Férias:", absences["ferias"])
    _append_section(lines, "LP:", absences["lp"])
    _append_section(lines, "Afastamentos:", absences["afastamentos"])

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


def build_export_text(db: Session, scale_id: int) -> str:
    scale = _load_scale(db, scale_id)
    if not scale:
        msg = "Escala não encontrada"
        raise ValueError(msg)
    return format_published_scale(db, scale)
