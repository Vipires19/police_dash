import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    N90 = "N90"
    TAT_CMD = "TAT_CMD"
    BRACAL = "BRACAL"
    ESTAGIO = "ESTAGIO"


class UserStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    patente: Mapped[str] = mapped_column(String(64), nullable=False)
    nome_guerra: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    re: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(Text(), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    blood_type: Mapped[str | None] = mapped_column(String(8), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole", create_type=False),
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="userstatus", create_type=False),
        nullable=False,
        default=UserStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
