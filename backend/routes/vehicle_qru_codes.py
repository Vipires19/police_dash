from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_approved_user
from database.session import get_db
from models.user import User
from schemas.criminal_watch import VehicleQruCodeCreate, VehicleQruCodePublic, VehicleQruCodeUpdate
from services import vehicle_qru_code_service as svc

router = APIRouter(prefix="/vehicle-qru-codes", tags=["vehicle-qru-codes"])


@router.get("/", response_model=list[VehicleQruCodePublic])
def list_vehicle_qru_codes(
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[VehicleQruCodePublic]:
    rows = svc.list_vehicle_qru_codes(db)
    return [svc.vehicle_qru_code_to_public(r) for r in rows]


@router.get("/active", response_model=list[VehicleQruCodePublic])
def list_active_vehicle_qru_codes(
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[VehicleQruCodePublic]:
    rows = svc.list_vehicle_qru_codes(db, active_only=True)
    return [svc.vehicle_qru_code_to_public(r) for r in rows]


@router.post("/", response_model=VehicleQruCodePublic, status_code=status.HTTP_201_CREATED)
def create_vehicle_qru_code(
    body: VehicleQruCodeCreate,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> VehicleQruCodePublic:
    try:
        row = svc.create_vehicle_qru_code(db, current, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return svc.vehicle_qru_code_to_public(row)


@router.patch("/{code_id}", response_model=VehicleQruCodePublic)
def update_vehicle_qru_code(
    code_id: int,
    body: VehicleQruCodeUpdate,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> VehicleQruCodePublic:
    try:
        row = svc.update_vehicle_qru_code(db, code_id, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return svc.vehicle_qru_code_to_public(row)


@router.patch("/{code_id}/deactivate", response_model=VehicleQruCodePublic)
def deactivate_vehicle_qru_code(
    code_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> VehicleQruCodePublic:
    try:
        row = svc.deactivate_vehicle_qru_code(db, code_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return svc.vehicle_qru_code_to_public(row)
