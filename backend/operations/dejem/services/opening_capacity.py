"""Limite de abertura de vagas da campanha DEJEM.

A soma das capacidades abertas (DejemShift + ShiftSlot) não pode
ultrapassar o total disponível da campanha (OfferEvents / projeção).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.dejem import DejemShift
from operations.dejem.models.shift_slot import ShiftSlot
from operations.dejem.repositories.campaign_repository import CampaignRepository
from operations.dejem.repositories.offer_repository import OfferRepository


class OpeningCapacityError(ValueError):
    pass


def campaign_total_slots(db: Session, campaign_id: int) -> int:
    """Total de vagas da campanha: OfferEvents, com fallback na projeção do mês."""
    campaign = CampaignRepository(db).get(campaign_id)
    if campaign is None:
        raise OpeningCapacityError("Campanha DEJEM não encontrada.")
    from_events = OfferRepository(db).sum_quantity(campaign_id)
    if from_events > 0:
        return from_events
    return max(0, int(campaign.total_available_slots or 0))


def opened_capacity(
    db: Session,
    campaign_id: int,
    *,
    exclude_shift_id: int | None = None,
    exclude_slot_id: int | None = None,
) -> int:
    """Soma das capacidades já abertas na campanha (escalas + turnos)."""
    shift_stmt = select(func.coalesce(func.sum(DejemShift.capacity), 0)).where(
        DejemShift.month_id == campaign_id
    )
    if exclude_shift_id is not None:
        shift_stmt = shift_stmt.where(DejemShift.id != exclude_shift_id)
    shifts_total = int(db.scalar(shift_stmt) or 0)

    slot_stmt = select(func.coalesce(func.sum(ShiftSlot.total_slots), 0)).where(
        ShiftSlot.campaign_id == campaign_id
    )
    if exclude_slot_id is not None:
        slot_stmt = slot_stmt.where(ShiftSlot.id != exclude_slot_id)
    slots_total = int(db.scalar(slot_stmt) or 0)

    return shifts_total + slots_total


def remaining_opening_slots(
    db: Session,
    campaign_id: int,
    *,
    exclude_shift_id: int | None = None,
    exclude_slot_id: int | None = None,
) -> int:
    total = campaign_total_slots(db, campaign_id)
    opened = opened_capacity(
        db,
        campaign_id,
        exclude_shift_id=exclude_shift_id,
        exclude_slot_id=exclude_slot_id,
    )
    return max(0, total - opened)


def assert_can_open_capacity(
    db: Session,
    campaign_id: int,
    requested: int,
    *,
    exclude_shift_id: int | None = None,
    exclude_slot_id: int | None = None,
    action: str = "criar",
) -> None:
    """Garante que ``requested`` cabe no saldo restante para abertura."""
    if requested < 0:
        raise OpeningCapacityError("A capacidade não pode ser negativa.")
    remaining = remaining_opening_slots(
        db,
        campaign_id,
        exclude_shift_id=exclude_shift_id,
        exclude_slot_id=exclude_slot_id,
    )
    if requested > remaining:
        verb = "criar" if action == "criar" else "editar"
        raise OpeningCapacityError(
            f"Não é possível {verb} esta escala. A campanha possui apenas "
            f"{remaining} vagas disponíveis para abertura."
        )


def opening_capacity_snapshot(db: Session, campaign_id: int) -> tuple[int, int, int]:
    """Retorna (total_campanha, vagas_abertas, restantes_para_abertura)."""
    total = campaign_total_slots(db, campaign_id)
    opened = opened_capacity(db, campaign_id)
    return total, opened, max(0, total - opened)
