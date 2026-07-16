"""Contexto Actor/Target para God Mode (ADMIN atua em nome de outro policial)."""

from __future__ import annotations

from dataclasses import dataclass

from models.audit import AuditOrigin
from models.user import User

ACT_AS_HEADER = "X-Act-As-User-Id"


@dataclass(frozen=True, slots=True)
class ActingContext:
    """Actor executa; Target é o dono do registro."""

    actor: User
    target: User
    origin: AuditOrigin

    @property
    def is_acting_as(self) -> bool:
        return self.actor.id != self.target.id

    @classmethod
    def self(cls, user: User) -> ActingContext:
        return cls(actor=user, target=user, origin=AuditOrigin.SELF)

    @classmethod
    def admin_as(cls, actor: User, target: User) -> ActingContext:
        return cls(actor=actor, target=target, origin=AuditOrigin.ADMIN)
