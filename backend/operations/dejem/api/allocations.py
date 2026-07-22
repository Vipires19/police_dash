"""Router Allocations — CRUD (C4) + Allocation Engine (C5)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from auth.dependencies import require_dejem_admin
from database.session import get_db
from operations.dejem.api.http_errors import domain_http_error
from models.user import User
from operations.dejem.schemas.allocation import (
    AllocationAuditResponse,
    AllocationCreate,
    AllocationResponse,
    AllocationUpdate,
)
from operations.dejem.schemas.credit import CreditResponse
from operations.dejem.schemas.engine import (
    AllocateRequest,
    AllocateResponse,
    AllocationSummaryResponse,
    RemainingSlotsResponse,
)
from operations.dejem.services.allocation_engine_service import (
    AllocationEngineError,
    AllocationEngineService,
)
from operations.dejem.services.allocation_service import AllocationError, AllocationService
from operations.dejem.services.incremental_allocation_service import (
    IncrementalAllocationError,
    IncrementalAllocationService,
)
from operations.dejem.schemas.incremental import (
    IncrementalAuditResponse,
    IncrementalPreviewResponse,
    IncrementalRequest,
    IncrementalResultResponse,
)

router = APIRouter(prefix="/allocations", tags=["operations-dejem-allocations"])

# --- Allocation Engine (C5) — rotas estáticas antes de /{id} ---

@router.post("/allocate", response_model=AllocateResponse, status_code=status.HTTP_201_CREATED)
def allocate_campaign(
    body: AllocateRequest,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> AllocateResponse:
    """Distribuição igualitária. Não redistribui sobras. Idempotente (bloqueia reexecução)."""
    try:
        return AllocationEngineService(db).allocate(current, body.campaign_id)
    except AllocationEngineError as e:
        raise domain_http_error(e) from e

@router.get("/allocation-summary", response_model=AllocationSummaryResponse)
def allocation_summary(
    campaign_id: int = Query(...),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> AllocationSummaryResponse:
    try:
        return AllocationEngineService(db).summary(campaign_id)
    except AllocationEngineError as e:
        raise domain_http_error(e) from e

@router.get("/remaining", response_model=RemainingSlotsResponse)
def remaining_slots(
    campaign_id: int = Query(...),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> RemainingSlotsResponse:
    try:
        return AllocationEngineService(db).remaining(campaign_id)
    except AllocationEngineError as e:
        raise domain_http_error(e) from e

@router.get("/credits", response_model=list[CreditResponse])
def list_allocation_credits(
    campaign_id: int = Query(...),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[CreditResponse]:
    try:
        return AllocationEngineService(db).list_credits(campaign_id)
    except AllocationEngineError as e:
        raise domain_http_error(e) from e

# --- Incremental Engine (C6) ---

@router.post("/incremental", response_model=IncrementalResultResponse)
def run_incremental(
    body: IncrementalRequest,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> IncrementalResultResponse:
    """Processa aumento/redução de oferta e novos interessados de forma incremental."""
    try:
        return IncrementalAllocationService(db).run_incremental(
            current,
            body.campaign_id,
            reason=body.reason,
        )
    except IncrementalAllocationError as e:
        raise domain_http_error(e) from e

@router.post("/redistribute-remaining", response_model=IncrementalResultResponse)
def redistribute_remaining(
    body: IncrementalRequest,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> IncrementalResultResponse:
    """Redistribui apenas ``undistributed_slots`` por antiguidade."""
    try:
        return IncrementalAllocationService(db).redistribute_remaining(
            current,
            body.campaign_id,
            reason=body.reason,
        )
    except IncrementalAllocationError as e:
        raise domain_http_error(e) from e

@router.get("/preview", response_model=IncrementalPreviewResponse)
def incremental_preview(
    campaign_id: int = Query(...),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> IncrementalPreviewResponse:
    try:
        return IncrementalAllocationService(db).preview(campaign_id)
    except IncrementalAllocationError as e:
        raise domain_http_error(e) from e

@router.get("/audit", response_model=list[IncrementalAuditResponse])
def incremental_audit(
    campaign_id: int = Query(...),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[IncrementalAuditResponse]:
    try:
        return IncrementalAllocationService(db).list_audits(campaign_id)
    except IncrementalAllocationError as e:
        raise domain_http_error(e) from e

# --- CRUD infra (C4) ---

@router.get("/audits", response_model=list[AllocationAuditResponse])
def list_allocation_audits(
    campaign_id: int = Query(...),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[AllocationAuditResponse]:
    try:
        return AllocationService(db).list_audits(campaign_id)
    except AllocationError as e:
        raise domain_http_error(e) from e

@router.get("/", response_model=list[AllocationResponse])
def list_allocations(
    campaign_id: int = Query(...),
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> list[AllocationResponse]:
    try:
        return AllocationService(db).list_by_campaign(campaign_id)
    except AllocationError as e:
        raise domain_http_error(e) from e

@router.get("/{allocation_id}", response_model=AllocationResponse)
def get_allocation(
    allocation_id: int,
    _: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> AllocationResponse:
    try:
        return AllocationService(db).get(allocation_id)
    except AllocationError as e:
        raise domain_http_error(e) from e

@router.post("/", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
def create_allocation(
    body: AllocationCreate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> AllocationResponse:
    """Cria allocation manualmente. NÃO executa algoritmo de distribuição."""
    try:
        return AllocationService(db).create(current, body)
    except AllocationError as e:
        raise domain_http_error(e) from e

@router.put("/{allocation_id}", response_model=AllocationResponse)
def update_allocation(
    allocation_id: int,
    body: AllocationUpdate,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> AllocationResponse:
    try:
        return AllocationService(db).update(allocation_id, current, body)
    except AllocationError as e:
        raise domain_http_error(e) from e

@router.delete("/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_allocation(
    allocation_id: int,
    current: User = Depends(require_dejem_admin),
    db: Session = Depends(get_db),
) -> Response:
    try:
        AllocationService(db).delete(allocation_id, current)
    except AllocationError as e:
        raise domain_http_error(e) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)
