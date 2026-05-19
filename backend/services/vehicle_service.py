from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.user import User
from models.vehicle import (
    Vehicle,
    VehicleActionType,
    VehicleLog,
    VehicleModalidade,
    VehicleStatus,
)
from schemas.vehicle import (
    VehicleActionTypeEnum,
    VehicleCreate,
    VehicleLogFeedItem,
    VehicleStatusChange,
    VehicleStatusEnum,
    VehicleUpdate,
)

_BR = ZoneInfo("America/Sao_Paulo")


def _date_label() -> str:
    return datetime.now(_BR).strftime("%d/%m/%Y")


def _actor(user: User) -> str:
    return f"{user.patente} {user.nome_guerra}"


def _append_log(
    db: Session,
    *,
    vehicle_id: int,
    user_id: int,
    action: VehicleActionType,
    description: str,
    motivo: str | None = None,
    old_status: VehicleStatus | None = None,
    new_status: VehicleStatus | None = None,
) -> VehicleLog:
    row = VehicleLog(
        vehicle_id=vehicle_id,
        user_id=user_id,
        action_type=action,
        description=description,
        motivo=motivo,
        old_status=old_status,
        new_status=new_status,
    )
    db.add(row)
    return row


def _ensure_unique_fields(
    db: Session,
    vehicle_id: int,
    *,
    placa: str | None = None,
    prefixo: str | None = None,
) -> None:
    if placa:
        dup = db.scalars(
            select(Vehicle).where(Vehicle.placa == placa, Vehicle.id != vehicle_id)
        ).first()
        if dup:
            raise ValueError("Placa já cadastrada")
    if prefixo:
        dup = db.scalars(
            select(Vehicle).where(Vehicle.prefixo == prefixo, Vehicle.id != vehicle_id)
        ).first()
        if dup:
            raise ValueError("Prefixo já cadastrado")


def _apply_status_change(
    db: Session,
    vehicle: Vehicle,
    new: VehicleStatus,
    actor: User,
    motivo: str,
) -> bool:
    """Aplica mudança de status com auditoria. Retorna True se houve alteração."""
    old = vehicle.status
    if old == new:
        return False
    now_aware = datetime.now(_BR).astimezone()
    if new == VehicleStatus.BAIXADA:
        vehicle.baixada_at = now_aware
    if new == VehicleStatus.OPERANDO:
        vehicle.retorno_operacao_at = now_aware
    vehicle.status = new
    motivo_clean = motivo.strip()
    if new == VehicleStatus.OPERANDO and old in (VehicleStatus.BAIXADA, VehicleStatus.MANUTENCAO):
        action = VehicleActionType.RETURNED
        desc = f"{_date_label()} — {vehicle.prefixo} retornou à operação — por {_actor(actor)}"
    else:
        action = VehicleActionType.STATUS_CHANGED
        desc = f"{_date_label()} — {vehicle.prefixo} status {old.value} → {new.value} — por {_actor(actor)}"
    _append_log(
        db,
        vehicle_id=vehicle.id,
        user_id=actor.id,
        action=action,
        description=desc,
        motivo=motivo_clean,
        old_status=old,
        new_status=new,
    )
    return True


def list_vehicles(db: Session) -> list[Vehicle]:
    return list(
        db.scalars(
            select(Vehicle).order_by(
                Vehicle.modalidade.asc(),
                Vehicle.prefixo.asc(),
            )
        ).all()
    )


def get_vehicle(db: Session, vehicle_id: int) -> Vehicle | None:
    return db.scalars(select(Vehicle).where(Vehicle.id == vehicle_id)).first()


def list_vehicle_logs(db: Session, vehicle_id: int) -> list[VehicleLog]:
    return list(
        db.scalars(
            select(VehicleLog)
            .where(VehicleLog.vehicle_id == vehicle_id)
            .order_by(VehicleLog.created_at.desc())
        ).all()
    )


