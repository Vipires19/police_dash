import calendar
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.user import User
from models.vacation import (
    VacationApprovalLog,
    VacationLogAction,
    VacationRequest,
    VacationStatus,
    VacationType,
)
from schemas.vacation import ALLOWED_VACATION_DURATIONS, VacationRequestCreate

_BR = ZoneInfo("America/Sao_Paulo")
_MAX_SIMULTANEOUS_PER_DAY = 2
_ACTIVE_VACATION_STATUSES = (VacationStatus.PENDING, VacationStatus.REVIEW, VacationStatus.APPROVED)


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    return start, last


def _inclusive_days(start: date, end: date) -> int:
    return (end - start).days + 1


def _iter_days(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _append_vacation_log(
    db: Session,
    *,
    vacation: VacationRequest,
    actor_id: int,
    action: VacationLogAction,
    from_status: VacationStatus | None,
    to_status: VacationStatus | None,
    reason: str | None = None,
) -> None:
    db.add(
        VacationApprovalLog(
            vacation_request_id=vacation.id,
            actor_id=actor_id,
            action=action,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
        )
    )


def _count_day_vacations(db: Session, day: date, exclude_id: int | None = None) -> int:
    stmt = select(func.count()).select_from(VacationRequest).where(
        VacationRequest.start_date <= day,
        VacationRequest.end_date >= day,
        VacationRequest.status.in_(_ACTIVE_VACATION_STATUSES),
    )
    if exclude_id is not None:
        stmt = stmt.where(VacationRequest.id != exclude_id)
    return int(db.scalar(stmt) or 0)


def _user_overlap_active(
    db: Session,
    user_id: int,
    start: date,
    end: date,
    exclude_id: int | None = None,
) -> bool:
    stmt = select(func.count()).select_from(VacationRequest).where(
        VacationRequest.user_id == user_id,
        VacationRequest.start_date <= end,
        VacationRequest.end_date >= start,
        VacationRequest.status.in_(_ACTIVE_VACATION_STATUSES),
    )
    if exclude_id is not None:
        stmt = stmt.where(VacationRequest.id != exclude_id)
    return int(db.scalar(stmt) or 0) > 0


def _simultaneity_review_reasons(
    db: Session,
    start: date,
    end: date,
    exclude_id: int | None = None,
) -> list[str]:
    reasons: list[str] = []
    for day in _iter_days(start, end):
        count = _count_day_vacations(db, day, exclude_id)
        if count + 1 > _MAX_SIMULTANEOUS_PER_DAY:
            reasons.append(
                f"{day.strftime('%d/%m/%Y')}: simultaneidade operacional (máx. {_MAX_SIMULTANEOUS_PER_DAY} policiais)"
            )
    return reasons


def create_vacation_request(db: Session, actor: User, payload: VacationRequestCreate) -> VacationRequest:
    total = _inclusive_days(payload.start_date, payload.end_date)
    if total not in ALLOWED_VACATION_DURATIONS:
        raise ValueError("Período permitido apenas de 15 ou 30 dias corridos")

    if _user_overlap_active(db, actor.id, payload.start_date, payload.end_date):
        raise ValueError("Já existe solicitação ativa que sobrepõe este período")

    review_reasons = _simultaneity_review_reasons(db, payload.start_date, payload.end_date)
    status = VacationStatus.REVIEW if review_reasons else VacationStatus.PENDING
    review_reason = "; ".join(review_reasons) if review_reasons else None

    row = VacationRequest(
        user_id=actor.id,
        vacation_type=payload.vacation_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        total_days=total,
        status=status,
        review_reason=review_reason,
    )
    db.add(row)
    db.flush()

    details = (
        f"Tipo={payload.vacation_type.value}; Dias={total}; "
        f"Regras={review_reason or 'dentro dos parâmetros'}"
    )
    _append_vacation_log(
        db,
        vacation=row,
        actor_id=actor.id,
        action=VacationLogAction.CREATED,
        from_status=None,
        to_status=status,
        reason=details,
    )
    db.commit()
    db.refresh(row)
    return row


def approve_vacation(db: Session, vacation_id: int, approver: User, reason: str | None) -> VacationRequest:
    row = db.scalars(select(VacationRequest).where(VacationRequest.id == vacation_id)).first()
    if not row:
        raise ValueError("Solicitação não encontrada")
    if row.status not in (VacationStatus.PENDING, VacationStatus.REVIEW):
        raise ValueError("Status não permite aprovação")

    prev = row.status
    row.status = VacationStatus.APPROVED
    row.approved_by_id = approver.id
    row.approved_at = datetime.now(_BR)
    row.decision_reason = reason

    _append_vacation_log(
        db,
        vacation=row,
        actor_id=approver.id,
        action=VacationLogAction.APPROVED,
        from_status=prev,
        to_status=VacationStatus.APPROVED,
        reason=reason,
    )
    db.commit()
    db.refresh(row)
    return row


def reject_vacation(db: Session, vacation_id: int, approver: User, reason: str) -> VacationRequest:
    row = db.scalars(select(VacationRequest).where(VacationRequest.id == vacation_id)).first()
    if not row:
        raise ValueError("Solicitação não encontrada")
    if row.status not in (VacationStatus.PENDING, VacationStatus.REVIEW):
        raise ValueError("Status não permite rejeição")

    prev = row.status
    row.status = VacationStatus.REJECTED
    row.approved_by_id = approver.id
    row.approved_at = datetime.now(_BR)
    row.decision_reason = reason

    _append_vacation_log(
        db,
        vacation=row,
        actor_id=approver.id,
        action=VacationLogAction.REJECTED,
        from_status=prev,
        to_status=VacationStatus.REJECTED,
        reason=reason,
    )
    db.commit()
    db.refresh(row)
    return row


def cancel_vacation(db: Session, vacation_id: int, actor: User, reason: str | None) -> VacationRequest:
    row = db.scalars(select(VacationRequest).where(VacationRequest.id == vacation_id)).first()
    if not row:
        raise ValueError("Solicitação não encontrada")
    if row.user_id != actor.id:
        raise ValueError("Somente o solicitante pode cancelar")
    if row.status not in (VacationStatus.PENDING, VacationStatus.REVIEW):
        raise ValueError("Somente pendências em análise podem ser canceladas pelo policial")

    prev = row.status
    row.status = VacationStatus.CANCELLED
    row.decision_reason = reason

    _append_vacation_log(
        db,
        vacation=row,
        actor_id=actor.id,
        action=VacationLogAction.CANCELLED,
        from_status=prev,
        to_status=VacationStatus.CANCELLED,
        reason=reason,
    )
    db.commit()
    db.refresh(row)
    return row


def list_pending_vacations(db: Session) -> list[VacationRequest]:
    return list(
        db.scalars(
            select(VacationRequest)
            .options(joinedload(VacationRequest.user))
            .where(VacationRequest.status.in_((VacationStatus.PENDING, VacationStatus.REVIEW)))
            .order_by(VacationRequest.start_date.asc(), VacationRequest.created_at.asc())
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
            select(VacationRequest)
            .options(joinedload(VacationRequest.user))
            .where(
                VacationRequest.end_date >= start,
                VacationRequest.start_date <= last,
                VacationRequest.status.in_(_ACTIVE_VACATION_STATUSES),
            )
        ).all()
    )

    def operational_rank(vt: VacationType) -> int:
        return 1 if vt == VacationType.FERIAS else 2

    by_day: dict[date, list[VacationRequest]] = defaultdict(list)
    for r in rows:
        day_start = max(r.start_date, start)
        day_end = min(r.end_date, last)
        for d in _iter_days(day_start, day_end):
            by_day[d].append(r)

    days_out: list[dict] = []
    d = start
    while d <= last:
        bucket = by_day.get(d, [])
        seen: set[int] = set()
        unique_rows: list[VacationRequest] = []
        for r in bucket:
            if r.id not in seen:
                seen.add(r.id)
                unique_rows.append(r)

        entries: list[dict] = []
        for r in sorted(
            unique_rows,
            key=lambda x: (operational_rank(x.vacation_type), x.user.display_order, x.user.nome_guerra),
        ):
            u = r.user
            entries.append(
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "patente": u.patente,
                    "nome_guerra": u.nome_guerra,
                    "display_order": u.display_order,
                    "vacation_type": r.vacation_type,
                    "status": r.status,
                    "start_date": r.start_date,
                    "end_date": r.end_date,
                    "total_days": r.total_days,
                    "operational_rank": operational_rank(r.vacation_type),
                }
            )
        active_count = len(unique_rows)
        days_out.append(
            {
                "date": d,
                "entries": entries,
                "active_count": active_count,
                "is_critical": active_count >= _MAX_SIMULTANEOUS_PER_DAY,
            }
        )
        d = date.fromordinal(d.toordinal() + 1)

    my_pending = int(
        db.scalar(
            select(func.count())
            .select_from(VacationRequest)
            .where(
                VacationRequest.user_id == viewer.id,
                VacationRequest.status.in_((VacationStatus.PENDING, VacationStatus.REVIEW)),
            )
        )
        or 0
    )

    summary: dict = {"my_pending_count": my_pending}
    if is_command:
        today = datetime.now(_BR).date()
        cmd_pending = int(
            db.scalar(
                select(func.count())
                .select_from(VacationRequest)
                .where(VacationRequest.status.in_((VacationStatus.PENDING, VacationStatus.REVIEW)))
            )
            or 0
        )
        away = int(
            db.scalar(
                select(func.count())
                .select_from(VacationRequest)
                .where(
                    VacationRequest.status == VacationStatus.APPROVED,
                    VacationRequest.start_date <= today,
                    VacationRequest.end_date >= today,
                )
            )
            or 0
        )
        critical_days = [day["date"] for day in days_out if day["is_critical"]]
        summary["command_pending_vacations"] = cmd_pending
        summary["critical_days"] = critical_days
        summary["currently_away_count"] = away

    return {
        "year": year,
        "month": month,
        "days": days_out,
        "summary": summary,
    }
