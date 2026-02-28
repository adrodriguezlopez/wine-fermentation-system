"""Pytest configuration for analysis engine tests."""
import pytest
import sys
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Add paths for imports
# This test is at: tests/unit/modules/analysis_engine/conftest.py
# Go to project root, then into /src to get access to shared and modules
src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from shared.infra.orm.base_entity import Base


@pytest.fixture
async def engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def session(engine):
    """Create a session for testing."""
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
