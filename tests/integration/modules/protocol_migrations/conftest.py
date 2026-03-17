"""
Integration test fixtures for protocol migration tables.

Tests that all 3 Alembic migrations created the correct tables and that
the repository layer can perform CRUD against the live PostgreSQL DB.

Covers:
- 001_create_protocol_tables (fermentation_protocols, protocol_steps,
  protocol_executions, step_completions)
- 002_create_protocol_alerts_table (protocol_alerts)
- 003_create_protocol_advisory_table (protocol_advisory)

Database: localhost:5433/wine_fermentation  (same DB that alembic upgrade head ran on)
Tables are created by alembic, NOT by Base.metadata.create_all() here.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent.parent.parent
for _p in [str(_project_root), str(_project_root / "src")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Step 1: Register stub tables for cross-module FK targets ──────────────────
# FermentationProtocol, ProtocolExecution, ProtocolAlert declare
# ForeignKey("wineries.id") and ForeignKey("fermentations.id") at ORM level.
# These FKs were removed from the DB (migration 001/002) but still exist in the
# mapper metadata. SQLAlchemy raises NoReferencedTableError during flush if those
# tables are absent from the metadata.  Registering minimal stubs here silences
# the error without requiring cross-module imports.
from sqlalchemy import Table, Column, Integer
from src.shared.infra.orm.base_entity import Base  # shared declarative Base

for _stub_name, _pk_type in [("wineries", Integer), ("fermentations", Integer)]:
    if _stub_name not in Base.metadata.tables:
        Table(_stub_name, Base.metadata, Column("id", _pk_type, primary_key=True))

# ── Step 2: Import all ORM entities so mapper cascade resolves correctly ──────
try:
    import src.shared.auth.domain.entities.user  # noqa: F401
    import src.modules.fermentation.src.domain.entities.fermentation  # noqa: F401
    import src.modules.fermentation.src.domain.entities.fermentation_note  # noqa: F401
    import src.modules.fermentation.src.domain.entities.fermentation_lot_source  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_protocol  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_step  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_execution  # noqa: F401
    import src.modules.fermentation.src.domain.entities.step_completion  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_alert  # noqa: F401
    import src.modules.analysis_engine.src.domain.entities.protocol_advisory  # noqa: F401
except Exception:
    pass

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ─── Connection to the migrated DB ──────────────────────────────────────────
# Tables already exist (created by `alembic upgrade head`).
# We do NOT call create_all() here — we rely on what Alembic created.
_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/wine_fermentation"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Provide an async session connected to the live migrated DB.
    Each test wraps its operations in a transaction that is rolled back,
    so tests are isolated and leave no data behind.
    """
    engine = create_async_engine(_DB_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()

    await engine.dispose()
