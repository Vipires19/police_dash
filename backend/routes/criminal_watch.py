from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_approved_user
from database.session import get_db
from models.user import User
from schemas.criminal_watch import (
    CriminalWatchNoteCreate,
    CriminalWatchNotePublic,
    CriminalWatchSheetResponse,
    CriminalWatchVehicleCreate,
    CriminalWatchVehicleDetail,
    CriminalWatchVehiclePublic,
)
from services import criminal_watch_service as svc

router = APIRouter(prefix="/criminal-watch-vehicles", tags=["criminal-watch-vehicles"])


@router.post("/", response_model=CriminalWatchVehiclePublic, status_code=status.HTTP_201_CREATED)
def create_criminal_watch_vehicle(
    body: CriminalWatchVehicleCreate,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CriminalWatchVehiclePublic:
    try:
        row = svc.create_criminal_watch_vehicle(db, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return svc.criminal_watch_vehicle_to_public(row, current)


@router.get("/search", response_model=list[CriminalWatchVehiclePublic])
def search_criminal_watch_vehicles(
    q: str = Query(min_length=1, max_length=128),
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[CriminalWatchVehiclePublic]:
    rows = svc.search_criminal_watch_vehicles(db, q, limit=limit)
    return [svc.criminal_watch_vehicle_to_public(r) for r in rows]


@router.get("/sheet", response_model=CriminalWatchSheetResponse)
def get_operational_sheet(
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CriminalWatchSheetResponse:
    return svc.get_operational_sheet(db)


@router.get("/{vehicle_id}", response_model=CriminalWatchVehicleDetail)
def get_criminal_watch_vehicle(
    vehicle_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CriminalWatchVehicleDetail:
    try:
        return svc.get_criminal_watch_vehicle_detail(db, vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_criminal_watch_vehicle(
    vehicle_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        svc.delete_criminal_watch_vehicle(db, vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{vehicle_id}/notes", response_model=CriminalWatchNotePublic, status_code=status.HTTP_201_CREATED)
def add_criminal_watch_note(
    vehicle_id: int,
    body: CriminalWatchNoteCreate,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> CriminalWatchNotePublic:
    try:
        note = svc.add_criminal_watch_note(db, vehicle_id, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return CriminalWatchNotePublic(
        id=note.id,
        vehicle_id=note.vehicle_id,
        note=note.note,
        created_at=note.created_at,
        created_by_id=note.created_by_id,
        created_by_label=f"{current.patente} {current.nome_guerra}",
    )
