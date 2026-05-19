import calendar
from collections import defaultdict
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from core.compensation_labels import compensation_display_label
from core.leave_booking_policy import (
    BOOKING_HINT,
    allowed_booking_month_keys,
    assert_leave_booking_allowed,
    today_br,
)
from models.compensations import CompensationEvent, CompensationStatus, UserCompensation, UserCompensationStatus
from models.leaves import LeaveApprovalLog, LeaveLogAction, LeaveRequest, LeaveStatus, LeaveType
from models.user import User
from schemas.leaves import LeaveRequestCreate

_BR = ZoneInfo("America/Sao_Paulo")

_ACTIVE_LEAVE_STATUSES = (LeaveStatus.PENDING, LeaveStatus.REVIEW, LeaveStatus.APPROVED)


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    return start, last


def _append_leave_log(
    db: Session,
    *,
    leave: LeaveRequest,
    actor_id: int,
    action: LeaveLogAction,
    from_status: LeaveStatus | None,
    to_status: LeaveStatus | None,
    motivo: str | None = None,
    details: str | None = None,
) -> None:
    db.add(
        LeaveApprovalLog(
            leave_request_id=leave.id,
            actor_id=actor_id,
            action=action,
            from_status=from_status,
            to_status=to_status,
            motivo=motivo,
            details=details,
        )
    )


def _count_user_monthly_folgas(db: Session, user_id: int, year: int, month: int, exclude_id: int | None = None) -> int:
    start, last = _month_bounds(year, month)
    stmt = (
        select(func.count())
        .select_from(LeaveRequest)
        .where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.leave_type == LeaveType.MONTHLY,
            LeaveRequest.leave_on >= start,
            LeaveRequest.leave_on <= last,
            LeaveRequest.status.in_(_ACTIVE_LEAVE_STATUSES),
        )
    )
    if exclude_id is not None:
        stmt = stmt.where(LeaveRequest.id != exclude_id)
    return int(db.scalar(stmt) or 0)


def _count_user_month_leaves(db: Session, user_id: int, year: int, month: int, exclude_id: int | None = None) -> int:
    start, last = _month_bounds(year, month)
    stmt = (
        select(func.count())
        .select_from(LeaveRequest)
        .where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.leave_on >= start,
            LeaveRequest.leave_on <= last,
            LeaveRequest.status.in_(_ACTIVE_LEAVE_STATUSES),
        )
    )
    if exclude_id is not None:
        stmt = stmt.where(LeaveRequest.id != exclude_id)
    return int(db.scalar(stmt) or 0)


def _count_day_leaves(db: Session, leave_on: date, exclude_id: int | None = None) -> int:
    stmt = select(func.count()).select_from(LeaveRequest).where(
        LeaveRequest.leave_on == leave_on,
        LeaveRequest.status.in_(_ACTIVE_LEAVE_STATUSES),
    )
    if exclude_id is not None:
        stmt = stmt.where(LeaveRequest.id != exclude_id)
    return int(db.scalar(stmt) or 0)


def _duplicate_active(db: Session, user_id: int, leave_on: date) -> bool:
    stmt = select(func.count()).select_from(LeaveRequest).where(
        LeaveRequest.user_id == user_id,
        LeaveRequest.leave_on == leave_on,
        LeaveRequest.status.in_(_ACTIVE_LEAVE_STATUSES),
    )
    return int(db.scalar(stmt) or 0) > 0


def create_leave_request(db: Session, actor: User, payload: LeaveRequestCreate) -> LeaveRequest:
    if _duplicate_active(db, actor.id, payload.leave_on):
        raise ValueError("Já existe solicitação ativa para este dia")

    assert_leave_booking_allowed(payload.leave_on)

    if payload.leave_type == LeaveType.MONTHLY and payload.user_compensation_id is not None:
        raise ValueError("Folga mensal não utiliza compensação vinculada")

    if payload.leave_type == LeaveType.DS:
        if payload.user_compensation_id is not None:
            raise ValueError("DS não utiliza crédito de compensação")

    if payload.leave_type == LeaveType.COMPENSATION:
        if payload.user_compensation_id is None:
            raise ValueError("Compensação obrigatória para este tipo de folga")
        uc = db.scalars(
            select(UserCompensation).where(UserCompensation.id == payload.user_compensation_id)
        ).first()
        if not uc or uc.user_id != actor.id:
            raise ValueError("Compensação inválida")
        if uc.status != UserCompensationStatus.AVAILABLE:
            raise ValueError("Compensação indisponível")

    year, month = payload.leave_on.year, payload.leave_on.month
    month_total = _count_user_month_leaves(db, actor.id, year, month)
    day_total = _count_day_leaves(db, payload.leave_on)

    reasons: list[str] = []
    if payload.leave_type == LeaveType.MONTHLY:
        if _count_user_monthly_folgas(db, actor.id, year, month) >= 1:
            reasons.append("Já existe folga mensal ativa neste mês")
    elif month_total + 1 > 2:
        reasons.append("Excedeu limite operacional mensal (máx. 2 folgas)")
    if day_total + 1 > 4:
        reasons.append("Efetivo reduzido no dia (acima de 4 policiais)")

    status = LeaveStatus.REVIEW if reasons else LeaveStatus.PENDING
    review_reason = "; ".join(reasons) if reasons else None

    row = LeaveRequest(
        user_id=actor.id,
        leave_on=payload.leave_on,
        leave_type=payload.leave_type,
        user_compensation_id=payload.user_compensation_id,
        status=status,
        review_reason=review_reason,
    )
    db.add(row)
    db.flush()

    details = f"Tipo={payload.leave_type.value}; Regras={review_reason or 'dentro dos parâmetros'}"
    _append_leave_log(
        db,
        leave=row,
        actor_id=actor.id,
        action=LeaveLogAction.CREATED,
        from_status=None,
        to_status=status,
        motivo="Solicitação registrada",
        details=details,
    )
    db.commit()
    db.refresh(row)
    return row


