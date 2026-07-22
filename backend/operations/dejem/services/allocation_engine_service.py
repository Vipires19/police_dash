"""AllocationEngineService — orquestra distribuição igualitária (C5)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.dejem import DejemAllocation
from models.user import User
from operations.dejem.models.allocation_audit import AllocationAudit
from operations.dejem.models.campaign_audit import CampaignStatusAudit
from operations.dejem.models.credit import Credit
from operations.dejem.models.enums import CampaignStatus, CreditStatus
from operations.dejem.models.status_mapping import assert_transition, from_legacy, to_legacy
from operations.dejem.repositories.allocation_repository import AllocationRepository
from operations.dejem.repositories.campaign_repository import CampaignRepository
from operations.dejem.repositories.credit_repository import CreditRepository
from operations.dejem.repositories.interest_repository import InterestRepository
from operations.dejem.repositories.offer_repository import OfferRepository
from operations.dejem.schemas.allocation import AllocationResponse
from operations.dejem.schemas.credit import CreditResponse
from operations.dejem.schemas.engine import (
    AllocateResponse,
    AllocationSummaryResponse,
    RemainingSlotsResponse,
)
from operations.dejem.services.allocation_engine import equal_distribute


class AllocationEngineError(ValueError):
    pass


class AllocationEngineService:
    """Gera Allocations + Credits. Sem redistribuição / datas / escalas."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.campaigns = CampaignRepository(db)
        self.offers = OfferRepository(db)
        self.interests = InterestRepository(db)
        self.allocations = AllocationRepository(db)
        self.credits = CreditRepository(db)

    def allocate(self, actor: User, campaign_id: int) -> AllocateResponse:
        campaign = self.campaigns.get_for_update(campaign_id)
        if not campaign:
            raise AllocationEngineError("Campanha DEJEM não encontrada.")
        status = from_legacy(campaign.status)

        if status not in {
            CampaignStatus.REGISTRATION_CLOSED,
            CampaignStatus.OPEN,
        }:
            raise AllocationEngineError(
                f"Distribuição não permitida no status {status.value}. "
                "Use campanha OPEN ou REGISTRATION_CLOSED."
            )

        existing_allocs = self.allocations.list_by_campaign(campaign_id)
        existing_credits = self.credits.list_by_campaign(campaign_id)
        if existing_allocs or existing_credits:
            raise AllocationEngineError(
                "Campanha já possui distribuição. "
                "Recriação/redistribuição não está disponível nesta sprint."
            )

        available = self._available_slots(campaign_id, campaign.total_available_slots)
        if available <= 0:
            raise AllocationEngineError("Não há vagas disponíveis para distribuir.")

        interested = self.interests.list_by_campaign(campaign_id, only_interested=True)
        officer_ids = [row.user_id for row in interested]
        if not officer_ids:
            raise AllocationEngineError("Não há policiais interessados nesta campanha.")

        result = equal_distribute(available, officer_ids)
        if result.distributed_slots == 0:
            raise AllocationEngineError(
                "Oferta insuficiente para atribuir ao menos 1 vaga por interessado "
                f"(available={available}, interested={result.interested_count})."
            )

        created_allocs: list[DejemAllocation] = []
        credits_created = 0

        for officer_id in sorted(result.allocations.keys()):
            slots = result.allocations[officer_id]
            alloc = DejemAllocation(
                month_id=campaign_id,
                user_id=officer_id,
                allocated_slots=slots,
                used_slots=0,
                remaining_slots=slots,
            )
            self.allocations.add(alloc)
            created_allocs.append(alloc)

            for _ in range(slots):
                self.credits.add(
                    Credit(
                        allocation_id=alloc.id,
                        campaign_id=campaign_id,
                        police_officer_id=officer_id,
                        status=CreditStatus.AVAILABLE,
                    )
                )
                credits_created += 1

        campaign.undistributed_slots = result.remaining_slots
        campaign.total_available_slots = available

        if status == CampaignStatus.OPEN:
            self._transition_status(
                campaign,
                actor_id=actor.id,
                current=CampaignStatus.OPEN,
                target=CampaignStatus.REGISTRATION_CLOSED,
            )
            status = CampaignStatus.REGISTRATION_CLOSED

        if status == CampaignStatus.REGISTRATION_CLOSED:
            self._transition_status(
                campaign,
                actor_id=actor.id,
                current=CampaignStatus.REGISTRATION_CLOSED,
                target=CampaignStatus.ALLOCATED,
            )

        self.campaigns.save(campaign)
        self.allocations.add_audit(
            AllocationAudit(
                allocation_id=None,
                campaign_id=campaign_id,
                actor_id=actor.id,
                action="ENGINE_ALLOCATE",
                details=(
                    f"distributed={result.distributed_slots} "
                    f"remaining={result.remaining_slots} "
                    f"per={result.slots_per_officer} "
                    f"officers={result.interested_count} "
                    f"credits={credits_created}"
                ),
            )
        )

        if credits_created != result.distributed_slots:
            self.db.rollback()
            raise AllocationEngineError("Inconsistência: créditos != vagas distribuídas.")
        if sum(a.allocated_slots for a in created_allocs) != result.distributed_slots:
            self.db.rollback()
            raise AllocationEngineError("Inconsistência: soma allocations != distribuídas.")
        if result.distributed_slots + result.remaining_slots != available:
            self.db.rollback()
            raise AllocationEngineError("Inconsistência: distribuídas + remaining != oferta.")

        self.db.commit()
        for alloc in created_allocs:
            self.db.refresh(alloc)

        return AllocateResponse(
            campaign_id=campaign_id,
            available_slots=available,
            interested_count=result.interested_count,
            slots_per_officer=result.slots_per_officer,
            distributed_slots=result.distributed_slots,
            remaining_slots=result.remaining_slots,
            allocations_created=len(created_allocs),
            credits_created=credits_created,
            allocations=[self._alloc_response(a) for a in created_allocs],
        )

    def summary(self, campaign_id: int) -> AllocationSummaryResponse:
        campaign = self._require_campaign(campaign_id)
        available = self._available_slots(campaign_id, campaign.total_available_slots)
        allocs = self.allocations.list_by_campaign(campaign_id)
        credits = self.credits.list_by_campaign(campaign_id)
        distributed = sum(a.allocated_slots for a in allocs)
        interested = len(
            self.interests.list_by_campaign(campaign_id, only_interested=True)
        )
        per: int | None = None
        if allocs:
            values = {a.allocated_slots for a in allocs}
            per = next(iter(values)) if len(values) == 1 else None

        return AllocationSummaryResponse(
            campaign_id=campaign_id,
            available_slots=available,
            interested_count=interested,
            allocations_count=len(allocs),
            credits_count=len(credits),
            distributed_slots=distributed,
            remaining_slots=campaign.undistributed_slots,
            slots_per_officer=per,
            is_distributed=bool(allocs),
        )

    def remaining(self, campaign_id: int) -> RemainingSlotsResponse:
        campaign = self._require_campaign(campaign_id)
        available = self._available_slots(campaign_id, campaign.total_available_slots)
        allocs = self.allocations.list_by_campaign(campaign_id)
        distributed = sum(a.allocated_slots for a in allocs)
        return RemainingSlotsResponse(
            campaign_id=campaign_id,
            available_slots=available,
            distributed_slots=distributed,
            remaining_slots=campaign.undistributed_slots,
        )

    def list_credits(self, campaign_id: int) -> list[CreditResponse]:
        self._require_campaign(campaign_id)
        return [
            CreditResponse.model_validate(c)
            for c in self.credits.list_by_campaign(campaign_id)
        ]

    def _available_slots(self, campaign_id: int, fallback: int) -> int:
        from_events = self.offers.sum_quantity(campaign_id)
        if from_events > 0:
            return from_events
        return max(0, fallback)

    def _require_campaign(self, campaign_id: int):
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise AllocationEngineError("Campanha DEJEM não encontrada.")
        return campaign

    def _transition_status(
        self,
        campaign,
        *,
        actor_id: int,
        current: CampaignStatus,
        target: CampaignStatus,
    ) -> None:
        try:
            assert_transition(current, target)
        except ValueError as exc:
            raise AllocationEngineError(str(exc)) from exc
        campaign.status = to_legacy(target)
        self.campaigns.add_status_audit(
            CampaignStatusAudit(
                campaign_id=campaign.id,
                actor_id=actor_id,
                from_status=current.value,
                to_status=target.value,
            )
        )

    def _alloc_response(self, row: DejemAllocation) -> AllocationResponse:
        return AllocationResponse(
            id=row.id,
            campaign_id=row.month_id,
            police_officer_id=row.user_id,
            allocated_slots=row.allocated_slots,
            used_slots=row.used_slots,
            remaining_slots=row.remaining_slots,
            created_at=row.created_at,
        )
