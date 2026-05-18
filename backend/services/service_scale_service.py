from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.leaves import LeaveApprovalLog, LeaveLogAction, LeaveRequest, LeaveStatus
from models.service_scale import (
    ScaleLog,
    ScaleLogAction,
    ScaleModality,
    ScaleStatus,
    ScaleTeam,
    ScaleTeamMember,
    ServiceScale,
)
from models.user import User, UserRole, UserStatus
from models.vacation import (
    VacationApprovalLog,
    VacationLogAction,
    VacationRequest,
    VacationStatus,
    VacationType,
)
from models.vehicle import Vehicle, VehicleModalidade, VehicleStatus
from schemas.service_scale import (
    MAX_FT_MEMBERS,
    MAX_ROCAM_MEMBERS,
    ScaleTeamCreate,
    ScaleTeamMemberInput,
    ScaleTeamMembersUpdate,
    ScaleTeamUpdate,
    ServiceScaleCreate,
    ServiceScaleUpdate,
)

_BR = ZoneInfo("America/Sao_Paulo")
_ACTIVE_LEAVE = (LeaveStatus.PENDING, LeaveStatus.REVIEW, LeaveStatus.APPROVED)
_ACTIVE_VACATION = (VacationStatus.PENDING, VacationStatus.REVIEW, VacationStatus.APPROVED)


def _operational_rank(role: UserRole) -> int:
    order = {
        UserRole.ADMIN: 0,
        UserRole.N90: 1,
        UserRole.TAT_CMD: 2,
        UserRole.BRACAL: 3,
        UserRole.ESTAGIO: 4,
    }
    return order.get(role, 99)


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    return start, last


def _append_scale_log(
    db: Session,
    *,
    scale_id: int,
    actor_id: int,
    action: ScaleLogAction,
    description: str,
) -> None:
    db.add(
        ScaleLog(
            service_scale_id=scale_id,
            actor_id=actor_id,
            action_type=action,
            description=description,
        )
    )


def _scale_detail_load_options():
    return (
        joinedload(ServiceScale.teams).joinedload(ScaleTeam.members).joinedload(ScaleTeamMember.user),
        joinedload(ServiceScale.teams).joinedload(ScaleTeam.vehicle),
        joinedload(ServiceScale.teams)
        .joinedload(ScaleTeam.members)
        .joinedload(ScaleTeamMember.assigned_vehicle),
        joinedload(ServiceScale.created_by),
    )


def _load_scale(db: Session, scale_id: int) -> ServiceScale | None:
    return db.scalars(
        select(ServiceScale)
        .where(ServiceScale.id == scale_id)
        .options(*_scale_detail_load_options())
    ).unique().first()


def _load_scale_by_date(db: Session, scale_date: date) -> ServiceScale | None:
    return db.scalars(
        select(ServiceScale)
        .where(ServiceScale.scale_date == scale_date)
        .options(*_scale_detail_load_options())
    ).unique().first()


def _validate_vehicle(modality: ScaleModality, vehicle_id: int | None, db: Session) -> Vehicle | None:
    if modality == ScaleModality.ROCAM:
        if vehicle_id is not None:
            raise ValueError("Equipe ROCAM não possui viatura principal")
        return None
    if vehicle_id is None:
        raise ValueError("Viatura FT é obrigatória")
    v = db.get(Vehicle, vehicle_id)
    if not v:
        raise ValueError("Viatura não encontrada")
    if v.status != VehicleStatus.OPERANDO:
        raise ValueError("Somente viaturas em operação podem ser escaladas")
    if v.modalidade != VehicleModalidade.FT:
        raise ValueError("Viatura incompatível com modalidade FT")
    return v


def _validate_assigned_vehicle(vehicle_id: int | None, db: Session) -> Vehicle | None:
    if vehicle_id is None:
        return None
    v = db.get(Vehicle, vehicle_id)
    if not v:
        raise ValueError("Moto/viatura individual não encontrada")
    if v.status != VehicleStatus.OPERANDO:
        raise ValueError("Somente viaturas em operação podem ser vinculadas")
    if v.modalidade != VehicleModalidade.ROCAM:
        raise ValueError("Viatura individual deve ser ROCAM")
    return v


