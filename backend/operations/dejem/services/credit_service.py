"""CreditService — CRUD (C4) + Lifecycle (C7) + Reserva ShiftSlot (C8).

C8 não altera a state machine: reserva é associação Credit.shift_slot_id
enquanto o crédito permanece APPROVED.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.user import User
from operations.dejem.models.allocation_audit import CreditStatusAudit
from operations.dejem.models.credit import Credit
from operations.dejem.models.credit_state_machine import (
    CreditStateMachine,
    CreditStateMachineError,
    CreditTransitionOrigin,
)
from operations.dejem.models.enums import CreditStatus, ShiftSlotStatus
from operations.dejem.models.reservation_audit import CreditReservationAudit
from operations.dejem.models.shift_slot import ShiftSlot
from operations.dejem.repositories.allocation_repository import AllocationRepository
from operations.dejem.repositories.campaign_repository import CampaignRepository
from operations.dejem.repositories.credit_repository import CreditRepository
from operations.dejem.repositories.shift_slot_repository import ShiftSlotRepository
from operations.dejem.schemas.credit import (
    CreditAuditResponse,
    CreditCreate,
    CreditResponse,
    CreditUpdate,
)
from operations.dejem.services.publication_lock import raise_if_campaign_locked


class CreditError(ValueError):
    pass


class CreditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CreditRepository(db)
        self.allocations = AllocationRepository(db)
        self.campaigns = CampaignRepository(db)
        self.slots = ShiftSlotRepository(db)

    def list_by_campaign(self, campaign_id: int) -> list[CreditResponse]:
        self._require_campaign(campaign_id)
        return [self._to_response(r) for r in self.repo.list_by_campaign(campaign_id)]

    def list_by_officer(self, police_officer_id: int) -> list[CreditResponse]:
        return [self._to_response(r) for r in self.repo.list_by_officer(police_officer_id)]

    def get(self, credit_id: int) -> CreditResponse:
        return self._to_response(self._get_or_raise(credit_id))

    def get_for_actor(self, credit_id: int, actor: User, *, admin: bool) -> CreditResponse:
        row = self._get_or_raise(credit_id)
        if not admin and row.police_officer_id != actor.id:
            raise CreditError("Sem permissão para consultar este crédito.")
        return self._to_response(row)

    def create(self, actor: User, body: CreditCreate) -> CreditResponse:
        self._require_campaign(body.campaign_id)
        allocation = self.allocations.get(body.allocation_id)
        if not allocation:
            raise CreditError("Allocation não encontrada.")
        if allocation.month_id != body.campaign_id:
            raise CreditError("Allocation não pertence à campanha informada.")
        if allocation.user_id != body.police_officer_id:
            raise CreditError("Allocation não pertence ao policial informado.")
        if body.status != CreditStatus.AVAILABLE:
            raise CreditError("Novos créditos devem nascer como AVAILABLE.")

        row = Credit(
            allocation_id=body.allocation_id,
            campaign_id=body.campaign_id,
            police_officer_id=body.police_officer_id,
            status=CreditStatus.AVAILABLE,
        )
        self.repo.add(row)
        self._audit(
            credit_id=row.id,
            campaign_id=row.campaign_id,
            actor_id=actor.id,
            from_status=None,
            to_status=CreditStatus.AVAILABLE,
            origin=CreditTransitionOrigin.ADMIN,
            reason="credit_created",
        )
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def update_status(
        self,
        credit_id: int,
        actor: User,
        body: CreditUpdate,
    ) -> CreditResponse:
        """Transição genérica (admin) — sempre via state machine."""
        return self._apply_transition(
            credit_id,
            actor,
            body.status,
            origin=CreditTransitionOrigin.MANUAL,
            reason=body.reason,
            require_owner=False,
            commit=True,
        )

    def select_date(
        self,
        credit_id: int,
        actor: User,
        reason: str | None = None,
    ) -> CreditResponse:
        return self._apply_transition(
            credit_id,
            actor,
            CreditStatus.DATE_SELECTED,
            origin=CreditTransitionOrigin.POLICE,
            reason=reason or "select_date",
            require_owner=True,
            commit=True,
        )

    def release(
        self,
        credit_id: int,
        actor: User,
        reason: str | None = None,
    ) -> CreditResponse:
        return self._apply_transition(
            credit_id,
            actor,
            CreditStatus.AVAILABLE,
            origin=CreditTransitionOrigin.POLICE,
            reason=reason or "release",
            require_owner=True,
            commit=True,
        )

    def request_approval(
        self,
        credit_id: int,
        actor: User,
        reason: str | None = None,
    ) -> CreditResponse:
        return self._apply_transition(
            credit_id,
            actor,
            CreditStatus.PENDING_APPROVAL,
            origin=CreditTransitionOrigin.POLICE,
            reason=reason or "request_approval",
            require_owner=True,
            commit=True,
        )

    def approve(
        self,
        credit_id: int,
        actor: User,
        reason: str | None = None,
    ) -> CreditResponse:
        return self._apply_transition(
            credit_id,
            actor,
            CreditStatus.APPROVED,
            origin=CreditTransitionOrigin.ADMIN,
            reason=reason or "approve",
            require_owner=False,
            commit=True,
        )

    def cancel(
        self,
        credit_id: int,
        actor: User,
        reason: str | None = None,
        *,
        origin: CreditTransitionOrigin = CreditTransitionOrigin.ADMIN,
        commit: bool = True,
    ) -> CreditResponse:
        return self._apply_transition(
            credit_id,
            actor,
            CreditStatus.CANCELLED,
            origin=origin,
            reason=reason or "cancel",
            require_owner=False,
            commit=commit,
        )

    def execute(
        self,
        credit_id: int,
        actor: User,
        reason: str | None = None,
    ) -> CreditResponse:
        return self._apply_transition(
            credit_id,
            actor,
            CreditStatus.EXECUTED,
            origin=CreditTransitionOrigin.ADMIN,
            reason=reason or "execute",
            require_owner=False,
            commit=True,
        )

    # --- Reserva ShiftSlot (C8) — não muda CreditStatus ---

    def reserve(
        self,
        credit_id: int,
        actor: User,
        shift_slot_id: int,
        reason: str | None = None,
    ) -> CreditResponse:
        credit = self._lock_credit(credit_id)
        self._assert_owner(credit, actor)
        raise_if_campaign_locked(self.db, credit.campaign_id, CreditError)
        self._assert_can_reserve(credit)
        if credit.shift_slot_id is not None:
            raise CreditError("Crédito já possui reserva. Use change-slot.")

        slot = self._lock_slot_for_reservation(shift_slot_id, credit.campaign_id)
        self._consume_slot(slot)
        credit.shift_slot_id = slot.id
        self.repo.save(credit)
        self._reservation_audit(
            credit=credit,
            actor=actor,
            from_slot_id=None,
            to_slot_id=slot.id,
            action="RESERVE",
            reason=reason or "reserve",
            origin=CreditTransitionOrigin.POLICE,
        )
        self.db.commit()
        self.db.refresh(credit)
        return self._to_response(credit)

    def change_slot(
        self,
        credit_id: int,
        actor: User,
        shift_slot_id: int,
        reason: str | None = None,
    ) -> CreditResponse:
        credit = self._lock_credit(credit_id)
        self._assert_owner(credit, actor)
        raise_if_campaign_locked(self.db, credit.campaign_id, CreditError)
        self._assert_can_change_reservation(credit)
        if credit.shift_slot_id is None:
            raise CreditError("Crédito sem reserva. Use reserve.")
        if credit.shift_slot_id == shift_slot_id:
            raise CreditError("Crédito já está reservado neste turno.")

        old_id = credit.shift_slot_id
        # Lock em ordem estável para evitar deadlock
        first_id, second_id = sorted((old_id, shift_slot_id))
        first = self._lock_slot_for_reservation(first_id, credit.campaign_id, allow_full_release=True)
        second = self._lock_slot_for_reservation(second_id, credit.campaign_id, allow_full_release=True)
        old_slot = first if first.id == old_id else second
        new_slot = second if second.id == shift_slot_id else first

        if new_slot.status == ShiftSlotStatus.CLOSED:
            raise CreditError("Turno fechado para novas reservas.")
        if new_slot.remaining_slots <= 0 or new_slot.status == ShiftSlotStatus.FULL:
            raise CreditError("Turno sem vagas disponíveis.")

        self._release_slot(old_slot)
        self._consume_slot(new_slot)
        credit.shift_slot_id = new_slot.id
        self.repo.save(credit)
        self._reservation_audit(
            credit=credit,
            actor=actor,
            from_slot_id=old_id,
            to_slot_id=new_slot.id,
            action="CHANGE",
            reason=reason or "change_slot",
            origin=CreditTransitionOrigin.POLICE,
        )
        self.db.commit()
        self.db.refresh(credit)
        return self._to_response(credit)

    def cancel_reservation(
        self,
        credit_id: int,
        actor: User,
        reason: str | None = None,
    ) -> CreditResponse:
        credit = self._lock_credit(credit_id)
        self._assert_owner(credit, actor)
        raise_if_campaign_locked(self.db, credit.campaign_id, CreditError)
        self._assert_can_change_reservation(credit)
        if credit.shift_slot_id is None:
            raise CreditError("Crédito não possui reserva.")

        old_id = credit.shift_slot_id
        slot = self._lock_slot_for_reservation(
            old_id,
            credit.campaign_id,
            allow_full_release=True,
        )
        self._release_slot(slot)
        credit.shift_slot_id = None
        self.repo.save(credit)
        self._reservation_audit(
            credit=credit,
            actor=actor,
            from_slot_id=old_id,
            to_slot_id=None,
            action="CANCEL",
            reason=reason or "cancel_reservation",
            origin=CreditTransitionOrigin.POLICE,
        )
        # Status permanece APPROVED
        self.db.commit()
        self.db.refresh(credit)
        return self._to_response(credit)

    def list_reservation_audits(self, credit_id: int) -> list[ReservationAuditResponse]:
        self._get_or_raise(credit_id)
        return [
            ReservationAuditResponse.model_validate(r)
            for r in self.slots.list_reservation_audits(credit_id)
        ]

    def delete(self, credit_id: int, _actor: User) -> None:
        row = self._get_or_raise(credit_id)
        if row.shift_slot_id is not None:
            raise CreditError("Cancele a reserva do crédito antes de excluí-lo.")
        self.repo.delete(row)
        self.db.commit()

    def list_audits(self, credit_id: int) -> list[CreditAuditResponse]:
        self._get_or_raise(credit_id)
        return [
            CreditAuditResponse.model_validate(r)
            for r in self.repo.list_status_audits(credit_id)
        ]

    def history(self, credit_id: int) -> list[CreditAuditResponse]:
        return self.list_audits(credit_id)

    def _apply_transition(
        self,
        credit_id: int,
        actor: User,
        target: CreditStatus,
        *,
        origin: CreditTransitionOrigin,
        reason: str | None,
        require_owner: bool,
        commit: bool = True,
    ) -> CreditResponse:
        row = self._get_or_raise(credit_id)

        if require_owner and row.police_officer_id != actor.id:
            raise CreditError("Somente o policial titular pode executar esta ação.")

        if row.status == CreditStatus.APPROVED and target == CreditStatus.CANCELLED:
            if origin not in {
                CreditTransitionOrigin.ADMIN,
                CreditTransitionOrigin.MANUAL,
            }:
                raise CreditError("APPROVED só pode ser cancelado por administrador.")

        try:
            transition = CreditStateMachine.transition(
                row.status,
                target,
                origin=origin,
                reason=reason,
            )
        except CreditStateMachineError as exc:
            raise CreditError(str(exc)) from exc

        # Liberar reserva ao cancelar crédito (capacidade); EXECUTED mantém o vínculo.
        if (
            transition.to_status == CreditStatus.CANCELLED
            and row.shift_slot_id is not None
        ):
            old_id = row.shift_slot_id
            slot = self.slots.get_for_update(old_id)
            if slot:
                self._release_slot(slot)
            row.shift_slot_id = None
            self._reservation_audit(
                credit=row,
                actor=actor,
                from_slot_id=old_id,
                to_slot_id=None,
                action="RELEASE_ON_CANCEL",
                reason=reason or "credit_cancelled",
                origin=origin,
            )

        previous = row.status
        row.status = transition.to_status
        self.repo.save(row)
        self._audit(
            credit_id=row.id,
            campaign_id=row.campaign_id,
            actor_id=actor.id,
            from_status=previous,
            to_status=transition.to_status,
            origin=transition.origin,
            reason=transition.reason,
        )
        if commit:
            self.db.commit()
            self.db.refresh(row)
        return self._to_response(row)

    def _lock_credit(self, credit_id: int) -> Credit:
        row = self.repo.get_for_update(credit_id)
        if not row:
            raise CreditError("Crédito não encontrado.")
        return row

    def _lock_slot_for_reservation(
        self,
        slot_id: int,
        campaign_id: int,
        *,
        allow_full_release: bool = False,
    ) -> ShiftSlot:
        slot = self.slots.get_for_update(slot_id)
        if not slot:
            raise CreditError("ShiftSlot não encontrado.")
        if slot.campaign_id != campaign_id:
            raise CreditError("Turno não pertence à campanha do crédito.")
        if not allow_full_release and slot.status == ShiftSlotStatus.CLOSED:
            raise CreditError("Turno fechado para novas reservas.")
        if not allow_full_release and (
            slot.remaining_slots <= 0 or slot.status == ShiftSlotStatus.FULL
        ):
            raise CreditError("Turno sem vagas disponíveis.")
        return slot

    def _consume_slot(self, slot: ShiftSlot) -> None:
        if slot.status == ShiftSlotStatus.CLOSED:
            raise CreditError("Turno fechado para novas reservas.")
        if slot.reserved_slots >= slot.total_slots or slot.remaining_slots <= 0:
            raise CreditError("Turno sem vagas disponíveis.")
        slot.reserved_slots += 1
        slot.sync_capacity()
        self.slots.save(slot)

    def _release_slot(self, slot: ShiftSlot) -> None:
        if slot.reserved_slots > 0:
            slot.reserved_slots -= 1
        slot.sync_capacity()
        self.slots.save(slot)

    def _assert_owner(self, credit: Credit, actor: User) -> None:
        if credit.police_officer_id != actor.id:
            raise CreditError("Somente o policial titular pode executar esta ação.")

    def _assert_can_reserve(self, credit: Credit) -> None:
        if credit.status == CreditStatus.EXECUTED:
            raise CreditError("Crédito EXECUTED não pode reservar turno.")
        if credit.status == CreditStatus.CANCELLED:
            raise CreditError("Crédito CANCELLED não pode reservar turno.")
        if credit.status == CreditStatus.AVAILABLE:
            raise CreditError("Crédito AVAILABLE não pode reservar turno.")
        if credit.status != CreditStatus.APPROVED:
            raise CreditError(
                f"Somente créditos APPROVED podem reservar "
                f"(atual={credit.status.value})."
            )

    def _assert_can_change_reservation(self, credit: Credit) -> None:
        if credit.status == CreditStatus.EXECUTED:
            raise CreditError("Crédito EXECUTED não pode alterar reserva.")
        if credit.status != CreditStatus.APPROVED:
            raise CreditError(
                "Troca/cancelamento de reserva somente com crédito APPROVED."
            )

    def _reservation_audit(
        self,
        *,
        credit: Credit,
        actor: User,
        from_slot_id: int | None,
        to_slot_id: int | None,
        action: str,
        reason: str | None,
        origin: CreditTransitionOrigin,
    ) -> None:
        self.slots.add_reservation_audit(
            CreditReservationAudit(
                credit_id=credit.id,
                campaign_id=credit.campaign_id,
                actor_id=actor.id,
                from_shift_slot_id=from_slot_id,
                to_shift_slot_id=to_slot_id,
                action=action,
                reason=reason,
                origin=origin.value,
            )
        )

    def _audit(
        self,
        *,
        credit_id: int,
        campaign_id: int,
        actor_id: int,
        from_status: CreditStatus | None,
        to_status: CreditStatus,
        origin: CreditTransitionOrigin | None = None,
        reason: str | None = None,
    ) -> None:
        self.repo.add_status_audit(
            CreditStatusAudit(
                credit_id=credit_id,
                campaign_id=campaign_id,
                actor_id=actor_id,
                from_status=from_status.value if from_status else None,
                to_status=to_status.value,
                reason=reason,
                origin=origin.value if origin else None,
            )
        )

    def _get_or_raise(self, credit_id: int) -> Credit:
        row = self.repo.get(credit_id)
        if not row:
            raise CreditError("Crédito não encontrado.")
        return row

    def _require_campaign(self, campaign_id: int) -> None:
        if not self.campaigns.get(campaign_id):
            raise CreditError("Campanha DEJEM não encontrada.")

    def _to_response(self, row: Credit) -> CreditResponse:
        return CreditResponse.model_validate(row)
