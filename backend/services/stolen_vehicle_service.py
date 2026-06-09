from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from models.stolen_vehicle import (
    StolenOccurrenceType,
    StolenVehicle,
    StolenVehicleType,
)
from models.user import User
from schemas.stolen_vehicle import (
    StolenOccurrenceTypeEnum,
    StolenVehicleCreate,
    StolenVehiclePublic,
    StolenVehicleSheetEntry,
    StolenVehicleSheetGroup,
    StolenVehicleSheetResponse,
    StolenVehicleTypeEnum,
)

_BR = ZoneInfo("America/Sao_Paulo")
SLOTS_PER_GROUP = 10
GROUPS = range(10)


def extract_plate_group(plate: str) -> int:
    normalized = plate.strip().upper()
    match = re.search(r"\d", normalized)
    if not match:
        raise ValueError("A placa deve conter pelo menos um número para identificar o grupo (0 a 9).")
    group = int(match.group())
    if group < 0 or group > 9:
        raise ValueError("O grupo da placa deve estar entre 0 e 9.")
    return group


def _to_public(row: StolenVehicle) -> StolenVehiclePublic:
    return StolenVehiclePublic.model_validate(row)


def create_stolen_vehicle(db: Session, current: User, body: StolenVehicleCreate) -> StolenVehicle:
    plate_group = extract_plate_group(body.plate)
    row = StolenVehicle(
        vehicle_type=StolenVehicleType(body.vehicle_type.value),
        plate=body.plate.strip().upper(),
        vehicle_model=body.vehicle_model.strip(),
        color=body.color.strip(),
        year=body.year,
        occurrence_type=StolenOccurrenceType(body.occurrence_type.value),
        plate_group=plate_group,
        observation=body.observation.strip() if body.observation else None,
        is_recovered=False,
        recovered_at=None,
        recovered_by_id=None,
        recovered_notes=None,
        created_by_id=current.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_stolen_vehicles(
    db: Session,
    *,
    is_recovered: bool | None = None,
    vehicle_type: StolenVehicleType | None = None,
    plate_group: int | None = None,
    limit: int = 200,
) -> list[StolenVehicle]:
    q = select(StolenVehicle).order_by(StolenVehicle.created_at.desc())
    if is_recovered is not None:
        q = q.where(StolenVehicle.is_recovered.is_(is_recovered))
    if vehicle_type is not None:
        q = q.where(StolenVehicle.vehicle_type == vehicle_type)
    if plate_group is not None:
        q = q.where(StolenVehicle.plate_group == plate_group)
    q = q.limit(limit)
    return list(db.scalars(q).all())


def search_stolen_vehicles(db: Session, query: str, *, limit: int = 100) -> list[StolenVehicle]:
    term = query.strip()
    if not term:
        return []
    pattern = f"%{term}%"
    q = (
        select(StolenVehicle)
        .where(
            or_(
                StolenVehicle.plate.ilike(pattern),
                StolenVehicle.vehicle_model.ilike(pattern),
                StolenVehicle.color.ilike(pattern),
            )
        )
        .order_by(StolenVehicle.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(q).all())


def get_stolen_vehicle(db: Session, vehicle_id: int) -> StolenVehicle | None:
    return db.get(StolenVehicle, vehicle_id)


def recover_stolen_vehicle(
    db: Session,
    vehicle_id: int,
    current: User,
    *,
    notes: str | None = None,
) -> StolenVehicle:
    row = get_stolen_vehicle(db, vehicle_id)
    if not row:
        raise ValueError("Veículo não encontrado.")
    if row.is_recovered:
        raise ValueError("Veículo já está marcado como localizado.")
    row.is_recovered = True
    row.recovered_at = datetime.now(_BR)
    row.recovered_by_id = current.id
    row.recovered_notes = notes.strip() if notes else None
    db.commit()
    db.refresh(row)
    return row


def _empty_slots() -> list[StolenVehicleSheetEntry]:
    return [StolenVehicleSheetEntry() for _ in range(SLOTS_PER_GROUP)]


def _build_sheet_groups(
    db: Session,
    vehicle_type: StolenVehicleType,
) -> list[StolenVehicleSheetGroup]:
    groups: list[StolenVehicleSheetGroup] = []
    for group in GROUPS:
        rows = list(
            db.scalars(
                select(StolenVehicle)
                .where(
                    StolenVehicle.is_recovered.is_(False),
                    StolenVehicle.vehicle_type == vehicle_type,
                    StolenVehicle.plate_group == group,
                )
                .order_by(StolenVehicle.created_at.desc())
                .limit(SLOTS_PER_GROUP)
            ).all()
        )
        slots = _empty_slots()
        # Preenchimento de baixo para cima: o mais recente ocupa o slot inferior (índice 9).
        for i, row in enumerate(rows):
            slot_index = SLOTS_PER_GROUP - 1 - i
            slots[slot_index] = StolenVehicleSheetEntry(
                id=row.id,
                plate=row.plate,
                vehicle_model=row.vehicle_model,
                color=row.color,
                year=row.year,
                occurrence_type=StolenOccurrenceTypeEnum(row.occurrence_type.value),
            )
        groups.append(StolenVehicleSheetGroup(group=group, slots=slots))
    return groups


def get_operational_sheet(db: Session) -> StolenVehicleSheetResponse:
    return StolenVehicleSheetResponse(
        carros=_build_sheet_groups(db, StolenVehicleType.CARRO),
        motos=_build_sheet_groups(db, StolenVehicleType.MOTO),
    )


def stolen_vehicle_to_public(row: StolenVehicle) -> StolenVehiclePublic:
    return _to_public(row)
