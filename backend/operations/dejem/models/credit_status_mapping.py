"""Reexport da máquina de estados (compatibilidade C4)."""

from operations.dejem.models.credit_state_machine import (
    ALLOWED_CREDIT_TRANSITIONS,
    ALLOWED_TRANSITIONS,
    CreditStateMachine,
    CreditStateMachineError,
    CreditTransition,
    CreditTransitionOrigin,
    assert_credit_transition,
)

__all__ = [
    "ALLOWED_CREDIT_TRANSITIONS",
    "ALLOWED_TRANSITIONS",
    "CreditStateMachine",
    "CreditStateMachineError",
    "CreditTransition",
    "CreditTransitionOrigin",
    "assert_credit_transition",
]
