from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class VehicleQruCode(Base):
    __tablename__ = "vehicle_qru_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)


class CriminalWatchVehicle(Base):
    __tablename__ = "criminal_watch_vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plate: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    vehicle_model: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    color: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    qru_code_id: Mapped[int] = mapped_column(ForeignKey("vehicle_qru_codes.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    qru_code: Mapped[VehicleQruCode] = relationship("VehicleQruCode")
    notes: Mapped[list[CriminalWatchNote]] = relationship(
        "CriminalWatchNote",
        back_populates="vehicle",
        cascade="all, delete-orphan",
        order_by="CriminalWatchNote.created_at",
    )


class CriminalWatchNote(Base):
    __tablename__ = "criminal_watch_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("criminal_watch_vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    note: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    vehicle: Mapped[CriminalWatchVehicle] = relationship("CriminalWatchVehicle", back_populates="notes")
