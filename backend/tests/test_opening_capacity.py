"""Testes do limite de abertura de vagas da campanha DEJEM."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from operations.dejem.services.opening_capacity import (
    OpeningCapacityError,
    assert_can_open_capacity,
    campaign_total_slots,
    remaining_opening_slots,
)


def test_campaign_total_prefers_offer_events(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(
        "operations.dejem.services.opening_capacity.CampaignRepository",
        lambda _db: SimpleNamespace(
            get=lambda _id: SimpleNamespace(id=1, total_available_slots=100),
        ),
    )
    monkeypatch.setattr(
        "operations.dejem.services.opening_capacity.OfferRepository",
        lambda _db: SimpleNamespace(sum_quantity=lambda _id: 80),
    )
    assert campaign_total_slots(db, 1) == 80


def test_campaign_total_fallback_to_month(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(
        "operations.dejem.services.opening_capacity.CampaignRepository",
        lambda _db: SimpleNamespace(
            get=lambda _id: SimpleNamespace(id=1, total_available_slots=97),
        ),
    )
    monkeypatch.setattr(
        "operations.dejem.services.opening_capacity.OfferRepository",
        lambda _db: SimpleNamespace(sum_quantity=lambda _id: 0),
    )
    assert campaign_total_slots(db, 1) == 97


def test_assert_blocks_when_insufficient(monkeypatch):
    monkeypatch.setattr(
        "operations.dejem.services.opening_capacity.remaining_opening_slots",
        lambda *_a, **_k: 4,
    )
    with pytest.raises(OpeningCapacityError) as exc:
        assert_can_open_capacity(MagicMock(), 1, 8, action="criar")
    assert "apenas 4 vagas disponíveis para abertura" in str(exc.value)


def test_assert_allows_when_fits(monkeypatch):
    monkeypatch.setattr(
        "operations.dejem.services.opening_capacity.remaining_opening_slots",
        lambda *_a, **_k: 4,
    )
    assert_can_open_capacity(MagicMock(), 1, 4, action="criar")


def test_remaining_opening_slots_math(monkeypatch):
    monkeypatch.setattr(
        "operations.dejem.services.opening_capacity.campaign_total_slots",
        lambda *_a, **_k: 100,
    )
    monkeypatch.setattr(
        "operations.dejem.services.opening_capacity.opened_capacity",
        lambda *_a, **_k: 96,
    )
    assert remaining_opening_slots(MagicMock(), 1) == 4
