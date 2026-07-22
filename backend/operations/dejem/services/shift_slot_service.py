"""ShiftSlotService — CRUD de turnos e capacidade (Sprint C8)."""

from __future__ import annotations

from datetime import date as DateValue

from sqlalchemy.orm import Session

from models.user import User
from operations.dejem.models.enums import ShiftSlotStatus
from operations.dejem.models.shift_slot import ShiftSlot
from operations.dejem.repositories.campaign_repository import CampaignRepository
from operations.dejem.repositories.shift_slot_repository import ShiftSlotRepository
from operations.dejem.schemas.shift_slot import (
    ShiftSlotAvailabilityResponse,
    ShiftSlotCreate,
    ShiftSlotResponse,
    ShiftSlotUpdate,
)
from operations.dejem.services.publication_lock import raise_if_campaign_locked
from operations.dejem.services.opening_capacity import (
    OpeningCapacityError,
    assert_can_open_capacity,
)

class ShiftSlotError(ValueError):
    pass

class ShiftSlotService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ShiftSlotRepository(db)
        self.campaigns = CampaignRepository(db)

    def list(
        self,
        campaign_id: int,
        *,
        on_date: DateValue | None = None,
        status: ShiftSlotStatus | None = None,
    ) -> list[ShiftSlotResponse]:
        self._require_campaign(campaign_id)
        return [
            self._to_response(r)
            for r in self.repo.list_by_campaign(
                campaign_id,
                on_date=on_date,
                status=status,
            )
        ]

    def availability(self, campaign_id: int) -> ShiftSlotAvailabilityResponse:
        self._require_campaign(campaign_id)
        rows = self.repo.list_available(campaign_id)
        slots = [self._to_response(r) for r in rows]
        return ShiftSlotAvailabilityResponse(
            campaign_id=campaign_id,
            slots=slots,
            total_remaining=sum(s.remaining_slots for s in slots),
        )

    def get(self, slot_id: int) -> ShiftSlotResponse:
        return self._to_response(self._get_or_raise(slot_id))

    def create(self, _actor: User, body: ShiftSlotCreate) -> ShiftSlotResponse:
        self._require_campaign(body.campaign_id)
        raise_if_campaign_locked(self.db, body.campaign_id, ShiftSlotError)
        if body.status == ShiftSlotStatus.FULL:
            raise ShiftSlotError("Novo turno não pode nascer FULL; use OPEN ou CLOSED.")

        try:
            assert_can_open_capacity(
                self.db,
                body.campaign_id,
                body.total_slots,
                action="criar",
            )
        except OpeningCapacityError as e:
            raise ShiftSlotError(str(e)) from e

        row = ShiftSlot(
            campaign_id=body.campaign_id,
            date=body.date,
            start_time=body.start_time,
            end_time=body.end_time,
            total_slots=body.total_slots,
            reserved_slots=0,
            remaining_slots=body.total_slots,
            status=body.status,
        )
        if row.status != ShiftSlotStatus.CLOSED:
            row.sync_capacity()
        self.repo.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def update(self, slot_id: int, _actor: User, body: ShiftSlotUpdate) -> ShiftSlotResponse:
        row = self._get_or_raise(slot_id)
        raise_if_campaign_locked(self.db, row.campaign_id, ShiftSlotError)

        if body.date is not None:
            row.date = body.date
        if body.start_time is not None:
            row.start_time = body.start_time
        if body.end_time is not None:
            row.end_time = body.end_time
        if body.total_slots is not None:
            if body.total_slots < row.reserved_slots:
                raise ShiftSlotError(
                    f"total_slots ({body.total_slots}) não pode ser menor que "
                    f"reserved_slots ({row.reserved_slots})."
                )
            if body.total_slots > row.total_slots:
                try:
                    assert_can_open_capacity(
                        self.db,
                        row.campaign_id,
                        body.total_slots,
                        exclude_slot_id=row.id,
                        action="editar",
                    )
                except OpeningCapacityError as e:
                    raise ShiftSlotError(str(e)) from e
            row.total_slots = body.total_slots

        end_t = body.end_time if body.end_time is not None else row.end_time
        start_t = body.start_time if body.start_time is not None else row.start_time
        if end_t <= start_t:
            raise ShiftSlotError("end_time deve ser posterior a start_time.")

        if body.status is not None:
            if body.status == ShiftSlotStatus.FULL and row.remaining_slots > 0:
                raise ShiftSlotError(
                    "Não marque FULL manualmente enquanto houver remaining_slots."
                )
            row.status = body.status

        if row.status != ShiftSlotStatus.CLOSED:
            row.sync_capacity()
        else:
            row.remaining_slots = max(0, row.total_slots - row.reserved_slots)

        self.repo.save(row)
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def delete(self, slot_id: int, _actor: User) -> None:
        row = self._get_or_raise(slot_id)
        raise_if_campaign_locked(self.db, row.campaign_id, ShiftSlotError)
        if row.reserved_slots > 0:
            raise ShiftSlotError(
                "Não é possível excluir turno com reservas ativas. "
                "Cancele as reservas antes."
            )
        self.repo.delete(row)
        self.db.commit()

    def _get_or_raise(self, slot_id: int) -> ShiftSlot:
        row = self.repo.get(slot_id)
        if not row:
            raise ShiftSlotError("ShiftSlot não encontrado.")
        return row

    def _require_campaign(self, campaign_id: int) -> None:
        if not self.campaigns.get(campaign_id):
            raise ShiftSlotError("Campanha DEJEM não encontrada.")

    def _to_response(self, row: ShiftSlot) -> ShiftSlotResponse:
        return ShiftSlotResponse.model_validate(row)
