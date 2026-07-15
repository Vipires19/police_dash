"""Integração DEJEM ↔ Mapa Força (fase 4.6).

Disparada apenas na publicação/despublicação da Escala Operacional.
Não altera participantes nem saldo.
"""

from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.dejem import (
    DejemEnrollmentAction,
    DejemEnrollmentAudit,
    DejemParticipant,
    DejemShift,
    DejemShiftStatus,
    DejemShiftType,
    ParticipantStatus,
)
from models.user import User
from repositories.dejem_repository import DejemEnrollmentAuditRepository
from schemas.dejem import DejemMapBlock, DejemMapMember

_BR = ZoneInfo("America/Sao_Paulo")

# Status elegíveis para incorporação no Mapa Força (nunca OPEN / FINISHED).
_ELIGIBLE_FOR_INTEGRATION = {
    DejemShiftStatus.CLOSED,
    DejemShiftStatus.READY_FOR_MAP,
}

_MAP_TITLE: dict[DejemShiftType, str] = {
    DejemShiftType.FT: "APOIO TÁTICO",
    DejemShiftType.ROCAM: "ROCAM EXTRA",
    DejemShiftType.OUTROS: "DEJEM",
}


def map_block_title(shift_type: DejemShiftType | str) -> str:
    if isinstance(shift_type, str):
        try:
            shift_type = DejemShiftType(shift_type)
        except ValueError:
            return "DEJEM"
    return _MAP_TITLE.get(shift_type, "DEJEM")


def list_shifts_for_date(
    db: Session,
    day: date,
    *,
    statuses: set[DejemShiftStatus] | None = None,
) -> list[DejemShift]:
    stmt = (
        select(DejemShift)
        .options(
            joinedload(DejemShift.participants).joinedload(DejemParticipant.user),
        )
        .where(DejemShift.date == day)
        .order_by(DejemShift.start_time.asc(), DejemShift.id.asc())
    )
    if statuses is not None:
        stmt = stmt.where(DejemShift.status.in_(statuses))
    return list(db.scalars(stmt).unique().all())


def _active_members(shift: DejemShift) -> list[DejemMapMember]:
    members: list[DejemMapMember] = []
    for p in shift.participants or []:
        if p.status == ParticipantStatus.CANCELLED:
            continue
        u = p.user
        if not u:
            continue
        members.append(
            DejemMapMember(
                user_id=u.id,
                patente=u.patente or "",
                nome_guerra=u.nome_guerra or "",
                display_order=getattr(u, "display_order", 0) or 0,
            )
        )
    members.sort(key=lambda m: (m.display_order, m.nome_guerra.lower()))
    return members


def build_map_blocks(
    db: Session,
    day: date,
    *,
    statuses: set[DejemShiftStatus],
) -> list[DejemMapBlock]:
    blocks: list[DejemMapBlock] = []
    for shift in list_shifts_for_date(db, day, statuses=statuses):
        members = _active_members(shift)
        if not members:
            continue
        blocks.append(
            DejemMapBlock(
                shift_id=shift.id,
                title=map_block_title(shift.shift_type),
                shift_type=shift.shift_type,  # type: ignore[arg-type]
                start_time=shift.start_time,
                end_time=shift.end_time,
                status=shift.status,  # type: ignore[arg-type]
                vehicle_prefixo=None,
                members=members,
            )
        )
    return blocks


def integrate_closed_shifts_for_scale(
    db: Session,
    *,
    scale_id: int,
    scale_date: date,
    actor: User,
) -> int:
    """CLOSED / READY_FOR_MAP → INTEGRATED. Retorna quantidade integrada."""
    now = datetime.now(tz=_BR)
    shifts = list_shifts_for_date(db, scale_date, statuses=_ELIGIBLE_FOR_INTEGRATION)
    count = 0
    audit = DejemEnrollmentAuditRepository(db)
    for shift in shifts:
        # Somente com ao menos um participante ativo.
        if not _active_members(shift):
            continue
        shift.status = DejemShiftStatus.INTEGRATED
        shift.service_scale_id = scale_id
        shift.integrated_at = now
        shift.integrated_by_id = actor.id
        db.add(shift)
        audit.add_flush(
            DejemEnrollmentAudit(
                action=DejemEnrollmentAction.INTEGRATED,
                shift_id=shift.id,
                participant_id=None,
                subject_user_id=None,
                actor_id=actor.id,
                details=f"service_scale_id={scale_id}",
            )
        )
        count += 1
    return count


def reopen_integrated_shifts_for_scale(db: Session, *, scale_id: int, actor: User) -> int:
    """INTEGRATED → READY_FOR_MAP ao despublicar. Não mexe em participantes/saldo."""
    stmt = select(DejemShift).where(
        DejemShift.service_scale_id == scale_id,
        DejemShift.status == DejemShiftStatus.INTEGRATED,
    )
    shifts = list(db.scalars(stmt).all())
    audit = DejemEnrollmentAuditRepository(db)
    for shift in shifts:
        shift.status = DejemShiftStatus.READY_FOR_MAP
        shift.service_scale_id = None
        shift.integrated_at = None
        shift.integrated_by_id = None
        db.add(shift)
        audit.add_flush(
            DejemEnrollmentAudit(
                action=DejemEnrollmentAction.MAP_REOPENED,
                shift_id=shift.id,
                participant_id=None,
                subject_user_id=None,
                actor_id=actor.id,
                details=f"despublicado service_scale_id={scale_id}",
            )
        )
    return len(shifts)


def format_dejem_map_section(db: Session, day: date) -> list[str]:
    """Linhas para o texto do Mapa Força (somente INTEGRATED)."""
    blocks = build_map_blocks(db, day, statuses={DejemShiftStatus.INTEGRATED})
    if not blocks:
        return []

    lines: list[str] = ["DEJEM", ""]
    for block in blocks:
        lines.append(block.title)
        # Horário ajuda a distinguir múltiplos blocos do mesmo tipo
        lines.append(_format_time(block.start_time, block.end_time))
        if block.vehicle_prefixo:
            lines.append(block.vehicle_prefixo)
        for m in block.members:
            lines.append(_member_line(m.patente, m.nome_guerra))
        lines.append("")
    return lines


def _format_time(start: time, end: time) -> str:
    return f"{start.hour:02d}:{start.minute:02d} às {end.hour:02d}:{end.minute:02d}"


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


def _member_line(patente: str, nome_guerra: str) -> str:
    raw = patente.strip()
    short = _PATENTE_SHORT.get(raw.upper(), raw)
    return f"{short} {nome_guerra}"
