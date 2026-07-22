"""OfferService — gestão de oferta via OfferEvents (Sprint C4).

Fonte da verdade: soma dos eventos. `dejem_months.total_available_slots`
é apenas projeção para compatibilidade com o legado.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.user import User
from operations.dejem.models.enums import OfferEventType
from operations.dejem.models.offer_event import OfferEvent
from operations.dejem.repositories.campaign_repository import CampaignRepository
from operations.dejem.repositories.offer_repository import OfferRepository
from operations.dejem.schemas.offer_event import (
    OfferAvailableResponse,
    OfferEventCreate,
    OfferEventResponse,
    OfferEventUpdate,
)


class OfferError(ValueError):
    pass


class OfferService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = OfferRepository(db)
        self.campaigns = CampaignRepository(db)

    def list_by_campaign(self, campaign_id: int) -> list[OfferEventResponse]:
        self._require_campaign(campaign_id)
        return [self._to_response(r) for r in self.repo.list_by_campaign(campaign_id)]

    def history(self, campaign_id: int) -> list[OfferEventResponse]:
        return self.list_by_campaign(campaign_id)

    def get(self, offer_id: int) -> OfferEventResponse:
        row = self.repo.get(offer_id)
        if not row:
            raise OfferError("OfferEvent não encontrado.")
        return self._to_response(row)

    def available(self, campaign_id: int) -> OfferAvailableResponse:
        self._require_campaign(campaign_id)
        return OfferAvailableResponse(
            campaign_id=campaign_id,
            available_slots=self.repo.sum_quantity(campaign_id),
            events_count=self.repo.count_by_campaign(campaign_id),
        )

    def create(self, actor: User, body: OfferEventCreate) -> OfferEventResponse:
        campaign = self._require_campaign(body.campaign_id)
        signed = self._signed_quantity(body.event_type, body.quantity)
        current = self.repo.sum_quantity(campaign.id)
        if current + signed < 0:
            raise OfferError(
                f"Oferta resultante não pode ser negativa "
                f"(atual={current}, delta={signed})."
            )

        row = OfferEvent(
            campaign_id=campaign.id,
            event_type=body.event_type,
            quantity=signed,
            reason=body.reason,
            created_by=actor.id,
        )
        self.repo.add(row)
        self._sync_projection(campaign.id)
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def update_reason(self, offer_id: int, body: OfferEventUpdate) -> OfferEventResponse:
        row = self.repo.get(offer_id)
        if not row:
            raise OfferError("OfferEvent não encontrado.")
        if body.reason is not None:
            row.reason = body.reason
        self.repo.save(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def delete(self, offer_id: int) -> None:
        row = self.repo.get(offer_id)
        if not row:
            raise OfferError("OfferEvent não encontrado.")
        campaign_id = row.campaign_id
        self.repo.delete(row)
        if self.repo.sum_quantity(campaign_id) < 0:
            self.db.rollback()
            raise OfferError("Remoção deixaria a oferta negativa.")
        self._sync_projection(campaign_id)
        self.db.commit()

    def _sync_projection(self, campaign_id: int) -> None:
        campaign = self.campaigns.get(campaign_id)
        if campaign is None:
            return
        campaign.total_available_slots = self.repo.sum_quantity(campaign_id)
        self.campaigns.save(campaign)

    def _require_campaign(self, campaign_id: int):
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise OfferError("Campanha DEJEM não encontrada.")
        return campaign

    @staticmethod
    def _signed_quantity(event_type: OfferEventType, quantity: int) -> int:
        if event_type == OfferEventType.INCREASE:
            if quantity <= 0:
                raise OfferError("INCREASE exige quantity > 0.")
            return quantity
        if event_type == OfferEventType.DECREASE:
            if quantity <= 0:
                raise OfferError("DECREASE exige quantity > 0 (magnitude).")
            return -quantity
        # ADJUSTMENT: signed as provided
        if quantity == 0:
            raise OfferError("ADJUSTMENT exige quantity != 0.")
        return quantity

    def _to_response(self, row: OfferEvent) -> OfferEventResponse:
        return OfferEventResponse.model_validate(row)
