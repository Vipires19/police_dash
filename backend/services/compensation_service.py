from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from core.compensation_labels import MERIT_COMPENSATION_TYPES, compensation_display_label
from models.audit import AuditOrigin
from models.compensations import (
    CompensationEvent,
    CompensationEventLog,
    CompensationEventParticipant,
    CompensationLogAction,
    CompensationStatus,
    CompensationType,
    DS_ANNUAL_REFERENCE_QUOTA,
    UserCompensation,
    UserCompensationStatus,
)
from models.leaves import LeaveRequest, LeaveStatus, LeaveType
from models.user import User, UserRole, UserStatus
from schemas.compensations import (
    CompensationDashboardSummary,
    CompensationEventCreate,
    CompensationEventUpdate,
    CompensationEventPublic,
    CompensationEventLogPublic,
    DsUsagePublic,
)

_BR = ZoneInfo("America/Sao_Paulo")

_TERMINAL_STATUSES = {
    CompensationStatus.REJECTED,
    CompensationStatus.CANCELLED,
    CompensationStatus.REVERTED,
}


def _actor_label(user: User) -> str:
    return f"{user.patente} {user.nome_guerra}"


def _append_log(
    db: Session,
    *,
    event_id: int,
    actor_id: int,
    action: CompensationLogAction,
    from_status: CompensationStatus | None = None,
    to_status: CompensationStatus | None = None,
    motivo: str | None = None,
    details: str | None = None,
    subject_user_id: int | None = None,
    origin: AuditOrigin = AuditOrigin.SELF,
) -> CompensationEventLog:
    row = CompensationEventLog(
        compensation_event_id=event_id,
        actor_id=actor_id,
        subject_user_id=subject_user_id,
        origin=origin,
        action=action,
        from_status=from_status,
        to_status=to_status,
        motivo=motivo,
        details=details,
    )
    db.add(row)
    return row


def _ensure_relevant_occurrence_gate(approver: User, event: CompensationEvent) -> None:
    if event.event_type != CompensationType.RELEVANT_OCCURRENCE:
        return
    if approver.role not in {UserRole.ADMIN, UserRole.CMD_TATICO, UserRole.N90, UserRole.TAT_CMD}:
        raise ValueError("Ocorrência de grande relevância: aprovação restrita a N90/TAT_CMD/CMD_TATICO (e ADMIN)")


def get_compensation_event(db: Session, event_id: int) -> CompensationEvent | None:
    return db.scalars(
        select(CompensationEvent)
        .options(selectinload(CompensationEvent.participants))
        .where(CompensationEvent.id == event_id)
    ).first()


def _revoke_credits_for_event(db: Session, event_id: int) -> None:
    credits = list(
        db.scalars(select(UserCompensation).where(UserCompensation.compensation_event_id == event_id)).all()
    )
    for c in credits:
        if c.status == UserCompensationStatus.AVAILABLE:
            c.status = UserCompensationStatus.REVOKED


def _issue_credits_for_event(db: Session, ev: CompensationEvent) -> None:
    for p in ev.participants:
        exists = db.scalars(
            select(UserCompensation).where(
                UserCompensation.compensation_event_id == ev.id,
                UserCompensation.user_id == p.user_id,
            )
        ).first()
        if exists:
            if exists.status == UserCompensationStatus.REVOKED:
                exists.status = UserCompensationStatus.AVAILABLE
            continue
        db.add(
            UserCompensation(
                user_id=p.user_id,
                compensation_event_id=ev.id,
                status=UserCompensationStatus.AVAILABLE,
                display_label=compensation_display_label(ev.event_type),
            )
        )


def event_to_public(ev: CompensationEvent, db: Session) -> CompensationEventPublic:
    creator = db.get(User, ev.created_by_id)
    decider = db.get(User, ev.decided_by_id) if ev.decided_by_id else None
    return CompensationEventPublic(
        id=ev.id,
        event_type=ev.event_type,
        motivo=ev.motivo,
        status=ev.status,
        created_by_id=ev.created_by_id,
        decided_by_id=ev.decided_by_id,
        decided_at=ev.decided_at,
        decision_motivo=ev.decision_motivo,
        created_at=ev.created_at,
        updated_at=ev.updated_at,
        participant_user_ids=[p.user_id for p in ev.participants],
        created_by_label=_actor_label(creator) if creator else None,
        decided_by_label=_actor_label(decider) if decider else None,
    )


