"""Alembic Environment Script

Provides the :class:`.EnvironmentContext` object which serves as a
source of event hooks and one or more :class:`.MigrationContext`
objects. Scripts which run in the alembic runner are passed a
template for this module.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Base and ALL entity classes so that Base.metadata contains
# the complete schema — required for autogenerate to produce accurate diffs.
from src.shared.infra.orm.base_entity import Base  # noqa: F401 (registers mapper)

# Multi-tenancy root
from src.modules.winery.src.domain.entities.winery import Winery  # noqa: F401
from src.shared.auth.domain.entities.user import User  # noqa: F401

# Fruit origin / traceability
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard  # noqa: F401
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock  # noqa: F401
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot  # noqa: F401

# Fermentation core
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation  # noqa: F401
from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote  # noqa: F401
from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource  # noqa: F401
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample  # noqa: F401

# Fermentation protocol (ADR-035)
from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol  # noqa: F401
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep  # noqa: F401
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution  # noqa: F401
from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion  # noqa: F401
from src.modules.fermentation.src.domain.entities.protocol_alert import ProtocolAlert  # noqa: F401
from src.modules.fermentation.src.domain.entities.winemaker_action import WinemakerAction  # noqa: F401

# Analysis engine
from src.modules.analysis_engine.src.domain.entities.recommendation_template import RecommendationTemplate  # noqa: F401
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis  # noqa: F401
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly  # noqa: F401
from src.modules.analysis_engine.src.domain.entities.recommendation import Recommendation  # noqa: F401
from src.modules.analysis_engine.src.domain.entities.protocol_advisory import ProtocolAdvisory  # noqa: F401

target_metadata = Base.metadata

# this is the Alembic Config object, which provides
# the values of the [alembic] section of the alembic.ini
# file as Python dictionary, with values mirroring those in the
# [alembic] section plus some coerced boolean inferred from the
# values. For Python 3.5+, the `with` statement is used to keep
# these values scoped to a section of code where they're being
# used. On Python 3.4 and earlier .INI files syntax requires you to
# manually close the config block.

config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# (target_metadata is defined above)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    sqlalchemy_url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=sqlalchemy_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    # Prefer DATABASE_URL env var; strip async driver prefix for sync engine
    env_url = os.environ.get("DATABASE_URL", "")
    if env_url:
        env_url = env_url.replace("postgresql+asyncpg://", "postgresql://")
    configuration["sqlalchemy.url"] = (
        env_url
        or configuration.get("sqlalchemy.url")
        or "postgresql://postgres:postgres@localhost:5433/wine_fermentation"
    )
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
