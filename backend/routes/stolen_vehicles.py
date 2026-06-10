from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_approved_user
from database.session import get_db
from models.stolen_vehicle import StolenVehicleType
from models.user import User
from schemas.stolen_vehicle import (
    StolenVehicleCreate,
    StolenVehiclePublic,
    StolenVehicleRecoverBody,
    StolenVehicleSheetResponse,
    StolenVehicleTypeEnum,
)
from services import stolen_vehicle_service as svc

router = APIRouter(prefix="/stolen-vehicles", tags=["stolen-vehicles"])


@router.post("/", response_model=StolenVehiclePublic, status_code=status.HTTP_201_CREATED)
def create_stolen_vehicle(
    body: StolenVehicleCreate,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> StolenVehiclePublic:
    try:
        row = svc.create_stolen_vehicle(db, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return svc.stolen_vehicle_to_public(row)


@router.get("/", response_model=list[StolenVehiclePublic])
def list_stolen_vehicles(
    is_recovered: bool | None = None,
    vehicle_type: StolenVehicleTypeEnum | None = None,
    plate_group: int | None = Query(default=None, ge=0, le=9),
    limit: int = Query(default=200, ge=1, le=500),
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[StolenVehiclePublic]:
    vtype = StolenVehicleType(vehicle_type.value) if vehicle_type else None
    rows = svc.list_stolen_vehicles(
        db,
        is_recovered=is_recovered,
        vehicle_type=vtype,
        plate_group=plate_group,
        limit=limit,
    )
    return [svc.stolen_vehicle_to_public(r) for r in rows]


@router.get("/search", response_model=list[StolenVehiclePublic])
def search_stolen_vehicles(
    q: str = Query(min_length=1, max_length=128),
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[StolenVehiclePublic]:
    rows = svc.search_stolen_vehicles(db, q, limit=limit)
    return [svc.stolen_vehicle_to_public(r) for r in rows]


@router.get("/sheet", response_model=StolenVehicleSheetResponse)
def get_operational_sheet(
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> StolenVehicleSheetResponse:
    return svc.get_operational_sheet(db)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stolen_vehicle(
    vehicle_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        svc.delete_stolen_vehicle(db, vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{vehicle_id}/recover", response_model=StolenVehiclePublic)
def recover_stolen_vehicle(
    vehicle_id: int,
    body: StolenVehicleRecoverBody = StolenVehicleRecoverBody(),
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> StolenVehiclePublic:
    try:
        row = svc.recover_stolen_vehicle(db, vehicle_id, current, notes=body.recovered_notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return svc.stolen_vehicle_to_public(row)