def approve_leave(db: Session, leave_id: int, approver: User, motivo: str | None) -> LeaveRequest:
    row = db.scalars(select(LeaveRequest).where(LeaveRequest.id == leave_id)).first()
    if not row:
        raise ValueError("Solicitação não encontrada")
    if row.status not in (LeaveStatus.PENDING, LeaveStatus.REVIEW):
        raise ValueError("Status não permite aprovação")

    prev = row.status
    row.status = LeaveStatus.APPROVED
    row.decided_by_id = approver.id
    row.decided_at = datetime.now(_BR)
    row.decision_motivo = motivo

    if row.leave_type == LeaveType.COMPENSATION and row.user_compensation_id:
        uc = db.scalars(
            select(UserCompensation).where(UserCompensation.id == row.user_compensation_id)
        ).first()
        if uc and uc.status == UserCompensationStatus.AVAILABLE:
            uc.status = UserCompensationStatus.USED
            uc.used_leave_request_id = row.id
            uc.used_at = datetime.now(_BR)

    _append_leave_log(
        db,
        leave=row,
        actor_id=approver.id,
        action=LeaveLogAction.APPROVED,
        from_status=prev,
        to_status=LeaveStatus.APPROVED,
        motivo=motivo,
        details=None,
    )
    db.commit()
    db.refresh(row)
    return row


def reject_leave(db: Session, leave_id: int, approver: User, motivo: str) -> LeaveRequest:
    row = db.scalars(select(LeaveRequest).where(LeaveRequest.id == leave_id)).first()
    if not row:
        raise ValueError("Solicitação não encontrada")
    if row.status not in (LeaveStatus.PENDING, LeaveStatus.REVIEW):
        raise ValueError("Status não permite rejeição")

    prev = row.status
    row.status = LeaveStatus.REJECTED
    row.decided_by_id = approver.id
    row.decided_at = datetime.now(_BR)
    row.decision_motivo = motivo

    _append_leave_log(
        db,
        leave=row,
        actor_id=approver.id,
        action=LeaveLogAction.REJECTED,
        from_status=prev,
        to_status=LeaveStatus.REJECTED,
        motivo=motivo,
        details=None,
    )
    db.commit()
    db.refresh(row)
    return row


def _release_compensation_credit_for_leave(db: Session, row: LeaveRequest) -> None:
    if row.leave_type != LeaveType.COMPENSATION or not row.user_compensation_id:
        return
    uc = db.scalars(
        select(UserCompensation).where(UserCompensation.id == row.user_compensation_id)
    ).first()
    if not uc:
        return
    if uc.status == UserCompensationStatus.USED and uc.used_leave_request_id == row.id:
        uc.status = UserCompensationStatus.AVAILABLE
        uc.used_leave_request_id = None
        uc.used_at = None


def cancel_leave(db: Session, leave_id: int, actor: User, motivo: str | None) -> LeaveRequest:
    row = db.scalars(select(LeaveRequest).where(LeaveRequest.id == leave_id)).first()
    if not row:
        raise ValueError("Solicitação não encontrada")
    if row.user_id != actor.id:
        raise ValueError("Somente o solicitante pode cancelar")
    if row.status not in _ACTIVE_LEAVE_STATUSES:
        raise ValueError("Esta solicitação não pode mais ser cancelada")
    if row.status == LeaveStatus.APPROVED and not (motivo and motivo.strip()):
        raise ValueError("Informe o motivo do cancelamento (ex.: remarcar para outro dia)")

    prev = row.status
    row.status = LeaveStatus.CANCELLED
    row.decision_motivo = motivo.strip() if motivo else motivo

    if prev == LeaveStatus.APPROVED:
        _release_compensation_credit_for_leave(db, row)

    _append_leave_log(
        db,
        leave=row,
        actor_id=actor.id,
        action=LeaveLogAction.CANCELLED,
        from_status=prev,
        to_status=LeaveStatus.CANCELLED,
        motivo=motivo,
        details=None,
    )
    db.commit()
    db.refresh(row)
    return row