def _member_limit(modality: ScaleModality) -> int:
    return MAX_FT_MEMBERS if modality == ScaleModality.FT else MAX_ROCAM_MEMBERS


def _validate_members(modality: ScaleModality, members: list[ScaleTeamMemberInput]) -> None:
    limit = _member_limit(modality)
    if not members:
        raise ValueError("Informe ao menos um policial na equipe")
    if len(members) > limit:
        raise ValueError(f"Máximo de {limit} policiais para {modality.value}")
    ids = [m.user_id for m in members]
    if len(ids) != len(set(ids)):
        raise ValueError("Policiais duplicados na equipe")
    if modality == ScaleModality.ROCAM:
        moto_ids = [m.assigned_vehicle_id for m in members]
        if any(mid is None for mid in moto_ids):
            raise ValueError("Cada policial ROCAM deve ter uma moto vinculada")
        if len(moto_ids) != len(set(moto_ids)):
            raise ValueError("Motos duplicadas na equipe ROCAM")


def _gather_scale_usage(
    scale: ServiceScale, *, exclude_team_id: int | None = None
) -> tuple[set[int], set[int], set[int]]:
    used_ft_vehicles: set[int] = set()
    used_motos: set[int] = set()
    used_users: set[int] = set()
    for team in scale.teams:
        if exclude_team_id is not None and team.id == exclude_team_id:
            continue
        if team.modality == ScaleModality.FT and team.vehicle_id:
            used_ft_vehicles.add(team.vehicle_id)
        for member in team.members:
            used_users.add(member.user_id)
            if member.assigned_vehicle_id:
                used_motos.add(member.assigned_vehicle_id)
    return used_ft_vehicles, used_motos, used_users


def _validate_scale_uniqueness(
    scale: ServiceScale,
    *,
    exclude_team_id: int | None,
    modality: ScaleModality,
    vehicle_id: int | None,
    members: list[ScaleTeamMemberInput],
) -> None:
    used_ft, used_motos, used_users = _gather_scale_usage(scale, exclude_team_id=exclude_team_id)
    for member in members:
        if member.user_id in used_users:
            raise ValueError("Policial já escalado em outra equipe neste dia")
    if modality == ScaleModality.FT and vehicle_id and vehicle_id in used_ft:
        raise ValueError("Viatura já utilizada em outra equipe FT desta escala")
    for member in members:
        if member.assigned_vehicle_id and member.assigned_vehicle_id in used_motos:
            raise ValueError("Moto ROCAM já vinculada a outro policial nesta escala")


def _cancel_leaves_for_user_on_date(db: Session, user_id: int, day: date, actor_id: int) -> int:
    rows = db.scalars(
        select(LeaveRequest).where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.leave_on == day,
            LeaveRequest.status.in_(_ACTIVE_LEAVE),
        )
    ).all()
    count = 0
    reason = f"Cancelado automaticamente: escalado em serviço em {day.strftime('%d/%m/%Y')}"
    for row in rows:
        prev = row.status
        row.status = LeaveStatus.CANCELLED
        row.decision_motivo = reason
        row.decided_by_id = actor_id
        row.decided_at = datetime.now(_BR)
        db.add(
            LeaveApprovalLog(
                leave_request_id=row.id,
                actor_id=actor_id,
                action=LeaveLogAction.CANCELLED,
                from_status=prev,
                to_status=LeaveStatus.CANCELLED,
                motivo=reason,
                details="Cancelamento operacional por escala de serviço",
            )
        )
        count += 1
    return count


