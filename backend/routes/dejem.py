"""Rotas do módulo DEJEM — interesse e distribuição automática."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from auth.dependencies import (
    get_current_approved_user,
    require_dejem_admin,
    require_dejem_reopen,
)
from database.session import get_db
from models.user import User
from schemas.dejem import (
    DejemAllocationAdminRow,
    DejemAllocationPublic,
    DejemDistributeResponse,
    DejemDistributionPreview,
    DejemInterestAdminRow,
    DejemInterestPublic,
    DejemInterestUpsert,
    DejemMonthCreate,
    DejemMonthPublic,
    DejemMonthUpdate,
)
from services import dejem_service as svc
from services.dejem_service import DejemError

router = APIRouter(prefix="/dejem", tags=["dejem"])

_NOT_IMPLEMENTED = {"detail": "Not Implemented — funcionalidade DEJEM ainda não disponível"}


def _stub() -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_501_NOT_IMPLEMENTED, content=_NOT_IMPLEMENTED)


def _http_error(exc: DejemError) -> HTTPException:
    code = status.HTTP_400_BAD_REQUEST
    msg = str(exc)
    if "não encontrad" in msg.lower():
        code = status.HTTP_404_NOT_FOUND
    return HTTPException(status_code=code, detail=msg)


@router.get("/")
def dejem_root(_: User = Depends(get_current_approved_user)) -> dict[str, str]:
    return {"module": "dejem", "phase": "4.3", "status": "distribution"}


# --- Months ---


@router.get("/months", response_model=list[DejemMonthPublic])
def list_months(
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[DejemMonthPublic]:
    return svc.list_months(db)


@router.post("/months", response_model=DejemMonthPublic, status_code=status.HTTP_201_CREATED)
def create_month(
    body: DejemMonthCreate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> DejemMonthPublic:
    try:
        return svc.create_month(db, current, body)
    except DejemError as e:
        raise _http_error(e) from e


@router.get("/months/{month_id}", response_model=DejemMonthPublic)
def get_month(
    month_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> DejemMonthPublic:
    try:
        return svc.get_month(db, month_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.patch("/months/{month_id}", response_model=DejemMonthPublic)
def update_month(
    month_id: int,
    body: DejemMonthUpdate,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> DejemMonthPublic:
    try:
        return svc.update_month(db, month_id, body)
    except DejemError as e:
        raise _http_error(e) from e


@router.post("/months/{month_id}/close-interest", response_model=DejemMonthPublic)
def close_interest(
    month_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> DejemMonthPublic:
    try:
        return svc.close_interest(db, month_id)
    except DejemError as e:
        raise _http_error(e) from e


# --- Interest (próprio policial) ---


@router.get("/months/{month_id}/interest", response_model=DejemInterestPublic | None)
def get_my_interest(
    month_id: int,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> DejemInterestPublic | None:
    try:
        return svc.get_my_interest(db, month_id, current)
    except DejemError as e:
        raise _http_error(e) from e


@router.post(
    "/months/{month_id}/interest",
    response_model=DejemInterestPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_my_interest(
    month_id: int,
    body: DejemInterestUpsert,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> DejemInterestPublic:
    try:
        return svc.create_my_interest(db, month_id, current, body)
    except DejemError as e:
        raise _http_error(e) from e


@router.patch("/months/{month_id}/interest", response_model=DejemInterestPublic)
def update_my_interest(
    month_id: int,
    body: DejemInterestUpsert,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> DejemInterestPublic:
    try:
        return svc.update_my_interest(db, month_id, current, body)
    except DejemError as e:
        raise _http_error(e) from e


@router.delete("/months/{month_id}/interest", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_interest(
    month_id: int,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        svc.delete_my_interest(db, month_id, current)
    except DejemError as e:
        raise _http_error(e) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Interest (admin) ---


@router.get("/months/{month_id}/interests", response_model=list[DejemInterestAdminRow])
def list_month_interests(
    month_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[DejemInterestAdminRow]:
    try:
        return svc.list_month_interests(db, month_id)
    except DejemError as e:
        raise _http_error(e) from e


# --- Distribution ---


@router.get("/months/{month_id}/distribution-preview", response_model=DejemDistributionPreview)
def distribution_preview(
    month_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> DejemDistributionPreview:
    try:
        return svc.get_distribution_preview(db, month_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.post("/months/{month_id}/distribute", response_model=DejemDistributeResponse)
def distribute_month(
    month_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> DejemDistributeResponse:
    try:
        return svc.distribute_month(db, month_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.post("/months/{month_id}/reopen-distribution", response_model=DejemMonthPublic)
def reopen_distribution(
    month_id: int,
    _: User = Depends(require_dejem_reopen),
    db: Session = Depends(get_db),
) -> DejemMonthPublic:
    try:
        return svc.reopen_distribution(db, month_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.get("/months/{month_id}/allocations", response_model=list[DejemAllocationAdminRow])
def list_month_allocations(
    month_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[DejemAllocationAdminRow]:
    try:
        return svc.list_month_allocations(db, month_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.get("/months/{month_id}/allocation", response_model=DejemAllocationPublic | None)
def get_my_allocation(
    month_id: int,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> DejemAllocationPublic | None:
    try:
        return svc.get_my_allocation(db, month_id, current)
    except DejemError as e:
        raise _http_error(e) from e


# --- Stubs (fases futuras) ---


@router.get("/shifts")
def list_shifts_stub(
    _: User = Depends(get_current_approved_user),
) -> JSONResponse:
    return _stub()


@router.get("/participants")
def list_participants_stub(
    _: User = Depends(get_current_approved_user),
) -> JSONResponse:
    return _stub()