def list_pending_leaves(db: Session) -> list[LeaveRequest]:
    return list(
        db.scalars(
            select(LeaveRequest)
            .options(joinedload(LeaveRequest.user))
            .where(LeaveRequest.status.in_((LeaveStatus.PENDING, LeaveStatus.REVIEW)))
            .order_by(LeaveRequest.leave_on.asc(), LeaveRequest.created_at.asc())
        ).all()
    )


def build_calendar(
    db: Session,
    *,
    year: int,
    month: int,
    viewer: User,
    is_command: bool,
) -> dict:
    start, last = _month_bounds(year, month)
    rows = list(
        db.scalars(
            select(LeaveRequest)
            .options(joinedload(LeaveRequest.user))
            .where(
                LeaveRequest.leave_on >= start,
                LeaveRequest.leave_on <= last,
                LeaveRequest.status.in_(_ACTIVE_LEAVE_STATUSES),
            )
        ).all()
    )

    by_day: dict[date, list[LeaveRequest]] = defaultdict(list)
    for r in rows:
        by_day[r.leave_on].append(r)

    def operational_rank(lt: LeaveType) -> int:
        if lt == LeaveType.MONTHLY:
            return 1
        if lt == LeaveType.DS:
            return 2
        return 3

    days_out: list[dict] = []
    d = start
    while d <= last:
        bucket = by_day.get(d, [])
        entries: list[dict] = []
        for r in sorted(
            bucket,
            key=lambda x: (operational_rank(x.leave_type), x.user.display_order, x.user.nome_guerra),
        ):
            u = r.user
            entries.append(
                {
                    "id": r.id,
                    "leave_on": r.leave_on,
                    "user_id": r.user_id,
                    "patente": u.patente,
                    "nome_guerra": u.nome_guerra,
                    "display_order": u.display_order,
                    "leave_type": r.leave_type,
                    "status": r.status,
                    "operational_rank": operational_rank(r.leave_type),
                }
            )
        active_count = len(bucket)
        days_out.append(
            {
                "date": d,
                "entries": entries,
                "active_count": active_count,
                "is_critical": active_count >= 4,
            }
        )
        d = date.fromordinal(d.toordinal() + 1)

    my_pending = int(
        db.scalar(
            select(func.count())
            .select_from(LeaveRequest)
            .where(
                LeaveRequest.user_id == viewer.id,
                LeaveRequest.status.in_((LeaveStatus.PENDING, LeaveStatus.REVIEW)),
            )
        )
        or 0
    )

    summary: dict = {"my_pending_count": my_pending}
    if is_command:
        cmd_pending = int(
            db.scalar(
                select(func.count())
                .select_from(LeaveRequest)
                .where(LeaveRequest.status.in_((LeaveStatus.PENDING, LeaveStatus.REVIEW)))
            )
            or 0
        )
        comp_pending = int(
            db.scalar(
                select(func.count())
                .select_from(CompensationEvent)
                .where(CompensationEvent.status == CompensationStatus.PENDING)
            )
            or 0
        )
        critical_days = [day["date"] for day in days_out if day["is_critical"]]
        summary["command_pending_leaves"] = cmd_pending
        summary["command_pending_compensations"] = comp_pending
        summary["critical_days"] = critical_days

    ref = today_br()
    allowed = sorted(allowed_booking_month_keys(ref))
    booking_policy = {
        "reference_date": ref,
        "allowed_year_months": [{"year": y, "month": m} for y, m in allowed],
        "operational_hint": BOOKING_HINT,
    }

    return {
        "year": year,
        "month": month,
        "days": days_out,
        "summary": summary,
        "booking_policy": booking_policy,
    }


def list_available_compensation_credits(db: Session, user_id: int) -> list[dict]:
    stmt = (
        select(UserCompensation, CompensationEvent)
        .join(CompensationEvent, UserCompensation.compensation_event_id == CompensationEvent.id)
        .where(
            UserCompensation.user_id == user_id,
            UserCompensation.status == UserCompensationStatus.AVAILABLE,
            CompensationEvent.status == CompensationStatus.APPROVED,
        )
        .order_by(UserCompensation.created_at.desc())
    )
    out: list[dict] = []
    for uc, ev in db.execute(stmt).all():
        br_dt = ev.created_at
        if br_dt.tzinfo is None:
            br_dt = br_dt.replace(tzinfo=_BR)
        else:
            br_dt = br_dt.astimezone(_BR)
        event_date = br_dt.date()
        label = (uc.display_label or "").strip() or compensation_display_label(ev.event_type)
        desc = ev.motivo.strip()
        if len(desc) > 360:
            desc = desc[:357] + "..."
        out.append(
            {
                "id": uc.id,
                "type": ev.event_type,
                "label": label,
                "event_date": event_date,
                "description": desc,
            }
        )
    return out
