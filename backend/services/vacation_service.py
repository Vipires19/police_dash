import calendar
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from auth.dependencies import APPROVER_ROLES
from core.absence_labels import (
    OPERATIONAL_RANK,
    absence_display_label,
    is_restricted_absence,
)
from models.user import User
from models.vacation import (
    VacationApprovalLog,
    VacationLogAction,
    VacationRequest,
    VacationStatus,
    VacationType,
)
from schemas.vacation import ALLOWED_VACATION_DURATIONS, VacationRequestCreate, VacationRequestUpdate

_BR = ZoneInfo("America/Sao_Paulo")
_MAX_SIMULTANEOUS_PER_DAY = 2
_ACTIVE_VACATION_STATUSES = (VacationStatus.PENDING, VacationStatus.REVIEW, VacationStatus.APPROVED)
RESTRICTED_FOR_SIMULTANEITY = (VacationType.FERIAS, VacationType.LP)


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


def _count_day_restricted_absences(db: Session, day: date, exclude_id: int | None = None) -> int:
    stmt = select(func.count()).select_from(VacationRequest).where(
        VacationRequest.start_date <= day,
        VacationRequest.end_date >= day,
        VacationRequest.status.in_(_ACTIVE_VACATION_STATUSES),
        VacationRequest.vacation_type.in_(tuple(RESTRICTED_FOR_SIMULTANEITY)),
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
    absence_type: VacationType,
    exclude_id: int | None = None,
) -> list[str]:
    if not is_restricted_absence(absence_type):
        return []
    reasons: list[str] = []
    for day in _iter_days(start, end):
        count = _count_day_restricted_absences(db, day, exclude_id)
        if count + 1 > _MAX_SIMULTANEOUS_PER_DAY:
            reasons.append(
                f"{day.strftime('%d/%m/%Y')}: simultaneidade operacional (máx. {_MAX_SIMULTANEOUS_PER_DAY} policiais)"
            )
    return reasons


def _validate_absence_period(
    absence_type: VacationType,
    start: date,
    end: date,
) -> int:
    if end < start:
        raise ValueError("Data final deve ser igual ou posterior à inicial")
    total = _inclusive_days(start, end)
    if is_restricted_absence(absence_type):
        if total not in ALLOWED_VACATION_DURATIONS:
            raise ValueError("Férias e LP: período permitido apenas de 15 ou 30 dias corridos")
    elif total < 1:
        raise ValueError("Período inválido")
    return total


def create_vacation_request(db: Session, actor: User, payload: VacationRequestCreate) -> VacationRequest:
    total = _validate_absence_period(payload.vacation_type, payload.start_date, payload.end_date)

    if _user_overlap_active(db, actor.id, payload.start_date, payload.end_date):
        raise ValueError("Já existe solicitação ativa que sobrepõe este período")

    review_reasons = _simultaneity_review_reasons(
        db, payload.start_date, payload.end_date, payload.vacation_type
    )
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
        notes=payload.notes,
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
    if row.status not in _ACTIVE_VACATION_STATUSES:
        raise ValueError("Esta solicitação não pode mais ser cancelada")
    if row.status == VacationStatus.APPROVED and not (reason and reason.strip()):
        raise ValueError("Informe o motivo do cancelamento")

    prev = row.status
    row.status = VacationStatus.CANCELLED
    row.decision_reason = reason.strip() if reason else reason

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


def revert_vacation(db: Session, vacation_id: int, approver: User, reason: str) -> VacationRequest:
    if approver.role not in APPROVER_ROLES:
        raise ValueError("Sem permissão para reverter afastamento")
    row = db.scalars(select(VacationRequest).where(VacationRequest.id == vacation_id)).first()
    if not row:
        raise ValueError("Solicitação não encontrada")
    if row.status != VacationStatus.APPROVED:
        raise ValueError("Somente afastamentos aprovados podem ser revertidos")
    if not reason.strip():
        raise ValueError("Motivo da reversão é obrigatório")

    prev = row.status
    row.status = VacationStatus.REVERTED
    row.approved_by_id = approver.id
    row.approved_at = datetime.now(_BR)
    row.decision_reason = reason.strip()

    _append_vacation_log(
        db,
        vacation=row,
        actor_id=approver.id,
        action=VacationLogAction.REVERTED,
        from_status=prev,
        to_status=VacationStatus.REVERTED,
        reason=reason.strip(),
    )
    db.commit()
    db.refresh(row)
    return row


