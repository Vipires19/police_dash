"""CreditStateMachine — única fonte de verdade das transições (Sprint C7)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from operations.dejem.models.enums import CreditStatus


class CreditTransitionOrigin(str, Enum):
    """Origem da operação de mudança de estado."""

    POLICE = "POLICE"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"
    INCREMENTAL = "INCREMENTAL"
    MANUAL = "MANUAL"


# Transições válidas — C7 (explícitas; sem condicionais espalhados).
ALLOWED_TRANSITIONS: dict[CreditStatus, frozenset[CreditStatus]] = {
    CreditStatus.AVAILABLE: frozenset(
        {CreditStatus.DATE_SELECTED, CreditStatus.CANCELLED}
    ),
    CreditStatus.DATE_SELECTED: frozenset(
        {CreditStatus.AVAILABLE, CreditStatus.PENDING_APPROVAL}
    ),
    CreditStatus.PENDING_APPROVAL: frozenset(
        {CreditStatus.APPROVED, CreditStatus.CANCELLED}
    ),
    CreditStatus.APPROVED: frozenset(
        {CreditStatus.EXECUTED, CreditStatus.CANCELLED}
    ),
    CreditStatus.EXECUTED: frozenset(),
    CreditStatus.CANCELLED: frozenset(),
}


@dataclass(frozen=True)
class CreditTransition:
    from_status: CreditStatus
    to_status: CreditStatus
    origin: CreditTransitionOrigin
    reason: str | None = None


class CreditStateMachineError(ValueError):
    """Transição de crédito inválida."""


class CreditStateMachine:
    """Valida e descreve transições. Não persiste."""

    @classmethod
    def can_transition(cls, current: CreditStatus, target: CreditStatus) -> bool:
        if current == target:
            return False
        return target in ALLOWED_TRANSITIONS.get(current, frozenset())

    @classmethod
    def assert_transition(
        cls,
        current: CreditStatus,
        target: CreditStatus,
    ) -> None:
        if current == CreditStatus.EXECUTED:
            raise CreditStateMachineError(
                "Crédito EXECUTED é terminal e não pode mudar de estado."
            )
        if current == target:
            raise CreditStateMachineError(f"Crédito já está em {current.value}.")
        allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
        if target not in allowed:
            opts = ", ".join(sorted(s.value for s in allowed)) or "nenhuma"
            raise CreditStateMachineError(
                f"Transição inválida: {current.value} -> {target.value}. "
                f"Permitidas: {opts}."
            )

    @classmethod
    def transition(
        cls,
        current: CreditStatus,
        target: CreditStatus,
        *,
        origin: CreditTransitionOrigin,
        reason: str | None = None,
    ) -> CreditTransition:
        cls.assert_transition(current, target)
        # Regras extras de domínio
        if current == CreditStatus.AVAILABLE and target == CreditStatus.EXECUTED:
            raise CreditStateMachineError(
                "AVAILABLE nunca pode ir diretamente para EXECUTED."
            )
        return CreditTransition(
            from_status=current,
            to_status=target,
            origin=origin,
            reason=reason,
        )


# Compatibilidade com imports C4/C6
def assert_credit_transition(current: CreditStatus, target: CreditStatus) -> None:
    CreditStateMachine.assert_transition(current, target)


ALLOWED_CREDIT_TRANSITIONS = ALLOWED_TRANSITIONS
