"""OfferEvent — alteração auditável na oferta de vagas da campanha."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from operations.dejem.models.enums import OfferEventType

if TYPE_CHECKING:
    from models.dejem import DejemMonth
    from models.user import User


class OfferEvent(Base):
    """Evento de alteração de quantidade de vagas (fonte da verdade da oferta)."""

    __tablename__ = "dejem_offer_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("dejem_months.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[OfferEventType] = mapped_column(
        Enum(OfferEventType, name="dejemoffereventtype", create_type=False),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    campaign: Mapped[DejemMonth] = relationship("DejemMonth", foreign_keys=[campaign_id])
    creator: Mapped[User] = relationship("User", foreign_keys=[created_by])
