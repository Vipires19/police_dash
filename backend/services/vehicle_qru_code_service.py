from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.criminal_watch import VehicleQruCode
from models.user import User
from schemas.criminal_watch import VehicleQruCodeCreate, VehicleQruCodePublic, VehicleQruCodeUpdate


def list_vehicle_qru_codes(db: Session, *, active_only: bool = False) -> list[VehicleQruCode]:
    q = select(VehicleQruCode).order_by(VehicleQruCode.code.asc())
    if active_only:
        q = q.where(VehicleQruCode.is_active.is_(True))
    return list(db.scalars(q).all())


def get_vehicle_qru_code(db: Session, code_id: int) -> VehicleQruCode | None:
    return db.get(VehicleQruCode, code_id)


def create_vehicle_qru_code(db: Session, current: User, body: VehicleQruCodeCreate) -> VehicleQruCode:
    code = body.code.strip().upper()
    existing = db.scalar(select(VehicleQruCode).where(VehicleQruCode.code == code))
    if existing:
        raise ValueError("Já existe um código QRU com este identificador.")
    row = VehicleQruCode(
        code=code,
        description=body.description.strip(),
        is_active=True,
        created_by_id=current.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_vehicle_qru_code(db: Session, code_id: int, body: VehicleQruCodeUpdate) -> VehicleQruCode:
    row = get_vehicle_qru_code(db, code_id)
    if not row:
        raise ValueError("Código QRU não encontrado.")
    if body.code is not None:
        code = body.code.strip().upper()
        existing = db.scalar(
            select(VehicleQruCode).where(VehicleQruCode.code == code, VehicleQruCode.id != code_id)
        )
        if existing:
            raise ValueError("Já existe um código QRU com este identificador.")
        row.code = code
    if body.description is not None:
        row.description = body.description.strip()
    db.commit()
    db.refresh(row)
    return row


def deactivate_vehicle_qru_code(db: Session, code_id: int) -> VehicleQruCode:
    row = get_vehicle_qru_code(db, code_id)
    if not row:
        raise ValueError("Código QRU não encontrado.")
    if not row.is_active:
        raise ValueError("Código QRU já está desativado.")
    row.is_active = False
    db.commit()
    db.refresh(row)
    return row


def vehicle_qru_code_to_public(row: VehicleQruCode) -> VehicleQruCodePublic:
    return VehicleQruCodePublic.model_validate(row)
