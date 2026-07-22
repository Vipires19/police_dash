"""Bloqueio de planejamento após publicação ACTIVE (C10 / R1)."""

from __future__ import annotations

from typing import TypeVar

from sqlalchemy.orm import Session

from operations.dejem.repositories.published_schedule_repository import (
    PublishedScheduleRepository,
)

E = TypeVar("E", bound=Exception)


class CampaignPublishedLockError(ValueError):
    pass


_LOCK_MSG = (
    "Campanha {campaign_id} possui publicação ACTIVE (v{version}). "
    "Desbloqueie com POST /republish {{unlock_for_revision:true}}, "
    "edite o planejamento e publique novamente."
)


def assert_campaign_not_locked(db: Session, campaign_id: int) -> None:
    """Impede mutações de equipes/turnos enquanto houver publicação ACTIVE."""
    active = PublishedScheduleRepository(db).get_active(campaign_id)
    if active:
        raise CampaignPublishedLockError(
            _LOCK_MSG.format(campaign_id=campaign_id, version=active.version)
        )


def raise_if_campaign_locked(
    db: Session,
    campaign_id: int,
    error_cls: type[E],
) -> None:
    """Re-lança o lock como o tipo de erro do serviço chamador."""
    try:
        assert_campaign_not_locked(db, campaign_id)
    except CampaignPublishedLockError as exc:
        raise error_cls(str(exc)) from exc


def campaign_is_locked(db: Session, campaign_id: int) -> bool:
    return PublishedScheduleRepository(db).get_active(campaign_id) is not None