def _cancel_vacations_for_user_on_date(db: Session, user_id: int, day: date, actor_id: int) -> int:
    rows = db.scalars(
        select(VacationRequest).where(
            VacationRequest.user_id == user_id,
            VacationRequest.start_date <= day,
            VacationRequest.end_date >= day,
            VacationRequest.status.in_(_ACTIVE_VACATION),
        )
    ).all()
    count = 0
    reason = f"Cancelado automaticamente: escalado em serviço em {day.strftime('%d/%m/%Y')}"
    for row in rows:
        prev = row.status
        row.status = VacationStatus.CANCELLED
        row.decision_reason = reason
        row.approved_by_id = actor_id
        row.approved_at = datetime.now(_BR)
        db.add(
            VacationApprovalLog(
                vacation_request_id=row.id,
                actor_id=actor_id,
                action=VacationLogAction.CANCELLED,
                from_status=prev,
                to_status=VacationStatus.CANCELLED,
                reason=reason,
            )
        )
        count += 1
    return count


def _apply_absence_cancellations(
    db: Session, scale_date: date, user_ids: list[int], actor_id: int
) -> list[str]:
    notes: list[str] = []
    for uid in user_ids:
        lc = _cancel_leaves_for_user_on_date(db, uid, scale_date, actor_id)
        vc = _cancel_vacations_for_user_on_date(db, uid, scale_date, actor_id)
        if lc or vc:
            u = db.get(User, uid)
            label = f"{u.patente} {u.nome_guerra}" if u else str(uid)
            parts = []
            if lc:
                parts.append(f"{lc} folga(s)")
            if vc:
                parts.append(f"{vc} afastamento(s)")
            notes.append(f"{label}: cancelou {' e '.join(parts)}")
    return notes


def _set_team_members(
    db: Session,
    team: ScaleTeam,
    members: list[ScaleTeamMemberInput],
    scale_date: date,
    actor_id: int,
) -> list[str]:
    _validate_members(team.modality, members)
    for m in members:
        u = db.get(User, m.user_id)
        if not u or u.status != UserStatus.APPROVED or not u.is_active:
            raise ValueError("Policial inválido ou inativo")
        if team.modality == ScaleModality.ROCAM:
            _validate_assigned_vehicle(m.assigned_vehicle_id, db)
    team.members.clear()
    for m in members:
        assigned_id = m.assigned_vehicle_id if team.modality == ScaleModality.ROCAM else None
        team.members.append(
            ScaleTeamMember(
                user_id=m.user_id,
                assigned_vehicle_id=assigned_id,
                role_label=m.role_label,
            )
        )
    return _apply_absence_cancellations(db, scale_date, [m.user_id for m in members], actor_id)


def build_staff_roster(db: Session, day: date) -> list[dict]:
    users = db.scalars(
        select(User)
        .where(User.status == UserStatus.APPROVED, User.is_active.is_(True))
        .order_by(User.display_order, User.nome_guerra)
    ).all()
    leaves = db.scalars(
        select(LeaveRequest).where(
            LeaveRequest.leave_on == day,
            LeaveRequest.status.in_(_ACTIVE_LEAVE),
        )
    ).all()
    vacations = db.scalars(
        select(VacationRequest).where(
            VacationRequest.start_date <= day,
            VacationRequest.end_date >= day,
            VacationRequest.status.in_(_ACTIVE_VACATION),
        )
    ).all()
    leave_by_user = {r.user_id: r for r in leaves}
    vac_by_user: dict[int, list[VacationRequest]] = {}
    for v in vacations:
        vac_by_user.setdefault(v.user_id, []).append(v)

    roster: list[dict] = []
    for u in users:
        absences: list[dict] = []
        if u.id in leave_by_user:
            absences.append({"kind": "FOLGA", "label": "Folga"})
        for vac in vac_by_user.get(u.id, []):
            if vac.vacation_type == VacationType.FERIAS:
                absences.append({"kind": "FERIAS", "label": "Férias"})
            else:
                absences.append({"kind": "LP", "label": "LP"})
        roster.append(
            {
                "user_id": u.id,
                "patente": u.patente,
                "nome_guerra": u.nome_guerra,
                "display_order": u.display_order,
                "operational_rank": _operational_rank(u.role),
                "absences": absences,
            }
        )
    roster.sort(key=lambda x: (x["operational_rank"], x["display_order"], x["nome_guerra"]))
    return roster