def create_compensation_event(db: Session, creator: User, body: CompensationEventCreate) -> CompensationEvent:
    if body.event_type not in MERIT_COMPENSATION_TYPES:
        raise ValueError("Selecione o mérito que gera direito à compensação (CPJ, ocorrências, etc.)")

    ids = list({int(x) for x in body.participant_user_ids})
    if not ids:
        raise ValueError("Selecione ao menos um envolvido")

    found = list(db.scalars(select(User).where(User.id.in_(ids))).all())
    if len(found) != len(ids):
        raise ValueError("Participante inexistente")
    if any(u.status != UserStatus.APPROVED or not u.is_active for u in found):
        raise ValueError("Participante inválido ou inativo")

    ev = CompensationEvent(
        event_type=body.event_type,
        motivo=body.motivo.strip(),
        created_by_id=creator.id,
        status=CompensationStatus.PENDING,
    )
    db.add(ev)
    db.flush()
    for uid in ids:
        db.add(CompensationEventParticipant(compensation_event_id=ev.id, user_id=uid))
    _append_log(
        db,
        event_id=ev.id,
        actor_id=creator.id,
        action=CompensationLogAction.CREATED,
        to_status=CompensationStatus.PENDING,
        details=f"Tipo: {body.event_type.value}",
        subject_user_id=ids[0] if len(ids) == 1 else None,
        origin=AuditOrigin.ADMIN if creator.id not in ids else AuditOrigin.SELF,
    )
    db.commit()
    db.refresh(ev)
    return ev


def list_compensation_events(
    db: Session,
    *,
    status: CompensationStatus | None = None,
    event_type: CompensationType | None = None,
    user_id: int | None = None,
    year: int | None = None,
    limit: int = 200,
) -> list[CompensationEvent]:
    stmt = select(CompensationEvent).options(selectinload(CompensationEvent.participants))
    if status is not None:
        stmt = stmt.where(CompensationEvent.status == status)
    if event_type is not None:
        stmt = stmt.where(CompensationEvent.event_type == event_type)
    if user_id is not None:
        stmt = stmt.join(CompensationEventParticipant).where(CompensationEventParticipant.user_id == user_id)
    if year is not None:
        start = datetime(year, 1, 1, tzinfo=_BR)
        end = datetime(year + 1, 1, 1, tzinfo=_BR)
        stmt = stmt.where(
            CompensationEvent.created_at >= start,
            CompensationEvent.created_at < end,
        )
    stmt = stmt.order_by(CompensationEvent.created_at.desc()).limit(limit)
    return list(db.scalars(stmt).unique().all())


def list_pending_compensation_events(db: Session) -> list[CompensationEvent]:
    return list_compensation_events(db, status=CompensationStatus.PENDING, limit=100)


def list_event_logs(db: Session, event_id: int) -> list[CompensationEventLogPublic]:
    stmt = (
        select(CompensationEventLog, User)
        .join(User, User.id == CompensationEventLog.actor_id)
        .where(CompensationEventLog.compensation_event_id == event_id)
        .order_by(CompensationEventLog.created_at.desc())
    )
    out: list[CompensationEventLogPublic] = []
    for log, actor in db.execute(stmt).all():
        out.append(
            CompensationEventLogPublic(
                id=log.id,
                compensation_event_id=log.compensation_event_id,
                actor_id=log.actor_id,
                actor_label=_actor_label(actor),
                action=log.action,
                from_status=log.from_status,
                to_status=log.to_status,
                motivo=log.motivo,
                details=log.details,
                created_at=log.created_at,
            )
        )
    return out


def count_ds_usage(db: Session, user_id: int, year: int) -> DsUsagePublic:
    from datetime import date

    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    used = db.scalar(
        select(func.count(LeaveRequest.id)).where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.leave_type == LeaveType.DS,
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.leave_on >= start,
            LeaveRequest.leave_on < end,
        )
    )
    used_count = int(used or 0)
    return DsUsagePublic(
        user_id=user_id,
        year=year,
        used_count=used_count,
        reference_quota=DS_ANNUAL_REFERENCE_QUOTA,
        display=f"{used_count}/{DS_ANNUAL_REFERENCE_QUOTA} DS utilizadas em {year}",
    )


def get_dashboard_summary(db: Session, actor: User, year: int) -> CompensationDashboardSummary:
    pending_count = db.scalar(
        select(func.count()).select_from(CompensationEvent).where(CompensationEvent.status == CompensationStatus.PENDING)
    )
    start = datetime(year, 1, 1, tzinfo=_BR)
    approved_recent = list(
        db.scalars(
            select(CompensationEvent)
            .options(selectinload(CompensationEvent.participants))
            .where(
                CompensationEvent.status == CompensationStatus.APPROVED,
                CompensationEvent.created_at >= start,
            )
            .order_by(CompensationEvent.decided_at.desc().nullslast())
            .limit(5)
        ).all()
    )
    ds_sample = count_ds_usage(db, actor.id, year)
    recent = list_compensation_events(db, limit=8)
    return CompensationDashboardSummary(
        pending_count=int(pending_count or 0),
        approved_recent_count=len(approved_recent),
        ds_usage_samples=[ds_sample],
        recent_events=[event_to_public(e, db) for e in recent],
    )