def list_recent_logs(db: Session, limit: int = 15) -> list[VehicleLogFeedItem]:
    stmt = (
        select(VehicleLog, Vehicle, User)
        .join(Vehicle, Vehicle.id == VehicleLog.vehicle_id)
        .join(User, User.id == VehicleLog.user_id)
        .order_by(VehicleLog.created_at.desc())
        .limit(limit)
    )
    out: list[VehicleLogFeedItem] = []
    for log, vehicle, actor in db.execute(stmt).all():
        out.append(
            VehicleLogFeedItem(
                id=log.id,
                vehicle_id=log.vehicle_id,
                user_id=log.user_id,
                action_type=VehicleActionTypeEnum(log.action_type.value),
                description=log.description,
                motivo=log.motivo,
                old_status=VehicleStatusEnum(log.old_status.value) if log.old_status else None,
                new_status=VehicleStatusEnum(log.new_status.value) if log.new_status else None,
                created_at=log.created_at,
                vehicle_prefixo=vehicle.prefixo,
                actor_label=_actor(actor),
            )
        )
    return out


def create_vehicle(db: Session, data: VehicleCreate, actor: User) -> Vehicle:
    placa = data.placa.strip().upper()
    prefixo = data.prefixo.strip()
    if db.scalars(select(Vehicle).where(Vehicle.placa == placa)).first():
        raise ValueError("Placa já cadastrada")
    if db.scalars(select(Vehicle).where(Vehicle.prefixo == prefixo)).first():
        raise ValueError("Prefixo já cadastrado")
    v = Vehicle(
        placa=placa,
        prefixo=prefixo,
        modelo=data.modelo.strip(),
        modalidade=VehicleModalidade(data.modalidade.value),
        status=VehicleStatus(data.status.value),
    )
    db.add(v)
    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Placa ou prefixo já cadastrados") from e
    desc = f"{_date_label()} — Nova viatura cadastrada — {v.prefixo}"
    _append_log(
        db,
        vehicle_id=v.id,
        user_id=actor.id,
        action=VehicleActionType.CREATED,
        description=desc,
        new_status=v.status,
    )
    db.commit()
    db.refresh(v)
    return v


def update_vehicle(db: Session, vehicle: Vehicle, data: VehicleUpdate, actor: User) -> Vehicle:
    changes: list[str] = []
    status_changed = False

    if data.placa is not None:
        np = data.placa.strip().upper()
        if np != vehicle.placa:
            _ensure_unique_fields(db, vehicle.id, placa=np)
            changes.append(f"placa {vehicle.placa} → {np}")
            vehicle.placa = np
    if data.prefixo is not None:
        np = data.prefixo.strip()
        if np != vehicle.prefixo:
            _ensure_unique_fields(db, vehicle.id, prefixo=np)
            changes.append(f"prefixo {vehicle.prefixo} → {np}")
            vehicle.prefixo = np
    if data.modelo is not None:
        nm = data.modelo.strip()
        if nm != vehicle.modelo:
            changes.append("modelo atualizado")
            vehicle.modelo = nm
    if data.modalidade is not None:
        nm = VehicleModalidade(data.modalidade.value)
        if nm != vehicle.modalidade:
            changes.append(f"modalidade {vehicle.modalidade.value} → {nm.value}")
            vehicle.modalidade = nm
    if data.observacoes is not None:
        new_obs = data.observacoes.strip() or None
        old_obs = (vehicle.observacoes or "").strip() or None
        if new_obs != old_obs:
            changes.append("observações atualizadas")
            vehicle.observacoes = new_obs

    if data.status is not None:
        new_status = VehicleStatus(data.status.value)
        if new_status != vehicle.status:
            if not data.status_motivo or not data.status_motivo.strip():
                raise ValueError("Motivo obrigatório ao alterar o status operacional")
            status_changed = _apply_status_change(
                db, vehicle, new_status, actor, data.status_motivo
            )

    if not changes and not status_changed:
        return vehicle

    if changes:
        try:
            db.flush()
        except IntegrityError as e:
            db.rollback()
            raise ValueError("Placa ou prefixo já cadastrados") from e
        desc = f"{_date_label()} — {vehicle.prefixo} atualizada — " + "; ".join(changes)
        _append_log(
            db,
            vehicle_id=vehicle.id,
            user_id=actor.id,
            action=VehicleActionType.UPDATED,
            description=desc,
        )

    db.commit()
    db.refresh(vehicle)
    return vehicle


def change_vehicle_status(
    db: Session,
    vehicle: Vehicle,
    body: VehicleStatusChange,
    actor: User,
) -> Vehicle:
    new = VehicleStatus(body.new_status.value)
    if vehicle.status == new:
        return vehicle
    _apply_status_change(db, vehicle, new, actor, body.motivo)
    db.commit()
    db.refresh(vehicle)
    return vehicle
