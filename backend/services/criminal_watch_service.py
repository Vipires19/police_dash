from __future__ import annotations

import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from models.criminal_watch import CriminalWatchNote, CriminalWatchVehicle, VehicleQruCode
from models.user import User
from schemas.criminal_watch import (
    CriminalWatchNoteCreate,
    CriminalWatchNotePublic,
    CriminalWatchSheetEntry,
    CriminalWatchSheetResponse,
    CriminalWatchVehicleCreate,
    CriminalWatchVehicleDetail,
    CriminalWatchVehiclePublic,
)

SLOTS_PER_SHEET = 15


def _user_label(user: User | None) -> str | None:
    if not user:
        return None
    return f"{user.patente} {user.nome_guerra}"


def split_plate(plate: str) -> tuple[str, str]:
    normalized = plate.strip().upper().replace("-", "").replace(" ", "")
    match = re.match(r"^([A-Z]{3})(.+)$", normalized)
    if match:
        return match.group(2), match.group(1)
    return normalized, ""


def year_short(year: int) -> str:
    return str(year)[-2:]


def _get_qru_code(db: Session, qru_code_id: int) -> VehicleQruCode:
    row = db.get(VehicleQruCode, qru_code_id)
    if not row:
        raise ValueError("Código QRU não encontrado.")
    if not row.is_active:
        raise ValueError("Código QRU inativo.")
    return row


def _vehicle_to_public(row: CriminalWatchVehicle, creator: User | None = None) -> CriminalWatchVehiclePublic:
    return CriminalWatchVehiclePublic(
        id=row.id,
        plate=row.plate,
        vehicle_model=row.vehicle_model,
        color=row.color,
        year=row.year,
        qru_code_id=row.qru_code_id,
        qru_code=row.qru_code.code,
        qru_description=row.qru_code.description,
        created_at=row.created_at,
        created_by_id=row.created_by_id,
        created_by_label=_user_label(creator),
    )


def create_criminal_watch_vehicle(
    db: Session,
    current: User,
    body: CriminalWatchVehicleCreate,
) -> CriminalWatchVehicle:
    qru = _get_qru_code(db, body.qru_code_id)
    row = CriminalWatchVehicle(
        plate=body.plate.strip().upper(),
        vehicle_model=body.vehicle_model.strip(),
        color=body.color.strip(),
        year=body.year,
        qru_code_id=qru.id,
        created_by_id=current.id,
    )
    db.add(row)
    db.flush()
    note = CriminalWatchNote(
        vehicle_id=row.id,
        note=body.initial_note.strip(),
        created_by_id=current.id,
    )
    db.add(note)
    db.commit()
    db.refresh(row)
    return row


def search_criminal_watch_vehicles(
    db: Session,
    query: str,
    *,
    limit: int = 100,
) -> list[CriminalWatchVehicle]:
    term = query.strip()
    if not term:
        return []
    pattern = f"%{term}%"
    q = (
        select(CriminalWatchVehicle)
        .join(VehicleQruCode, CriminalWatchVehicle.qru_code_id == VehicleQruCode.id)
        .options(joinedload(CriminalWatchVehicle.qru_code))
        .where(
            or_(
                CriminalWatchVehicle.plate.ilike(pattern),
                CriminalWatchVehicle.vehicle_model.ilike(pattern),
                CriminalWatchVehicle.color.ilike(pattern),
                VehicleQruCode.code.ilike(pattern),
                VehicleQruCode.description.ilike(pattern),
            )
        )
        .order_by(CriminalWatchVehicle.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(q).unique().all())


def get_criminal_watch_vehicle(db: Session, vehicle_id: int) -> CriminalWatchVehicle | None:
    return db.scalar(
        select(CriminalWatchVehicle)
        .options(
            joinedload(CriminalWatchVehicle.qru_code),
            joinedload(CriminalWatchVehicle.notes),
        )
        .where(CriminalWatchVehicle.id == vehicle_id)
    )


def get_criminal_watch_vehicle_detail(db: Session, vehicle_id: int) -> CriminalWatchVehicleDetail:
    row = get_criminal_watch_vehicle(db, vehicle_id)
    if not row:
        raise ValueError("Veículo não encontrado.")
    creator = db.get(User, row.created_by_id)
    note_creators = {
        uid: db.get(User, uid)
        for uid in {n.created_by_id for n in row.notes}
    }
    return CriminalWatchVehicleDetail(
        **_vehicle_to_public(row, creator).model_dump(),
        notes=[
            CriminalWatchNotePublic(
                id=n.id,
                vehicle_id=n.vehicle_id,
                note=n.note,
                created_at=n.created_at,
                created_by_id=n.created_by_id,
                created_by_label=_user_label(note_creators.get(n.created_by_id)),
            )
            for n in row.notes
        ],
    )


def add_criminal_watch_note(
    db: Session,
    vehicle_id: int,
    current: User,
    body: CriminalWatchNoteCreate,
) -> CriminalWatchNote:
    row = get_criminal_watch_vehicle(db, vehicle_id)
    if not row:
        raise ValueError("Veículo não encontrado.")
    note = CriminalWatchNote(
        vehicle_id=vehicle_id,
        note=body.note.strip(),
        created_by_id=current.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def delete_criminal_watch_vehicle(db: Session, vehicle_id: int) -> None:
    row = get_criminal_watch_vehicle(db, vehicle_id)
    if not row:
        raise ValueError("Veículo não encontrado.")
    db.delete(row)
    db.commit()


def get_operational_sheet(db: Session) -> CriminalWatchSheetResponse:
    rows = list(
        db.scalars(
            select(CriminalWatchVehicle)
            .options(joinedload(CriminalWatchVehicle.qru_code))
            .order_by(CriminalWatchVehicle.created_at.desc())
            .limit(SLOTS_PER_SHEET)
        )
        .unique()
        .all()
    )
    slots = [CriminalWatchSheetEntry() for _ in range(SLOTS_PER_SHEET)]
    for i, row in enumerate(rows):
        slot_index = SLOTS_PER_SHEET - 1 - i
        plate_numeric, plate_letters = split_plate(row.plate)
        slots[slot_index] = CriminalWatchSheetEntry(
            id=row.id,
            plate_numeric=plate_numeric,
            plate_letters=plate_letters,
            vehicle_model=row.vehicle_model.upper(),
            color_abbr=row.color.strip().upper(),
            year_short=year_short(row.year),
            qru_code=row.qru_code.code,
        )
    return CriminalWatchSheetResponse(slots=slots)


def criminal_watch_vehicle_to_public(row: CriminalWatchVehicle, creator: User | None = None) -> CriminalWatchVehiclePublic:
    return _vehicle_to_public(row, creator)
