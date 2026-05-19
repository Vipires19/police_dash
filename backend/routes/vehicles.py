from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_approved_user, require_vehicle_editor
from database.session import get_db
from models.user import User
from schemas.vehicle import (
    VehicleCreate,
    VehicleLogFeedItem,
    VehicleLogPublic,
    VehiclePublic,
    VehicleStatusChange,
    VehicleUpdate,
)
from services import vehicle_service as vehicle_svc

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/recent-logs", response_model=list[VehicleLogFeedItem])
def recent_logs(
    limit: int = Query(default=15, ge=1, le=50),
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[VehicleLogFeedItem]:
    return vehicle_svc.list_recent_logs(db, limit=limit)


@router.get("/", response_model=list[VehiclePublic])
def list_vehicles(
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[VehiclePublic]:
    rows = vehicle_svc.list_vehicles(db)
    return [VehiclePublic.model_validate(v) for v in rows]


@router.post("/", response_model=VehiclePublic, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    body: VehicleCreate,
    current: User = Depends(require_vehicle_editor),
    db: Session = Depends(get_db),
) -> VehiclePublic:
    try:
        v = vehicle_svc.create_vehicle(db, body, current)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return VehiclePublic.model_validate(v)


@router.get("/{vehicle_id}", response_model=VehiclePublic)
def get_vehicle(
    vehicle_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> VehiclePublic:
    v = vehicle_svc.get_vehicle(db, vehicle_id)
    if not v:
        raise HTTPException(status_code=404, detail="Viatura não encontrada")
    return VehiclePublic.model_validate(v)


@router.patch("/{vehicle_id}", response_model=VehiclePublic)
def update_vehicle(
    vehicle_id: int,
    body: VehicleUpdate,
    current: User = Depends(require_vehicle_editor),
    db: Session = Depends(get_db),
) -> VehiclePublic:
    v = vehicle_svc.get_vehicle(db, vehicle_id)
    if not v:
        raise HTTPException(status_code=404, detail="Viatura não encontrada")
    try:
        updated = vehicle_svc.update_vehicle(db, v, body, current)
    except ValueError as e:
        code = (
            status.HTTP_422_UNPROCESSABLE_ENTITY
            if "Motivo obrigatório" in str(e)
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=code, detail=str(e)) from e
    return VehiclePublic.model_validate(updated)


@router.patch("/{vehicle_id}/status", response_model=VehiclePublic)
def change_status(
    vehicle_id: int,
    body: VehicleStatusChange,
    current: User = Depends(require_vehicle_editor),
    db: Session = Depends(get_db),
) -> VehiclePublic:
    v = vehicle_svc.get_vehicle(db, vehicle_id)
    if not v:
        raise HTTPException(status_code=404, detail="Viatura não encontrada")
    updated = vehicle_svc.change_vehicle_status(db, v, body, current)
    return VehiclePublic.model_validate(updated)


@router.get("/{vehicle_id}/logs", response_model=list[VehicleLogPublic])
def list_logs(
    vehicle_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[VehicleLogPublic]:
    v = vehicle_svc.get_vehicle(db, vehicle_id)
    if not v:
        raise HTTPException(status_code=404, detail="Viatura não encontrada")
    logs = vehicle_svc.list_vehicle_logs(db, vehicle_id)
    return [VehicleLogPublic.model_validate(x) for x in logs]
