import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from core.config import settings
from database.base import Base
from models.user import User  # noqa: F401
from models.vehicle import Vehicle, VehicleLog  # noqa: F401
from models.compensations import (  # noqa: F401
    CompensationEvent,
    CompensationEventLog,
    CompensationEventParticipant,
    UserCompensation,
)
from models.leaves import LeaveApprovalLog, LeaveRequest  # noqa: F401
from models.vacation import VacationApprovalLog, VacationRequest  # noqa: F401
from models.service_scale import (  # noqa: F401
    ScaleLog,
    ScaleTeam,
    ScaleTeamMember,
    ServiceScale,
)
from models.stolen_vehicle import StolenVehicle  # noqa: F401
from models.criminal_watch import CriminalWatchNote, CriminalWatchVehicle, VehicleQruCode  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return settings.database_url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
