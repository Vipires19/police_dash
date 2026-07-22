"""IncrementalAllocationService — atualizações incrementais (Sprint C6).

Preserva Allocations/Credits existentes. Não recalcula a campanha.
Não altera o Allocation Engine inicial (C5).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.dejem import DejemAllocation
from models.user import User
from operations.dejem.models.allocation_audit import AllocationAudit
from operations.dejem.models.credit import Credit
from operations.dejem.models.credit_state_machine import CreditTransitionOrigin
from operations.dejem.models.enums import CampaignStatus, CreditStatus
from operations.dejem.models.status_mapping import from_legacy
from operations.dejem.repositories.allocation_repository import AllocationRepository
from operations.dejem.repositories.campaign_repository import CampaignRepository
from operations.dejem.repositories.credit_repository import CreditRepository
from operations.dejem.repositories.interest_repository import InterestRepository
from operations.dejem.repositories.offer_repository import OfferRepository
from operations.dejem.schemas.incremental import (
    IncrementalAuditResponse,
    IncrementalPreviewResponse,
    IncrementalResultResponse,
)
from operations.dejem.services.credit_service import CreditService
from operations.dejem.services.incremental_engine import (
    PriorityCandidate,
    distribute_by_seniority,
)


class IncrementalAllocationError(ValueError):
    pass


_INCREMENTAL_ACTIONS = frozenset(
    {
        "INCREMENTAL",
        "REDISTRIBUTE_REMAINING",
        "OFFER_EXCESS",
        "RELEASE_AVAILABLE",
    }
)


class IncrementalAllocationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.campaigns = CampaignRepository(db)
        self.offers = OfferRepository(db)
        self.interests = InterestRepository(db)
        self.allocations = AllocationRepository(db)
        self.credits = CreditRepository(db)

    def preview(self, campaign_id: int) -> IncrementalPreviewResponse:
        campaign = self._require_distributed_campaign(campaign_id)
        available = self._available(campaign_id, campaign.total_available_slots)
        distributed = self._distributed(campaign_id)
        undistributed = campaign.undistributed_slots
        unaccounted = max(0, available - distributed - undistributed)
        excess = max(0, distributed - available)
        without_alloc = len(self._interested_without_allocation(campaign_id))

        pool = unaccounted + undistributed
        candidates = self._priority_candidates(campaign_id)
        result = distribute_by_seniority(pool, candidates) if pool > 0 else None

        return IncrementalPreviewResponse(
            campaign_id=campaign_id,
            available_slots=available,
            distributed_slots=distributed,
            undistributed_slots=undistributed,
            unaccounted_slots=unaccounted,
            offer_excess_slots=max(campaign.offer_excess_slots, excess),
            interested_without_allocation=without_alloc,
            would_distribute=result.distributed if result else 0,
            would_remain=result.remaining if result else pool,
            has_inconsistency=excess > 0 or campaign.offer_excess_slots > 0,
        )

    def run_incremental(
        self,
        actor: User,
        campaign_id: int,
        reason: str | None = None,
    ) -> IncrementalResultResponse:
        """
        Processa:
        - aumento de oferta (unaccounted);
        - novos interessados via pool (unaccounted + undistributed);
        - redução de oferta (registra excess, não remove créditos).
        """
        campaign = self._require_distributed_campaign(campaign_id)
        available = self._available(campaign_id, campaign.total_available_slots)
        distributed = self._distributed(campaign_id)
        undistributed = campaign.undistributed_slots

        # Redução: oferta < créditos já concedidos
        if available < distributed:
            excess = distributed - available
            campaign.offer_excess_slots = excess
            campaign.undistributed_slots = 0
            campaign.total_available_slots = available
            self.campaigns.save(campaign)
            self._audit(
                campaign_id=campaign_id,
                actor_id=actor.id,
                action="OFFER_EXCESS",
                details=(
                    f"reason={reason or 'offer_reduction'} "
                    f"available={available} distributed={distributed} excess={excess}"
                ),
            )
            self.db.commit()
            return IncrementalResultResponse(
                campaign_id=campaign_id,
                reason=reason,
                available_slots=available,
                slots_processed=0,
                credits_created=0,
                allocations_updated=0,
                allocations_created=0,
                undistributed_slots=0,
                offer_excess_slots=excess,
                message=(
                    "Oferta menor que créditos já concedidos. "
                    "Inconsistência registrada; créditos não foram removidos."
                ),
            )

        unaccounted = available - distributed - undistributed
        if unaccounted < 0:
            # Ajuste de consistência: undistributed maior que deveria
            undistributed = available - distributed
            campaign.undistributed_slots = undistributed
            unaccounted = 0

        pool = unaccounted + undistributed
        if pool <= 0:
            campaign.offer_excess_slots = 0
            campaign.total_available_slots = available
            self.campaigns.save(campaign)
            self.db.commit()
            return IncrementalResultResponse(
                campaign_id=campaign_id,
                reason=reason,
                available_slots=available,
                slots_processed=0,
                credits_created=0,
                allocations_updated=0,
                allocations_created=0,
                undistributed_slots=undistributed,
                offer_excess_slots=0,
                noop=True,
                message="Nada a processar (estado já consistente).",
            )

        candidates = self._priority_candidates(campaign_id)
        result = distribute_by_seniority(pool, candidates)
        stats = self._apply_grants(campaign_id, result.grants)

        campaign.undistributed_slots = result.remaining
        campaign.offer_excess_slots = 0
        campaign.total_available_slots = available
        self.campaigns.save(campaign)
        self._audit(
            campaign_id=campaign_id,
            actor_id=actor.id,
            action="INCREMENTAL",
            details=(
                f"reason={reason or 'incremental'} "
                f"pool={pool} distributed={result.distributed} "
                f"remaining={result.remaining} "
                f"credits_created={stats['credits_created']} "
                f"alloc_updated={stats['allocations_updated']} "
                f"alloc_created={stats['allocations_created']}"
            ),
        )
        self.db.commit()

        return IncrementalResultResponse(
            campaign_id=campaign_id,
            reason=reason,
            available_slots=available,
            slots_processed=result.distributed,
            credits_created=stats["credits_created"],
            allocations_updated=stats["allocations_updated"],
            allocations_created=stats["allocations_created"],
            undistributed_slots=result.remaining,
            offer_excess_slots=0,
        )

    def redistribute_remaining(
        self,
        actor: User,
        campaign_id: int,
        reason: str | None = None,
    ) -> IncrementalResultResponse:
        """Consome apenas ``undistributed_slots``."""
        campaign = self._require_distributed_campaign(campaign_id)
        pool = campaign.undistributed_slots
        available = self._available(campaign_id, campaign.total_available_slots)

        if pool <= 0:
            return IncrementalResultResponse(
                campaign_id=campaign_id,
                reason=reason,
                available_slots=available,
                slots_processed=0,
                credits_created=0,
                allocations_updated=0,
                allocations_created=0,
                undistributed_slots=0,
                offer_excess_slots=campaign.offer_excess_slots,
                noop=True,
                message="Sem vagas remanescentes para redistribuir.",
            )

        candidates = self._priority_candidates(campaign_id)
        result = distribute_by_seniority(pool, candidates)
        stats = self._apply_grants(campaign_id, result.grants)

        campaign.undistributed_slots = result.remaining
        self.campaigns.save(campaign)
        self._audit(
            campaign_id=campaign_id,
            actor_id=actor.id,
            action="REDISTRIBUTE_REMAINING",
            details=(
                f"reason={reason or 'redistribute_remaining'} "
                f"pool={pool} distributed={result.distributed} "
                f"remaining={result.remaining} "
                f"credits_created={stats['credits_created']}"
            ),
        )
        self.db.commit()

        return IncrementalResultResponse(
            campaign_id=campaign_id,
            reason=reason,
            available_slots=available,
            slots_processed=result.distributed,
            credits_created=stats["credits_created"],
            allocations_updated=stats["allocations_updated"],
            allocations_created=stats["allocations_created"],
            undistributed_slots=result.remaining,
            offer_excess_slots=campaign.offer_excess_slots,
        )

    def release_available_credits(
        self,
        actor: User,
        campaign_id: int,
        police_officer_id: int,
        reason: str | None = None,
    ) -> IncrementalResultResponse:
        """
        Cancela créditos AVAILABLE do policial e devolve à sobra.
        Não afeta APPROVED / EXECUTED / DATE_SELECTED / PENDING_APPROVAL.
        """
        campaign = self._require_campaign_before_running(campaign_id)
        available_credits = [
            c
            for c in self.credits.list_by_campaign(campaign_id)
            if c.police_officer_id == police_officer_id
            and c.status == CreditStatus.AVAILABLE
        ]
        if not available_credits:
            return IncrementalResultResponse(
                campaign_id=campaign_id,
                reason=reason,
                available_slots=self._available(campaign_id, campaign.total_available_slots),
                slots_processed=0,
                credits_created=0,
                allocations_updated=0,
                allocations_created=0,
                undistributed_slots=campaign.undistributed_slots,
                offer_excess_slots=campaign.offer_excess_slots,
                credits_released=0,
                noop=True,
                message="Nenhum crédito AVAILABLE para liberar.",
            )

        released = 0
        alloc = self.allocations.get_by_campaign_and_officer(campaign_id, police_officer_id)
        credit_svc = CreditService(self.db)
        for credit in available_credits:
            credit_svc.cancel(
                credit.id,
                actor,
                reason=reason or "interest_cancel",
                origin=CreditTransitionOrigin.INCREMENTAL,
                commit=False,
            )
            released += 1

        campaign = self._require_campaign(campaign_id)
        alloc = self.allocations.get_by_campaign_and_officer(campaign_id, police_officer_id)
        if alloc and released > 0:
            # recalcular allocated a partir de créditos ativos
            active = [
                c
                for c in self.credits.list_by_campaign(campaign_id)
                if c.police_officer_id == police_officer_id
                and c.status != CreditStatus.CANCELLED
            ]
            alloc.allocated_slots = len(active)
            alloc.remaining_slots = max(0, alloc.allocated_slots - alloc.used_slots)
            self.allocations.save(alloc)

        campaign.undistributed_slots += released
        self.campaigns.save(campaign)
        self._audit(
            campaign_id=campaign_id,
            actor_id=actor.id,
            action="RELEASE_AVAILABLE",
            details=(
                f"reason={reason or 'interest_cancel'} "
                f"officer={police_officer_id} released={released}"
            ),
        )
        self.db.commit()

        return IncrementalResultResponse(
            campaign_id=campaign_id,
            reason=reason,
            available_slots=self._available(campaign_id, campaign.total_available_slots),
            slots_processed=0,
            credits_created=0,
            allocations_updated=1 if alloc and released else 0,
            allocations_created=0,
            undistributed_slots=campaign.undistributed_slots,
            offer_excess_slots=campaign.offer_excess_slots,
            credits_released=released,
        )

    def list_audits(self, campaign_id: int) -> list[IncrementalAuditResponse]:
        self._require_campaign(campaign_id)
        rows = [
            r
            for r in self.allocations.list_audits(campaign_id)
            if r.action in _INCREMENTAL_ACTIONS or r.action == "ENGINE_ALLOCATE"
        ]
        return [IncrementalAuditResponse.model_validate(r) for r in rows]

    def _apply_grants(
        self,
        campaign_id: int,
        grants: dict[int, int],
    ) -> dict[str, int]:
        credits_created = 0
        allocations_updated = 0
        allocations_created = 0

        for officer_id, slots in sorted(grants.items()):
            if slots <= 0:
                continue
            alloc = self.allocations.get_by_campaign_and_officer(campaign_id, officer_id)
            if alloc is None:
                alloc = DejemAllocation(
                    month_id=campaign_id,
                    user_id=officer_id,
                    allocated_slots=slots,
                    used_slots=0,
                    remaining_slots=slots,
                )
                self.allocations.add(alloc)
                allocations_created += 1
            else:
                alloc.allocated_slots += slots
                alloc.remaining_slots = alloc.allocated_slots - alloc.used_slots
                self.allocations.save(alloc)
                allocations_updated += 1

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

        return {
            "credits_created": credits_created,
            "allocations_updated": allocations_updated,
            "allocations_created": allocations_created,
        }

    def _priority_candidates(self, campaign_id: int) -> list[PriorityCandidate]:
        interests = self.interests.list_by_campaign(campaign_id, only_interested=True)
        out: list[PriorityCandidate] = []
        for row in interests:
            user = row.user
            if user is None:
                continue
            out.append(
                PriorityCandidate(
                    police_officer_id=row.user_id,
                    patente=user.patente or "",
                    display_order=user.display_order,
                    nome_guerra=user.nome_guerra or "",
                )
            )
        # Fallback: se interesse sem user carregado, usa só id
        if not out:
            for row in interests:
                out.append(
                    PriorityCandidate(
                        police_officer_id=row.user_id,
                        patente="",
                        display_order=0,
                        nome_guerra="",
                    )
                )
        return out

    def _interested_without_allocation(self, campaign_id: int) -> list[int]:
        allocated_ids = {a.user_id for a in self.allocations.list_by_campaign(campaign_id)}
        return [
            i.user_id
            for i in self.interests.list_by_campaign(campaign_id, only_interested=True)
            if i.user_id not in allocated_ids
        ]

    def _distributed(self, campaign_id: int) -> int:
        # Conta créditos ativos (não cancelados) como verdade da distribuição
        credits = self.credits.list_by_campaign(campaign_id)
        return sum(1 for c in credits if c.status != CreditStatus.CANCELLED)

    def _available(self, campaign_id: int, fallback: int) -> int:
        from_events = self.offers.sum_quantity(campaign_id)
        if from_events > 0:
            return from_events
        return max(0, fallback)

    def _require_campaign(self, campaign_id: int):
        campaign = self.campaigns.get_for_update(campaign_id)
        if not campaign:
            raise IncrementalAllocationError("Campanha DEJEM não encontrada.")
        return campaign

    def _require_distributed_campaign(self, campaign_id: int):
        campaign = self._require_campaign(campaign_id)
        status = from_legacy(campaign.status)
        if status not in {CampaignStatus.ALLOCATED, CampaignStatus.RUNNING}:
            # Também permite se já houver allocations (pós C5)
            if not self.allocations.list_by_campaign(campaign_id):
                raise IncrementalAllocationError(
                    "Processamento incremental exige campanha já distribuída (ALLOCATED)."
                )
        return campaign

    def _require_campaign_before_running(self, campaign_id: int):
        campaign = self._require_campaign(campaign_id)
        status = from_legacy(campaign.status)
        if status in {CampaignStatus.RUNNING, CampaignStatus.CLOSED}:
            raise IncrementalAllocationError(
                "Não é possível liberar créditos após início da campanha (RUNNING/CLOSED)."
            )
        return campaign

    def _audit(
        self,
        *,
        campaign_id: int,
        actor_id: int,
        action: str,
        details: str | None,
    ) -> None:
        self.allocations.add_audit(
            AllocationAudit(
                allocation_id=None,
                campaign_id=campaign_id,
                actor_id=actor_id,
                action=action,
                details=details,
            )
        )
