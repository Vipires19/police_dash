"""CampaignRepository — persistência de campanhas (`dejem_months`)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.dejem import DejemMonthStatus
from operations.dejem.models.campaign import Campaign
from operations.dejem.models.campaign_audit import CampaignStatusAudit


class CampaignRepository:
    """Acesso a campanhas. Commit fica no service."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, campaign_id: int) -> Campaign | None:
        return self.db.get(Campaign, campaign_id)

    def get_for_update(self, campaign_id: int) -> Campaign | None:
        """Lock de linha para allocate / publish (anti-corrida)."""
        stmt = (
            select(Campaign)
            .where(Campaign.id == campaign_id)
            .with_for_update()
        )
        return self.db.scalars(stmt).first()

    def get_by_year_month(self, year: int, month: int) -> Campaign | None:
        stmt = select(Campaign).where(Campaign.year == year, Campaign.month == month)
        return self.db.scalars(stmt).first()

    def list_all(self) -> list[Campaign]:
        stmt = select(Campaign).order_by(Campaign.year.desc(), Campaign.month.desc())
        return list(self.db.scalars(stmt).all())

    def list_open(self) -> list[Campaign]:
        """Campanhas com status OPEN (legado: OPEN_INTEREST)."""
        stmt = (
            select(Campaign)
            .where(Campaign.status == DejemMonthStatus.OPEN_INTEREST)
            .order_by(Campaign.year.desc(), Campaign.month.desc())
        )
        return list(self.db.scalars(stmt).all())

    def add(self, row: Campaign) -> Campaign:
        self.db.add(row)
        self.db.flush()
        return row

    def save(self, row: Campaign) -> Campaign:
        self.db.add(row)
        self.db.flush()
        return row

    def add_status_audit(self, row: CampaignStatusAudit) -> CampaignStatusAudit:
        self.db.add(row)
        self.db.flush()
        return row

    def list_status_audits(self, campaign_id: int) -> list[CampaignStatusAudit]:
        stmt = (
            select(CampaignStatusAudit)
            .where(CampaignStatusAudit.campaign_id == campaign_id)
            .order_by(CampaignStatusAudit.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())