def list_operating_vehicles(db: Session, modality: VehicleModalidade) -> list[Vehicle]:
    return list(
        db.scalars(
            select(Vehicle)
            .where(Vehicle.modalidade == modality, Vehicle.status == VehicleStatus.OPERANDO)
            .order_by(Vehicle.prefixo)
        ).all()
    )


def build_calendar(db: Session, year: int, month: int, *, hide_drafts: bool = False) -> dict:
    start, end = _month_bounds(year, month)
    rows = db.scalars(
        select(ServiceScale)
        .where(ServiceScale.scale_date >= start, ServiceScale.scale_date <= end)
        .options(joinedload(ServiceScale.teams))
    ).unique().all()
    by_date = {r.scale_date: r for r in rows}
    days: list[dict] = []
    d = start
    while d <= end:
        row = by_date.get(d)
        if hide_drafts and row and row.status == ScaleStatus.DRAFT:
            row = None
        days.append(
            {
                "date": d,
                "scale_id": row.id if row else None,
                "title": row.title if row else None,
                "status": row.status if row else None,
                "team_count": len(row.teams) if row else 0,
            }
        )
        d += timedelta(days=1)
    return {"year": year, "month": month, "days": days}


def get_day_detail(db: Session, scale_date: date, *, can_edit: bool) -> dict:
    scale = _load_scale_by_date(db, scale_date)
    if scale and scale.status == ScaleStatus.DRAFT and not can_edit:
        scale = None
    ft = list_operating_vehicles(db, VehicleModalidade.FT)
    ro = list_operating_vehicles(db, VehicleModalidade.ROCAM)
    return {
        "scale": scale,
        "staff_roster": build_staff_roster(db, scale_date),
        "vehicles_ft": ft,
        "vehicles_ro_cam": ro,
    }


def create_scale(db: Session, actor: User, payload: ServiceScaleCreate) -> ServiceScale:
    if db.scalar(select(func.count()).select_from(ServiceScale).where(ServiceScale.scale_date == payload.scale_date)):
        raise ValueError("Já existe escala para esta data")
    row = ServiceScale(
        scale_date=payload.scale_date,
        title=payload.title,
        description=payload.description,
        status=payload.status if payload.status == ScaleStatus.DRAFT else ScaleStatus.DRAFT,
        created_by_id=actor.id,
        published_at=datetime.now(_BR) if payload.status == ScaleStatus.PUBLISHED else None,
    )
    if payload.status == ScaleStatus.PUBLISHED:
        row.status = ScaleStatus.PUBLISHED
    db.add(row)
    db.flush()
    _append_scale_log(
        db,
        scale_id=row.id,
        actor_id=actor.id,
        action=ScaleLogAction.CREATED,
        description=f"Escala criada: {row.title} ({row.scale_date.strftime('%d/%m/%Y')})",
    )
    if row.status == ScaleStatus.PUBLISHED:
        _append_scale_log(
            db,
            scale_id=row.id,
            actor_id=actor.id,
            action=ScaleLogAction.PUBLISHED,
            description="Escala publicada na criação",
        )
    db.commit()
    db.refresh(row)
    return _load_scale(db, row.id) or row


def update_scale(db: Session, scale_id: int, actor: User, payload: ServiceScaleUpdate) -> ServiceScale:
    row = _load_scale(db, scale_id)
    if not row:
        raise ValueError("Escala não encontrada")
    changes: list[str] = []
    if payload.title is not None and payload.title != row.title:
        changes.append(f"título: {row.title} → {payload.title}")
        row.title = payload.title
    if payload.description is not None and payload.description != row.description:
        changes.append("descrição atualizada")
        row.description = payload.description
    if changes:
        _append_scale_log(
            db,
            scale_id=row.id,
            actor_id=actor.id,
            action=ScaleLogAction.UPDATED,
            description="; ".join(changes),
        )
    db.commit()
    return _load_scale(db, scale_id) or row