def update_vacation_request(
    db: Session,
    vacation_id: int,
    actor: User,
    payload: VacationRequestUpdate,
) -> VacationRequest:
    row = db.scalars(select(VacationRequest).where(VacationRequest.id == vacation_id)).first()
    if not row:
        raise ValueError("Solicitação não encontrada")

    is_command = actor.role in APPROVER_ROLES
    if row.user_id != actor.id and not is_command:
        raise ValueError("Sem permissão para editar")
    if row.status not in (VacationStatus.PENDING, VacationStatus.REVIEW) and not is_command:
        raise ValueError("Somente pendências podem ser editadas pelo solicitante")
    if row.status in (VacationStatus.CANCELLED, VacationStatus.REJECTED, VacationStatus.REVERTED):
        raise ValueError("Registro encerrado não pode ser editado")

    new_type = payload.vacation_type if payload.vacation_type is not None else row.vacation_type
    new_start = payload.start_date if payload.start_date is not None else row.start_date
    new_end = payload.end_date if payload.end_date is not None else row.end_date
    total = _validate_absence_period(new_type, new_start, new_end)

    if _user_overlap_active(db, row.user_id, new_start, new_end, exclude_id=row.id):
        raise ValueError("Já existe solicitação ativa que sobrepõe este período")

    review_reasons = _simultaneity_review_reasons(db, new_start, new_end, new_type, exclude_id=row.id)
    prev = row.status
    row.vacation_type = new_type
    row.start_date = new_start
    row.end_date = new_end
    row.total_days = total
    if payload.notes is not None:
        row.notes = payload.notes
    if review_reasons:
        row.status = VacationStatus.REVIEW
        row.review_reason = "; ".join(review_reasons)
    elif row.status == VacationStatus.REVIEW:
        row.status = VacationStatus.PENDING
        row.review_reason = None

    _append_vacation_log(
        db,
        vacation=row,
        actor_id=actor.id,
        action=VacationLogAction.UPDATED,
        from_status=prev,
        to_status=row.status,
        reason=f"Atualizado para {absence_display_label(new_type)} ({total}d)",
    )
    db.commit()
    db.refresh(row)
    return row


def list_absence_requests(
    db: Session,
    *,
    status: VacationStatus | None = None,
    absence_type: VacationType | None = None,
    user_id: int | None = None,
    year: int | None = None,
    month: int | None = None,
) -> list[VacationRequest]:
    stmt = select(VacationRequest).options(joinedload(VacationRequest.user))
    if status is not None:
        stmt = stmt.where(VacationRequest.status == status)
    if absence_type is not None:
        stmt = stmt.where(VacationRequest.vacation_type == absence_type)
    if user_id is not None:
        stmt = stmt.where(VacationRequest.user_id == user_id)
    if year is not None and month is not None:
        start, last = _month_bounds(year, month)
        stmt = stmt.where(
            VacationRequest.end_date >= start,
            VacationRequest.start_date <= last,
        )
    stmt = stmt.order_by(VacationRequest.start_date.desc(), VacationRequest.created_at.desc())
    return list(db.scalars(stmt).all())


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
        return OPERATIONAL_RANK.get(vt, 99)

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
                    "notes": r.notes,
                    "operational_rank": operational_rank(r.vacation_type),
                }
            )
        active_count = len(unique_rows)
        restricted_count = sum(
            1 for r in unique_rows if is_restricted_absence(r.vacation_type)
        )
        days_out.append(
            {
                "date": d,
                "entries": entries,
                "active_count": active_count,
                "is_critical": restricted_count >= _MAX_SIMULTANEOUS_PER_DAY,
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
