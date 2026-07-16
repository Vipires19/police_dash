"""Autoinscrição em escalas DEJEM (fase 4.5).

Separado da distribuição. Não integra com Escalas / Mapa Força / mensagens.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.dejem import (
    DejemEnrollmentAction,
    DejemEnrollmentAudit,
    DejemMonthStatus,
    DejemParticipant,
    DejemShift,
    DejemShiftStatus,
    ParticipantStatus,
    ParticipationType,
)
from models.user import User
from repositories.dejem_repository import (
    DejemAllocationRepository,
    DejemEnrollmentAuditRepository,
    DejemMonthRepository,
    DejemParticipantRepository,
    DejemShiftRepository,
)
from schemas.dejem import (
    DejemAdminAddParticipant,
    DejemEnrollmentResult,
    DejemMyShiftCard,
    DejemParticipantAdminRow,
    DejemShiftPublic,
)
from services.dejem_service import DejemError
from services.dejem_shift_service import _shift_to_public

_BR = ZoneInfo("America/Sao_Paulo")


def _consumes_balance(participation_type: ParticipationType) -> bool:
    return participation_type == ParticipationType.NORMAL


def _shift_window(day: date, start: time, end: time) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(day, start, tzinfo=_BR)
    end_dt = datetime.combine(day, end, tzinfo=_BR)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return start_dt, end_dt


def _assert_shift_open(shift: DejemShift) -> None:
    if shift.status != DejemShiftStatus.OPEN:
        raise DejemError("A escala não está aberta para inscrições.")


_ADMIN_PARTICIPANT_STATUSES = {
    DejemShiftStatus.OPEN,
    DejemShiftStatus.CLOSED,
    DejemShiftStatus.READY_FOR_MAP,
    DejemShiftStatus.INTEGRATED,
}


def _assert_shift_admin_editable(shift: DejemShift) -> None:
    """Admin pode gerenciar participantes até a publicação definitiva (FINISHED)."""
    if shift.status not in _ADMIN_PARTICIPANT_STATUSES:
        raise DejemError("Não é possível alterar participantes em escala finalizada.")


def _sync_map_artifacts(db: Session, shift: DejemShift, actor: User) -> None:
    if shift.status not in {
        DejemShiftStatus.CLOSED,
        DejemShiftStatus.READY_FOR_MAP,
        DejemShiftStatus.INTEGRATED,
    }:
        return
    from services.dejem_operational_sync import refresh_operational_artifacts_for_day

    refresh_operational_artifacts_for_day(db, shift.date, actor=actor)


def _assert_capacity(repo: DejemShiftRepository, shift: DejemShift) -> None:
    filled = repo.count_filled(shift.id)
    if filled >= shift.capacity:
        raise DejemError("Esta escala está lotada.")


def _assert_no_dejem_overlap(
    part_repo: DejemParticipantRepository,
    *,
    user_id: int,
    shift: DejemShift,
) -> None:
    start_dt, end_dt = _shift_window(shift.date, shift.start_time, shift.end_time)
    dates = [shift.date]
    if end_dt.date() != shift.date:
        dates.append(end_dt.date())

    others = part_repo.list_active_for_user_on_dates(
        user_id,
        dates,
        exclude_shift_id=shift.id,
    )
    for other in others:
        other_shift = other.shift
        if other_shift is None:
            continue
        o_start, o_end = _shift_window(
            other_shift.date,
            other_shift.start_time,
            other_shift.end_time,
        )
        if start_dt < o_end and o_start < end_dt:
            raise DejemError("Conflito com outra escala DEJEM no mesmo horário.")


def _assert_no_operational_overlap(db: Session, *, user_id: int, shift: DejemShift) -> None:
    from models.service_scale import ScaleStatus, ScaleTeam, ScaleTeamMember, ServiceScale

    start_dt, end_dt = _shift_window(shift.date, shift.start_time, shift.end_time)
    # Janela de busca: dia anterior e seguinte (overnight / fusos)
    window_start = start_dt - timedelta(days=1)
    window_end = end_dt + timedelta(days=1)

    stmt = (
        select(ScaleTeam)
        .join(ServiceScale, ScaleTeam.service_scale_id == ServiceScale.id)
        .join(ScaleTeamMember, ScaleTeamMember.scale_team_id == ScaleTeam.id)
        .where(
            ScaleTeamMember.user_id == user_id,
            ServiceScale.status == ScaleStatus.PUBLISHED,
            ScaleTeam.start_datetime < window_end,
            ScaleTeam.end_datetime > window_start,
        )
    )
    teams = list(db.scalars(stmt).unique().all())
    for team in teams:
        t0 = team.start_datetime
        t1 = team.end_datetime
        if t0.tzinfo is None:
            t0 = t0.replace(tzinfo=_BR)
        if t1.tzinfo is None:
            t1 = t1.replace(tzinfo=_BR)
        if start_dt < t1 and t0 < end_dt:
            raise DejemError(
                "Conflito com Escala Operacional já publicada no mesmo horário."
            )


def _participant_to_result(row: DejemParticipant, allocation_remaining: int | None) -> DejemEnrollmentResult:
    return DejemEnrollmentResult(
        participant_id=row.id,
        shift_id=row.shift_id,
        user_id=row.user_id,
        participation_type=row.participation_type,  # type: ignore[arg-type]
        status=row.status,  # type: ignore[arg-type]
        consumes_balance=row.consumes_balance,
        remaining_slots=allocation_remaining,
        created_at=row.created_at,
    )


def _audit(
    db: Session,
    *,
    action: DejemEnrollmentAction,
    shift_id: int,
    actor_id: int,
    subject_user_id: int | None,
    participant_id: int | None,
    details: str | None = None,
) -> None:
    DejemEnrollmentAuditRepository(db).add_flush(
        DejemEnrollmentAudit(
            action=action,
            shift_id=shift_id,
            participant_id=participant_id,
            subject_user_id=subject_user_id,
            actor_id=actor_id,
            details=details,
        )
    )


def _consume_or_release(
    alloc_repo: DejemAllocationRepository,
    *,
    month_id: int,
    user_id: int,
    consume: bool,
    delta: int = 1,
) -> int:
    """Ajusta saldo. delta positivo consome; negativo libera. Retorna remaining."""
    alloc = alloc_repo.get_by_month_and_user(month_id, user_id)
    if alloc is None:
        raise DejemError("Você não possui saldo DEJEM neste mês.")
    if consume:
        if alloc.remaining_slots < delta:
            raise DejemError("Saldo DEJEM insuficiente.")
        alloc.used_slots += delta
        alloc.remaining_slots = max(0, alloc.allocated_slots - alloc.used_slots)
    else:
        alloc.used_slots = max(0, alloc.used_slots - delta)
        alloc.remaining_slots = max(0, alloc.allocated_slots - alloc.used_slots)
    alloc_repo.save_flush(alloc)
    return alloc.remaining_slots


def enroll_self(
    db: Session,
    target: User,
    shift_id: int,
    *,
    actor: User | None = None,
) -> DejemEnrollmentResult:
    actor = actor or target
    shift_repo = DejemShiftRepository(db)
    part_repo = DejemParticipantRepository(db)
    alloc_repo = DejemAllocationRepository(db)

    shift = shift_repo.get_by_id(shift_id)
    if not shift:
        raise DejemError("Escala não encontrada.")

    month = DejemMonthRepository(db).get_by_id(shift.month_id)
    if not month:
        raise DejemError("Mês DEJEM não encontrado.")
    if month.status not in {DejemMonthStatus.DISTRIBUTED, DejemMonthStatus.OPEN_SHIFTS}:
        raise DejemError("Inscrições só são permitidas após a distribuição das vagas.")

    _assert_shift_open(shift)
    _assert_capacity(shift_repo, shift)

    existing = part_repo.get_by_shift_and_user(shift.id, target.id)
    if existing and existing.status != ParticipantStatus.CANCELLED:
        raise DejemError("Você já está inscrito nesta escala.")

    _assert_no_dejem_overlap(part_repo, user_id=target.id, shift=shift)
    _assert_no_operational_overlap(db, user_id=target.id, shift=shift)

    remaining = _consume_or_release(
        alloc_repo,
        month_id=shift.month_id,
        user_id=target.id,
        consume=True,
    )

    acting_as = actor.id != target.id
    if existing and existing.status == ParticipantStatus.CANCELLED:
        existing.status = ParticipantStatus.REGISTERED
        existing.participation_type = ParticipationType.NORMAL
        existing.consumes_balance = True
        existing.enrolled_by_id = actor.id
        existing.cancelled_at = None
        existing.cancelled_by_id = None
        row = part_repo.save_flush(existing)
        action = DejemEnrollmentAction.ADMIN_ADDED if acting_as else DejemEnrollmentAction.ENROLLED
    else:
        row = part_repo.add_flush(
            DejemParticipant(
                shift_id=shift.id,
                user_id=target.id,
                participation_type=ParticipationType.NORMAL,
                status=ParticipantStatus.REGISTERED,
                enrolled_by_id=actor.id,
                consumes_balance=True,
            )
        )
        action = DejemEnrollmentAction.ADMIN_ADDED if acting_as else DejemEnrollmentAction.ENROLLED

    if month.status == DejemMonthStatus.DISTRIBUTED:
        month.status = DejemMonthStatus.OPEN_SHIFTS
        db.add(month)

    _audit(
        db,
        action=action,
        shift_id=shift.id,
        actor_id=actor.id,
        subject_user_id=target.id,
        participant_id=row.id,
        details="god_mode" if acting_as else "autoinscrição",
    )
    part_repo.commit()
    return _participant_to_result(row, remaining)


def cancel_self(
    db: Session,
    target: User,
    shift_id: int,
    *,
    actor: User | None = None,
) -> DejemEnrollmentResult:
    actor = actor or target
    shift_repo = DejemShiftRepository(db)
    part_repo = DejemParticipantRepository(db)
    alloc_repo = DejemAllocationRepository(db)

    shift = shift_repo.get_by_id(shift_id)
    if not shift:
        raise DejemError("Escala não encontrada.")
    _assert_shift_open(shift)

    row = part_repo.get_by_shift_and_user(shift.id, target.id)
    if not row or row.status == ParticipantStatus.CANCELLED:
        raise DejemError("Você não está inscrito nesta escala.")

    remaining: int | None = None
    if row.consumes_balance:
        remaining = _consume_or_release(
            alloc_repo,
            month_id=shift.month_id,
            user_id=target.id,
            consume=False,
        )
    else:
        alloc = alloc_repo.get_by_month_and_user(shift.month_id, target.id)
        remaining = alloc.remaining_slots if alloc else None

    row.status = ParticipantStatus.CANCELLED
    row.cancelled_at = datetime.now(tz=_BR)
    row.cancelled_by_id = actor.id
    part_repo.save_flush(row)

    acting_as = actor.id != target.id
    _audit(
        db,
        action=DejemEnrollmentAction.ADMIN_REMOVED if acting_as else DejemEnrollmentAction.CANCELLED,
        shift_id=shift.id,
        actor_id=actor.id,
        subject_user_id=target.id,
        participant_id=row.id,
        details="god_mode" if acting_as else "autocancelamento",
    )
    part_repo.commit()
    return _participant_to_result(row, remaining)


def list_participants_admin(db: Session, shift_id: int) -> list[DejemParticipantAdminRow]:
    shift = DejemShiftRepository(db).get_by_id(shift_id)
    if not shift:
        raise DejemError("Escala não encontrada.")

    part_repo = DejemParticipantRepository(db)
    alloc_repo = DejemAllocationRepository(db)
    rows = part_repo.list_active_by_shift(shift_id)
    out: list[DejemParticipantAdminRow] = []
    for row in rows:
        u = row.user
        alloc = alloc_repo.get_by_month_and_user(shift.month_id, row.user_id)
        out.append(
            DejemParticipantAdminRow(
                id=row.id,
                shift_id=row.shift_id,
                user_id=row.user_id,
                participation_type=row.participation_type,  # type: ignore[arg-type]
                status=row.status,  # type: ignore[arg-type]
                consumes_balance=row.consumes_balance,
                created_at=row.created_at,
                enrolled_by_id=row.enrolled_by_id,
                patente=getattr(u, "patente", "") or "",
                nome_guerra=getattr(u, "nome_guerra", "") or "",
                full_name=getattr(u, "full_name", None),
                remaining_slots=alloc.remaining_slots if alloc else 0,
            )
        )
    return out


def admin_add_participant(
    db: Session,
    current: User,
    shift_id: int,
    body: DejemAdminAddParticipant,
) -> DejemEnrollmentResult:
    shift_repo = DejemShiftRepository(db)
    part_repo = DejemParticipantRepository(db)
    alloc_repo = DejemAllocationRepository(db)

    shift = shift_repo.get_by_id(shift_id)
    if not shift:
        raise DejemError("Escala não encontrada.")
    _assert_shift_admin_editable(shift)
    _assert_capacity(shift_repo, shift)

    target = db.get(User, body.user_id)
    if not target:
        raise DejemError("Policial não encontrado.")

    existing = part_repo.get_by_shift_and_user(shift.id, body.user_id)
    if existing and existing.status != ParticipantStatus.CANCELLED:
        raise DejemError("Este policial já está inscrito nesta escala.")

    _assert_no_dejem_overlap(part_repo, user_id=body.user_id, shift=shift)
    _assert_no_operational_overlap(db, user_id=body.user_id, shift=shift)

    ptype = ParticipationType(body.participation_type.value)
    consumes = _consumes_balance(ptype)
    remaining: int | None = None
    if consumes:
        remaining = _consume_or_release(
            alloc_repo,
            month_id=shift.month_id,
            user_id=body.user_id,
            consume=True,
        )
    else:
        alloc = alloc_repo.get_by_month_and_user(shift.month_id, body.user_id)
        remaining = alloc.remaining_slots if alloc else None

    if existing and existing.status == ParticipantStatus.CANCELLED:
        existing.status = ParticipantStatus.REGISTERED
        existing.participation_type = ptype
        existing.consumes_balance = consumes
        existing.enrolled_by_id = current.id
        existing.cancelled_at = None
        existing.cancelled_by_id = None
        row = part_repo.save_flush(existing)
    else:
        row = part_repo.add_flush(
            DejemParticipant(
                shift_id=shift.id,
                user_id=body.user_id,
                participation_type=ptype,
                status=ParticipantStatus.REGISTERED,
                enrolled_by_id=current.id,
                consumes_balance=consumes,
            )
        )

    month = DejemMonthRepository(db).get_by_id(shift.month_id)
    if month and month.status == DejemMonthStatus.DISTRIBUTED:
        month.status = DejemMonthStatus.OPEN_SHIFTS
        db.add(month)

    _audit(
        db,
        action=DejemEnrollmentAction.ADMIN_ADDED,
        shift_id=shift.id,
        actor_id=current.id,
        subject_user_id=body.user_id,
        participant_id=row.id,
        details=f"tipo={ptype.value}",
    )
    part_repo.commit()
    _sync_map_artifacts(db, shift, current)
    return _participant_to_result(row, remaining)


def admin_remove_participant(
    db: Session,
    current: User,
    shift_id: int,
    user_id: int,
) -> DejemEnrollmentResult:
    shift_repo = DejemShiftRepository(db)
    part_repo = DejemParticipantRepository(db)
    alloc_repo = DejemAllocationRepository(db)

    shift = shift_repo.get_by_id(shift_id)
    if not shift:
        raise DejemError("Escala não encontrada.")
    _assert_shift_admin_editable(shift)

    row = part_repo.get_by_shift_and_user(shift.id, user_id)
    if not row or row.status == ParticipantStatus.CANCELLED:
        raise DejemError("Participante não encontrado nesta escala.")

    remaining: int | None = None
    if row.consumes_balance:
        remaining = _consume_or_release(
            alloc_repo,
            month_id=shift.month_id,
            user_id=user_id,
            consume=False,
        )
    else:
        alloc = alloc_repo.get_by_month_and_user(shift.month_id, user_id)
        remaining = alloc.remaining_slots if alloc else None

    row.status = ParticipantStatus.CANCELLED
    row.cancelled_at = datetime.now(tz=_BR)
    row.cancelled_by_id = current.id
    part_repo.save_flush(row)

    _audit(
        db,
        action=DejemEnrollmentAction.ADMIN_REMOVED,
        shift_id=shift.id,
        actor_id=current.id,
        subject_user_id=user_id,
        participant_id=row.id,
        details="remoção administrativa",
    )
    part_repo.commit()
    _sync_map_artifacts(db, shift, current)
    return _participant_to_result(row, remaining)


def close_shift(db: Session, current: User, shift_id: int) -> DejemShiftPublic:
    shift_repo = DejemShiftRepository(db)
    shift = shift_repo.get_by_id(shift_id)
    if not shift:
        raise DejemError("Escala não encontrada.")
    if shift.status != DejemShiftStatus.OPEN:
        raise DejemError("Somente escalas abertas podem ser fechadas.")

    filled = shift_repo.count_filled(shift.id)
    if filled < 1:
        raise DejemError("É necessário ao menos um participante para fechar a escala.")
    if not shift.vehicle_id:
        raise DejemError(
            "Selecione uma viatura antes de fechar a escala DEJEM "
            "(necessária para a mensagem operacional / Mapa Força)."
        )

    shift.status = DejemShiftStatus.CLOSED
    shift.closed_at = datetime.now(tz=_BR)
    shift.closed_by_id = current.id
    db.add(shift)

    _audit(
        db,
        action=DejemEnrollmentAction.CLOSED,
        shift_id=shift.id,
        actor_id=current.id,
        subject_user_id=None,
        participant_id=None,
        details=f"participantes={filled}",
    )
    db.commit()
    shift = shift_repo.get_by_id(shift.id) or shift
    return _shift_to_public(shift, filled)


def get_my_day_cards(
    db: Session,
    target: User,
    year: int,
    month: int,
    day: int,
) -> list[DejemMyShiftCard]:
    d = date(year, month, day)
    month_row = DejemMonthRepository(db).get_by_year_month(year, month)
    if not month_row:
        return []

    shift_repo = DejemShiftRepository(db)
    part_repo = DejemParticipantRepository(db)
    rows = shift_repo.list_by_month_and_date(month_row.id, d)
    cards: list[DejemMyShiftCard] = []
    for shift in rows:
        filled = shift_repo.count_filled(shift.id)
        mine = part_repo.get_by_shift_and_user(shift.id, target.id)
        enrolled = bool(mine and mine.status != ParticipantStatus.CANCELLED)
        cards.append(
            DejemMyShiftCard(
                id=shift.id,
                month_id=shift.month_id,
                date=shift.date,
                start_time=shift.start_time,
                end_time=shift.end_time,
                shift_type=shift.shift_type,  # type: ignore[arg-type]
                capacity=shift.capacity,
                filled_slots=filled,
                available_slots=max(0, shift.capacity - filled),
                status=shift.status,  # type: ignore[arg-type]
                i_am_enrolled=enrolled,
                my_participation_type=(
                    mine.participation_type if enrolled and mine else None  # type: ignore[arg-type]
                ),
            )
        )
    return cards
