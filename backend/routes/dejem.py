"""Rotas do módulo DEJEM — interesse e distribuição automática."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from auth.dependencies import (
    get_current_approved_user,
    require_dejem_admin,
    require_dejem_reopen,
    require_dejem_shift_editor,
    require_dejem_shift_viewer,
)
from database.session import get_db
from models.user import User
from schemas.dejem import (
    DejemAdminAddParticipant,
    DejemAllocationAdminRow,
    DejemAllocationPublic,
    DejemDistributeResponse,
    DejemDistributionPreview,
    DejemEnrollmentResult,
    DejemInterestAdminRow,
    DejemInterestPublic,
    DejemInterestUpsert,
    DejemMonthCreate,
    DejemMonthGeneratePreview,
    DejemMonthGenerateRequest,
    DejemMonthGenerateResult,
    DejemMonthPublic,
    DejemMonthUpdate,
    DejemMyDayDetail,
    DejemParticipantAdminRow,
    DejemShiftCalendarResponse,
    DejemShiftCreate,
    DejemShiftDashboard,
    DejemShiftDayDetail,
    DejemShiftPublic,
    DejemShiftTemplateCreate,
    DejemShiftTemplatePublic,
    DejemShiftTemplateUpdate,
    DejemShiftUpdate,
)
from services import dejem_enrollment_service as enroll_svc
from services import dejem_month_generator_service as gen_svc
from services import dejem_service as svc
from services import dejem_shift_service as shift_svc
from services.dejem_service import DejemError

router = APIRouter(prefix="/dejem", tags=["dejem"])


def _http_error(exc: DejemError) -> HTTPException:
    code = status.HTTP_400_BAD_REQUEST
    msg = str(exc)
    if "não encontrad" in msg.lower():
        code = status.HTTP_404_NOT_FOUND
    return HTTPException(status_code=code, detail=msg)


@router.get("/")
def dejem_root(_: User = Depends(get_current_approved_user)) -> dict[str, str]:
    return {"module": "dejem", "phase": "4.6", "status": "map-force-integration"}


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


# --- Shifts (admin calendar) ---


@router.get("/shifts/calendar", response_model=DejemShiftCalendarResponse)
def shift_calendar(
    year: int,
    month: int,
    _: User = Depends(require_dejem_shift_viewer),
    db: Session = Depends(get_db),
) -> DejemShiftCalendarResponse:
    if month < 1 or month > 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mês inválido")
    return shift_svc.build_shift_calendar(db, year, month)


@router.get("/shifts/day", response_model=DejemShiftDayDetail)
def shift_day_detail(
    year: int,
    month: int,
    day: int,
    _: User = Depends(require_dejem_shift_viewer),
    db: Session = Depends(get_db),
) -> DejemShiftDayDetail:
    try:
        return shift_svc.get_day_detail(db, year, month, day)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/months/{month_id}/shifts", response_model=list[DejemShiftPublic])
def list_month_shifts(
    month_id: int,
    _: User = Depends(require_dejem_shift_viewer),
    db: Session = Depends(get_db),
) -> list[DejemShiftPublic]:
    try:
        return shift_svc.list_month_shifts(db, month_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.get("/months/{month_id}/shifts/dashboard", response_model=DejemShiftDashboard)
def shift_dashboard(
    month_id: int,
    _: User = Depends(require_dejem_shift_viewer),
    db: Session = Depends(get_db),
) -> DejemShiftDashboard:
    try:
        return shift_svc.get_shift_dashboard(db, month_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.post("/shifts", response_model=DejemShiftPublic, status_code=status.HTTP_201_CREATED)
def create_shift(
    body: DejemShiftCreate,
    current: User = Depends(require_dejem_shift_editor),
    db: Session = Depends(get_db),
) -> DejemShiftPublic:
    try:
        return shift_svc.create_shift(db, current, body)
    except DejemError as e:
        raise _http_error(e) from e


@router.post("/shifts/generate/preview", response_model=DejemMonthGeneratePreview)
def preview_month_shifts(
    body: DejemMonthGenerateRequest,
    _: User = Depends(require_dejem_shift_editor),
    db: Session = Depends(get_db),
) -> DejemMonthGeneratePreview:
    try:
        return gen_svc.preview_month_shifts(db, body)
    except DejemError as e:
        raise _http_error(e) from e


@router.post("/shifts/generate", response_model=DejemMonthGenerateResult)
def generate_month_shifts(
    body: DejemMonthGenerateRequest,
    current: User = Depends(require_dejem_shift_editor),
    db: Session = Depends(get_db),
) -> DejemMonthGenerateResult:
    try:
        return gen_svc.generate_month_shifts(db, current, body)
    except DejemError as e:
        raise _http_error(e) from e


# --- Enrollment (fase 4.5) — rotas específicas antes de /shifts/{shift_id} ---


@router.get("/my/calendar", response_model=DejemShiftCalendarResponse)
def my_shift_calendar(
    year: int,
    month: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> DejemShiftCalendarResponse:
    return shift_svc.build_shift_calendar(db, year, month)


@router.get("/my/day", response_model=DejemMyDayDetail)
def my_shift_day(
    year: int,
    month: int,
    day: int,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> DejemMyDayDetail:
    from datetime import date as Date

    from repositories.dejem_repository import DejemMonthRepository

    d = Date(year, month, day)
    month_entity = DejemMonthRepository(db).get_by_year_month(year, month)
    cards = enroll_svc.get_my_day_cards(db, current, year, month, day)
    return DejemMyDayDetail(
        date=d,
        month_id=month_entity.id if month_entity else None,
        shifts=cards,
    )


@router.post("/shifts/{shift_id}/enroll", response_model=DejemEnrollmentResult)
def enroll_in_shift(
    shift_id: int,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> DejemEnrollmentResult:
    try:
        return enroll_svc.enroll_self(db, current, shift_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.delete("/shifts/{shift_id}/enroll", response_model=DejemEnrollmentResult)
def cancel_shift_enrollment(
    shift_id: int,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> DejemEnrollmentResult:
    try:
        return enroll_svc.cancel_self(db, current, shift_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.get("/shifts/{shift_id}/participants", response_model=list[DejemParticipantAdminRow])
def list_shift_participants(
    shift_id: int,
    _: User = Depends(require_dejem_shift_viewer),
    db: Session = Depends(get_db),
) -> list[DejemParticipantAdminRow]:
    try:
        return enroll_svc.list_participants_admin(db, shift_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.post(
    "/shifts/{shift_id}/participants",
    response_model=DejemEnrollmentResult,
    status_code=status.HTTP_201_CREATED,
)
def add_shift_participant(
    shift_id: int,
    body: DejemAdminAddParticipant,
    current: User = Depends(require_dejem_shift_editor),
    db: Session = Depends(get_db),
) -> DejemEnrollmentResult:
    try:
        return enroll_svc.admin_add_participant(db, current, shift_id, body)
    except DejemError as e:
        raise _http_error(e) from e


@router.delete(
    "/shifts/{shift_id}/participants/{user_id}",
    response_model=DejemEnrollmentResult,
)
def remove_shift_participant(
    shift_id: int,
    user_id: int,
    current: User = Depends(require_dejem_shift_editor),
    db: Session = Depends(get_db),
) -> DejemEnrollmentResult:
    try:
        return enroll_svc.admin_remove_participant(db, current, shift_id, user_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.post("/shifts/{shift_id}/close", response_model=DejemShiftPublic)
def close_dejem_shift(
    shift_id: int,
    current: User = Depends(require_dejem_shift_editor),
    db: Session = Depends(get_db),
) -> DejemShiftPublic:
    try:
        return enroll_svc.close_shift(db, current, shift_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.get("/shifts/{shift_id}", response_model=DejemShiftPublic)
def get_shift(
    shift_id: int,
    _: User = Depends(require_dejem_shift_viewer),
    db: Session = Depends(get_db),
) -> DejemShiftPublic:
    try:
        return shift_svc.get_shift(db, shift_id)
    except DejemError as e:
        raise _http_error(e) from e


@router.patch("/shifts/{shift_id}", response_model=DejemShiftPublic)
def update_shift(
    shift_id: int,
    body: DejemShiftUpdate,
    current: User = Depends(require_dejem_shift_editor),
    db: Session = Depends(get_db),
) -> DejemShiftPublic:
    try:
        return shift_svc.update_shift(db, shift_id, body, actor=current)
    except DejemError as e:
        raise _http_error(e) from e


@router.delete("/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift(
    shift_id: int,
    _: User = Depends(require_dejem_shift_editor),
    db: Session = Depends(get_db),
) -> Response:
    try:
        shift_svc.delete_shift(db, shift_id)
    except DejemError as e:
        raise _http_error(e) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Templates ---


@router.get("/shift-templates", response_model=list[DejemShiftTemplatePublic])
def list_shift_templates(
    active_only: bool = False,
    _: User = Depends(require_dejem_shift_viewer),
    db: Session = Depends(get_db),
) -> list[DejemShiftTemplatePublic]:
    return shift_svc.list_templates(db, active_only=active_only)


@router.post(
    "/shift-templates",
    response_model=DejemShiftTemplatePublic,
    status_code=status.HTTP_201_CREATED,
)
def create_shift_template(
    body: DejemShiftTemplateCreate,
    current: User = Depends(require_dejem_shift_editor),
    db: Session = Depends(get_db),
) -> DejemShiftTemplatePublic:
    try:
        return shift_svc.create_template(db, current, body)
    except DejemError as e:
        raise _http_error(e) from e


@router.patch("/shift-templates/{template_id}", response_model=DejemShiftTemplatePublic)
def update_shift_template(
    template_id: int,
    body: DejemShiftTemplateUpdate,
    _: User = Depends(require_dejem_shift_editor),
    db: Session = Depends(get_db),
) -> DejemShiftTemplatePublic:
    try:
        return shift_svc.update_template(db, template_id, body)
    except DejemError as e:
        raise _http_error(e) from e


@router.delete("/shift-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift_template(
    template_id: int,
    _: User = Depends(require_dejem_shift_editor),
    db: Session = Depends(get_db),
) -> Response:
    try:
        shift_svc.delete_template(db, template_id)
    except DejemError as e:
        raise _http_error(e) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)
