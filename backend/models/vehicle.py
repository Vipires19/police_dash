import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class VehicleModalidade(str, enum.Enum):
    FT = "FT"
    ROCAM = "ROCAM"


class VehicleStatus(str, enum.Enum):
    OPERANDO = "OPERANDO"
    BAIXADA = "BAIXADA"
    MANUTENCAO = "MANUTENCAO"
    RESERVA = "RESERVA"


class VehicleActionType(str, enum.Enum):
    CREATED = "CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    RETURNED = "RETURNED"
    UPDATED = "UPDATED"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    placa: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    prefixo: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    modelo: Mapped[str] = mapped_column(String(128), nullable=False)
    modalidade: Mapped[VehicleModalidade] = mapped_column(
        Enum(VehicleModalidade, name="vehiclemodalidade", create_type=False),
        nullable=False,
    )
    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, name="vehiclestatus", create_type=False),
        nullable=False,
        default=VehicleStatus.OPERANDO,
    )
    baixada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retorno_operacao_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    logs: Mapped[list["VehicleLog"]] = relationship(
        "VehicleLog",
        back_populates="vehicle",
    )


class VehicleLog(Base):
    __tablename__ = "vehicle_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    action_type: Mapped[VehicleActionType] = mapped_column(
        Enum(VehicleActionType, name="vehicleactiontype", create_type=False),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text(), nullable=True)
    old_status: Mapped[VehicleStatus | None] = mapped_column(
        Enum(VehicleStatus, name="vehiclestatus", create_type=False),
        nullable=True,
    )
    new_status: Mapped[VehicleStatus | None] = mapped_column(
        Enum(VehicleStatus, name="vehiclestatus", create_type=False),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="logs")