def update_compensation_event(
    db: Session,
    event_id: int,
    actor: User,
    body: CompensationEventUpdate,
) -> CompensationEvent:
    ev = get_compensation_event(db, event_id)
    if not ev:
        raise ValueError("Evento não encontrado")
    if ev.status != CompensationStatus.PENDING:
        raise ValueError("Somente eventos pendentes podem ser editados")

    changes: list[str] = []
    if body.event_type is not None and body.event_type != ev.event_type:
        ev.event_type = body.event_type
        changes.append(f"tipo → {body.event_type.value}")
    if body.motivo is not None:
        nm = body.motivo.strip()
        if nm != ev.motivo:
            ev.motivo = nm
            changes.append("motivo atualizado")
    if body.participant_user_ids is not None:
        ids = list({int(x) for x in body.participant_user_ids})
        if not ids:
            raise ValueError("Selecione ao menos um envolvido")
        found = list(db.scalars(select(User).where(User.id.in_(ids))).all())
        if len(found) != len(ids):
            raise ValueError("Participante inexistente")
        if any(u.status != UserStatus.APPROVED or not u.is_active for u in found):
            raise ValueError("Participante inválido ou inativo")
        for p in list(ev.participants):
            db.delete(p)
        db.flush()
        for uid in ids:
            db.add(CompensationEventParticipant(compensation_event_id=ev.id, user_id=uid))
        changes.append("participantes atualizados")

    if not changes:
        return ev

    _append_log(
        db,
        event_id=ev.id,
        actor_id=actor.id,
        action=CompensationLogAction.UPDATED,
        from_status=CompensationStatus.PENDING,
        to_status=CompensationStatus.PENDING,
        details="; ".join(changes),
    )
    db.commit()
    db.refresh(ev)
    return get_compensation_event(db, ev.id) or ev


def approve_compensation_event(db: Session, event_id: int, approver: User, motivo: str | None) -> CompensationEvent:
    ev = get_compensation_event(db, event_id)
    if not ev:
        raise ValueError("Evento não encontrado")
    if ev.status != CompensationStatus.PENDING:
        raise ValueError("Evento não está pendente")

    _ensure_relevant_occurrence_gate(approver, ev)

    old = ev.status
    ev.status = CompensationStatus.APPROVED
    ev.decided_by_id = approver.id
    ev.decided_at = datetime.now(_BR)
    ev.decision_motivo = motivo

    _issue_credits_for_event(db, ev)
    _append_log(
        db,
        event_id=ev.id,
        actor_id=approver.id,
        action=CompensationLogAction.APPROVED,
        from_status=old,
        to_status=ev.status,
        motivo=motivo,
    )

    db.commit()
    db.refresh(ev)
    return ev


def reject_compensation_event(db: Session, event_id: int, approver: User, motivo: str) -> CompensationEvent:
    ev = get_compensation_event(db, event_id)
    if not ev:
        raise ValueError("Evento não encontrado")
    if ev.status != CompensationStatus.PENDING:
        raise ValueError("Evento não está pendente")

    _ensure_relevant_occurrence_gate(approver, ev)

    old = ev.status
    ev.status = CompensationStatus.REJECTED
    ev.decided_by_id = approver.id
    ev.decided_at = datetime.now(_BR)
    ev.decision_motivo = motivo

    _append_log(
        db,
        event_id=ev.id,
        actor_id=approver.id,
        action=CompensationLogAction.REJECTED,
        from_status=old,
        to_status=ev.status,
        motivo=motivo,
    )

    db.commit()
    db.refresh(ev)
    return ev


def cancel_compensation_event(db: Session, event_id: int, actor: User, motivo: str) -> CompensationEvent:
    ev = get_compensation_event(db, event_id)
    if not ev:
        raise ValueError("Evento não encontrado")
    if ev.status in _TERMINAL_STATUSES:
        raise ValueError("Evento já encerrado")

    old = ev.status
    ev.status = CompensationStatus.CANCELLED
    ev.decided_by_id = actor.id
    ev.decided_at = datetime.now(_BR)
    ev.decision_motivo = motivo
    if old == CompensationStatus.APPROVED:
        _revoke_credits_for_event(db, ev.id)

    _append_log(
        db,
        event_id=ev.id,
        actor_id=actor.id,
        action=CompensationLogAction.CANCELLED,
        from_status=old,
        to_status=ev.status,
        motivo=motivo,
    )

    db.commit()
    db.refresh(ev)
    return ev


def revert_compensation_event(db: Session, event_id: int, actor: User, motivo: str) -> CompensationEvent:
    ev = get_compensation_event(db, event_id)
    if not ev:
        raise ValueError("Evento não encontrado")
    if ev.status != CompensationStatus.APPROVED:
        raise ValueError("Somente eventos aprovados podem ser revertidos")

    old = ev.status
    ev.status = CompensationStatus.REVERTED
    ev.decided_by_id = actor.id
    ev.decided_at = datetime.now(_BR)
    ev.decision_motivo = motivo
    _revoke_credits_for_event(db, ev.id)

    _append_log(
        db,
        event_id=ev.id,
        actor_id=actor.id,
        action=CompensationLogAction.REVERTED,
        from_status=old,
        to_status=ev.status,
        motivo=motivo,
    )

    db.commit()
    db.refresh(ev)
    return ev
