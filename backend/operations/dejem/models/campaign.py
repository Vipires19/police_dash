"""Campaign — alias conceitual de `DejemMonth` (sem tabela duplicada)."""

from __future__ import annotations

from models.dejem import DejemMonth as Campaign
from models.dejem import DejemMonthStatus as LegacyCampaignStatus

from operations.dejem.models.enums import CampaignStatus

__all__ = ["Campaign", "CampaignStatus", "LegacyCampaignStatus"]