def add_team(db: Session, scale_id: int, actor: User, payload: ScaleTeamCreate) -> ServiceScale:
    row = _load_scale(db, scale_id)
    if not row:
        raise ValueError("Escala não encontrada")
    team_vehicle_id = None if payload.modality == ScaleModality.ROCAM else payload.vehicle_id
    _validate_vehicle(payload.modality, team_vehicle_id, db)
    _validate_members(payload.modality, payload.members)
    _validate_scale_uniqueness(
        row,
        exclude_team_id=None,
        modality=payload.modality,
        vehicle_id=team_vehicle_id,
        members=payload.members,
    )
    team = ScaleTeam(
        service_scale_id=row.id,
        modality=payload.modality,
        vehicle_id=team_vehicle_id,
        start_datetime=payload.start_datetime,
        end_datetime=payload.end_datetime,
        mission_name=payload.mission_name.strip(),
        notes=payload.notes,
    )
    db.add(team)
    db.flush()
    cancel_notes = _set_team_members(db, team, payload.members, row.scale_date, actor.id)
    desc = f"Equipe {payload.modality.value} — {payload.mission_name}"
    if cancel_notes:
        desc += f" | {'; '.join(cancel_notes)}"
    _append_scale_log(
        db,
        scale_id=row.id,
        actor_id=actor.id,
        action=ScaleLogAction.TEAM_ADDED,
        description=desc,
    )
    db.commit()
    return _load_scale(db, scale_id) or row


def update_team(db: Session, team_id: int, actor: User, payload: ScaleTeamUpdate) -> ServiceScale:
    team = db.scalars(
        select(ScaleTeam)
        .where(ScaleTeam.id == team_id)
        .options(joinedload(ScaleTeam.members))
    ).first()
    if not team:
        raise ValueError("Equipe não encontrada")
    row = _load_scale(db, team.service_scale_id)
    if not row:
        raise ValueError("Escala não encontrada")
    modality = payload.modality or team.modality
    if modality == ScaleModality.ROCAM:
        vehicle_id = None
    elif payload.vehicle_id is not None:
        vehicle_id = payload.vehicle_id
    else:
        vehicle_id = team.vehicle_id
    if payload.members is not None:
        members_input = payload.members
    else:
        members_input = [
            ScaleTeamMemberInput(
                user_id=m.user_id,
                assigned_vehicle_id=m.assigned_vehicle_id,
                role_label=m.role_label,
            )
            for m in team.members
        ]
    _validate_vehicle(modality, vehicle_id, db)
    _validate_members(modality, members_input)
    _validate_scale_uniqueness(
        row,
        exclude_team_id=team.id,
        modality=modality,
        vehicle_id=vehicle_id,
        members=members_input,
    )
    team.modality = modality
    team.vehicle_id = vehicle_id
    if payload.start_datetime is not None:
        team.start_datetime = payload.start_datetime
    if payload.end_datetime is not None:
        team.end_datetime = payload.end_datetime
    if payload.mission_name is not None:
        team.mission_name = payload.mission_name.strip()
    if payload.notes is not None:
        team.notes = payload.notes
    if team.end_datetime <= team.start_datetime:
        raise ValueError("Horário final deve ser posterior ao inicial")
    cancel_notes: list[str] = []
    if payload.members is not None:
        cancel_notes = _set_team_members(db, team, payload.members, row.scale_date, actor.id)
    _append_scale_log(
        db,
        scale_id=row.id,
        actor_id=actor.id,
        action=ScaleLogAction.TEAM_UPDATED,
        description=f"Equipe {team.modality.value} — {team.mission_name} atualizada"
        + (f" | {'; '.join(cancel_notes)}" if cancel_notes else ""),
    )
    db.commit()
    return _load_scale(db, row.id) or row


