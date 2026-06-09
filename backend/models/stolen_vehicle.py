from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class StolenVehicleType(str, enum.Enum):
    CARRO = "CARRO"
    MOTO = "MOTO"


class StolenOccurrenceType(str, enum.Enum):
    FURTO = "FURTO"
    ROUBO = "ROUBO"


class StolenVehicle(Base):
    __tablename__ = "stolen_vehicles"
    __table_args__ = (
        CheckConstraint(
            "plate_group >= 0 AND plate_group <= 9",
            name="ck_stolen_vehicles_plate_group_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vehicle_type: Mapped[StolenVehicleType] = mapped_column(
        Enum(StolenVehicleType, name="stolenvehicletype", create_type=False),
        nullable=False,
        index=True,
    )
    plate: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    vehicle_model: Mapped[str] = mapped_column(String(128), nullable=False)
    color: Mapped[str] = mapped_column(String(64), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    occurrence_type: Mapped[StolenOccurrenceType] = mapped_column(
        Enum(StolenOccurrenceType, name="stolenoccurrencetype", create_type=False),
        nullable=False,
    )
    plate_group: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    observation: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_recovered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    recovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recovered_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    recovered_notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
