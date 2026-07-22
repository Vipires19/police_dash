"""API routers da fundação DEJEM (`/operations/dejem`)."""

from fastapi import APIRouter

from operations.dejem.api.allocations import router as allocations_router
from operations.dejem.api.campaigns import router as campaigns_router
from operations.dejem.api.credits import router as credits_router
from operations.dejem.api.interests import router as interests_router
from operations.dejem.api.offers import router as offers_router
from operations.dejem.api.shift_slots import router as shift_slots_router
from operations.dejem.api.teams import router as teams_router
from operations.dejem.api.publications import router as publications_router

router = APIRouter(prefix="/operations/dejem", tags=["operations-dejem"])
router.include_router(campaigns_router)
router.include_router(offers_router)
router.include_router(interests_router)
router.include_router(allocations_router)
router.include_router(credits_router)
router.include_router(shift_slots_router)
router.include_router(teams_router)
router.include_router(publications_router)

__all__ = ["router"]