def update_team_members(
    db: Session, team_id: int, actor: User, payload: ScaleTeamMembersUpdate
) -> ServiceScale:
    team = db.get(ScaleTeam, team_id)
    if not team:
        raise ValueError("Equipe não encontrada")
    row = _load_scale(db, team.service_scale_id)
    if not row:
        raise ValueError("Escala não encontrada")
    _validate_members(team.modality, payload.members)
    _validate_scale_uniqueness(
        row,
        exclude_team_id=team.id,
        modality=team.modality,
        vehicle_id=team.vehicle_id,
        members=payload.members,
    )
    cancel_notes = _set_team_members(db, team, payload.members, row.scale_date, actor.id)
    desc = f"Efetivo da equipe {team.modality.value} — {team.mission_name} atualizado"
    if cancel_notes:
        desc += f" | {'; '.join(cancel_notes)}"
    _append_scale_log(
        db,
        scale_id=row.id,
        actor_id=actor.id,
        action=ScaleLogAction.MEMBERS_CHANGED,
        description=desc,
    )
    db.commit()
    return _load_scale(db, row.id) or row


def remove_team(db: Session, team_id: int, actor: User) -> ServiceScale:
    team = db.get(ScaleTeam, team_id)
    if not team:
        raise ValueError("Equipe não encontrada")
    scale_id = team.service_scale_id
    row = _load_scale(db, scale_id)
    if not row:
        raise ValueError("Escala não encontrada")
    desc = f"Equipe removida: {team.modality.value} — {team.mission_name}"
    db.delete(team)
    _append_scale_log(
        db,
        scale_id=scale_id,
        actor_id=actor.id,
        action=ScaleLogAction.TEAM_REMOVED,
        description=desc,
    )
    db.commit()
    return _load_scale(db, scale_id) or row


def publish_scale(db: Session, scale_id: int, actor: User) -> ServiceScale:
    row = _load_scale(db, scale_id)
    if not row:
        raise ValueError("Escala não encontrada")
    if not row.teams:
        raise ValueError("Adicione ao menos uma equipe antes de publicar")
    row.status = ScaleStatus.PUBLISHED
    row.published_at = datetime.now(_BR)
    _append_scale_log(
        db,
        scale_id=row.id,
        actor_id=actor.id,
        action=ScaleLogAction.PUBLISHED,
        description=f"Escala publicada: {row.title}",
    )
    db.commit()
    return _load_scale(db, scale_id) or row


def delete_scale(db: Session, scale_id: int, actor: User) -> None:
    row = db.get(ServiceScale, scale_id)
    if not row:
        raise ValueError("Escala não encontrada")
    title = row.title
    db.delete(row)
    db.commit()


def list_history(
    db: Session,
    *,
    from_date: date | None = None,
    to_date: date | None = None,
    status: ScaleStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ServiceScale], int]:
    stmt = select(ServiceScale).options(joinedload(ServiceScale.teams))
    count_stmt = select(func.count()).select_from(ServiceScale)
    if from_date:
        stmt = stmt.where(ServiceScale.scale_date >= from_date)
        count_stmt = count_stmt.where(ServiceScale.scale_date >= from_date)
    if to_date:
        stmt = stmt.where(ServiceScale.scale_date <= to_date)
        count_stmt = count_stmt.where(ServiceScale.scale_date <= to_date)
    if status:
        stmt = stmt.where(ServiceScale.status == status)
        count_stmt = count_stmt.where(ServiceScale.status == status)
    total = int(db.scalar(count_stmt) or 0)
    rows = db.scalars(
        stmt.order_by(ServiceScale.scale_date.desc()).limit(limit).offset(offset)
    ).unique().all()
    return list(rows), total


def list_recent_events(db: Session, limit: int = 15) -> list[ScaleLog]:
    return list(
        db.scalars(
            select(ScaleLog)
            .options(
                joinedload(ScaleLog.actor),
                joinedload(ScaleLog.service_scale),
            )
            .order_by(ScaleLog.created_at.desc())
            .limit(limit)
        ).all()
    )


def list_recent_published(db: Session, limit: int = 8) -> list[ServiceScale]:
    return list(
        db.scalars(
            select(ServiceScale)
            .where(ServiceScale.status == ScaleStatus.PUBLISHED)
            .order_by(ServiceScale.scale_date.desc())
            .limit(limit)
        ).all()
    )
