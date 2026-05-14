from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.compensation_labels import compensation_display_label
from models.compensations import (
    CompensationEvent,
    CompensationEventParticipant,
    CompensationStatus,
    CompensationType,
    UserCompensation,
    UserCompensationStatus,
)
from models.user import User, UserRole
from schemas.compensations import CompensationEventCreate

_BR = ZoneInfo("America/Sao_Paulo")


def _ensure_relevant_occurrence_gate(approver: User, event: CompensationEvent) -> None:
    if event.event_type != CompensationType.RELEVANT_OCCURRENCE:
        return
    if approver.role not in {UserRole.ADMIN, UserRole.N90, UserRole.TAT_CMD}:
        raise ValueError("Ocorrência de grande relevância: aprovação restrita a N90/TAT_CMD (e ADMIN)")


def create_compensation_event(db: Session, creator: User, body: CompensationEventCreate) -> CompensationEvent:
    ids = list({int(x) for x in body.participant_user_ids})
    if not ids:
        raise ValueError("Selecione ao menos um envolvido")

    found = list(db.scalars(select(User).where(User.id.in_(ids))).all())
    if len(found) != len(ids):
        raise ValueError("Participante inexistente")

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
    db.commit()
    db.refresh(ev)
    return ev


def list_pending_compensation_events(db: Session) -> list[CompensationEvent]:
    return list(
        db.scalars(
            select(CompensationEvent)
            .options(selectinload(CompensationEvent.participants))
            .where(CompensationEvent.status == CompensationStatus.PENDING)
            .order_by(CompensationEvent.created_at.asc())
        ).all()
    )


def approve_compensation_event(db: Session, event_id: int, approver: User, motivo: str | None) -> CompensationEvent:
    ev = db.scalars(
        select(CompensationEvent)
        .options(selectinload(CompensationEvent.participants))
        .where(CompensationEvent.id == event_id)
    ).first()
    if not ev:
        raise ValueError("Evento não encontrado")
    if ev.status != CompensationStatus.PENDING:
        raise ValueError("Evento não está pendente")

    _ensure_relevant_occurrence_gate(approver, ev)

    ev.status = CompensationStatus.APPROVED
    ev.decided_by_id = approver.id
    ev.decided_at = datetime.now(_BR)
    ev.decision_motivo = motivo

    for p in ev.participants:
        exists = db.scalars(
            select(UserCompensation).where(
                UserCompensation.compensation_event_id == ev.id,
                UserCompensation.user_id == p.user_id,
            )
        ).first()
        if exists:
            continue
        db.add(
            UserCompensation(
                user_id=p.user_id,
                compensation_event_id=ev.id,
                status=UserCompensationStatus.AVAILABLE,
                display_label=compensation_display_label(ev.event_type),
            )
        )

    db.commit()
    db.refresh(ev)
    return ev


def reject_compensation_event(db: Session, event_id: int, approver: User, motivo: str) -> CompensationEvent:
    ev = db.scalars(select(CompensationEvent).where(CompensationEvent.id == event_id)).first()
    if not ev:
        raise ValueError("Evento não encontrado")
    if ev.status != CompensationStatus.PENDING:
        raise ValueError("Evento não está pendente")

    _ensure_relevant_occurrence_gate(approver, ev)

    ev.status = CompensationStatus.REJECTED
    ev.decided_by_id = approver.id
    ev.decided_at = datetime.now(_BR)
    ev.decision_motivo = motivo

    db.commit()
    db.refresh(ev)
    return ev
