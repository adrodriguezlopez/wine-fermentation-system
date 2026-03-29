"""
Integration test for seed_initial_data.py script.

Tests the complete seed operation with a real (in-memory) async database.
Verifies idempotency and data integrity using aiosqlite + async SQLAlchemy.

ADR-018: Seed Script for Initial Data Bootstrap
"""
import asyncio
import sys
import tempfile
import os
from pathlib import Path
from typing import AsyncGenerator
import pytest
import pytest_asyncio
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
from src.modules.winery.src.domain.entities.winery import Winery
from src.shared.auth.domain.entities.user import User
from src.shared.auth.domain.enums.user_role import UserRole
from src.shared.infra.orm.base_entity import Base


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def test_config_file():
    """Create a temporary test configuration file."""
    test_config = {
        "winery": {
            "code": "TEST-INTEGRATION",
            "name": "Integration Test Winery",
            "location": "Test Location",
            "notes": "Created by integration test"
        },
        "admin_user": {
            "username": "testadmin",
            "email": "testadmin@integration.test",
            "password": "testpass123",
            "full_name": "Integration Test Admin"
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_config, f)
        config_path = f.name

    yield config_path

    os.unlink(config_path)


@pytest_asyncio.fixture
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an in-memory async SQLite engine for integration tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an AsyncSession backed by the in-memory engine."""
    factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session


# =============================================================================
# Helpers
# =============================================================================

def _make_session_cm(session: AsyncSession):
    """Build a minimal async context manager that yields the given session."""
    class _CM:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *args):
            return False

    return _CM()


# =============================================================================
# Tests
# =============================================================================

@pytest.mark.asyncio
async def test_seed_all_integration_creates_entities(test_config_file, async_engine, async_session):
    """Integration test: Verify seed creates winery and admin user."""
    import scripts.seed_initial_data as seed_module
    from unittest.mock import MagicMock, AsyncMock

    mock_db_session = MagicMock()
    mock_db_session.get_session.return_value = _make_session_cm(async_session)
    mock_db_session.close = AsyncMock()

    with __import__('unittest.mock', fromlist=['patch']).patch(
        'scripts.seed_initial_data.DatabaseConfig'
    ), __import__('unittest.mock', fromlist=['patch']).patch(
        'scripts.seed_initial_data.DatabaseSession', return_value=mock_db_session
    ):
        result = await seed_module.seed_all(test_config_file)

    assert result is not None
    assert "winery" in result
    assert "admin_user" in result

    winery = result["winery"]
    assert winery.id is not None
    assert winery.code == "TEST-INTEGRATION"
    assert winery.name == "Integration Test Winery"
    assert winery.location == "Test Location"

    admin_user = result["admin_user"]
    assert admin_user.id is not None
    assert admin_user.username == "testadmin"
    assert admin_user.email == "testadmin@integration.test"
    assert admin_user.winery_id == winery.id
    assert admin_user.role == UserRole.ADMIN.value
    assert admin_user.is_active is True
    assert admin_user.password_hash is not None
    assert admin_user.password_hash != "testpass123"

    # Verify data persisted in DB
    db_winery = (await async_session.execute(
        select(Winery).filter_by(code="TEST-INTEGRATION")
    )).scalars().first()
    assert db_winery is not None
    assert db_winery.name == "Integration Test Winery"

    db_user = (await async_session.execute(
        select(User).filter_by(email="testadmin@integration.test")
    )).scalars().first()
    assert db_user is not None
    assert db_user.username == "testadmin"
    assert db_user.winery_id == db_winery.id


@pytest.mark.asyncio
async def test_seed_all_integration_idempotent(test_config_file, async_engine):
    """Integration test: Verify seed is idempotent (can run multiple times safely)."""
    import scripts.seed_initial_data as seed_module
    from unittest.mock import MagicMock, AsyncMock

    factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async def run_seed():
        async with factory() as session:
            mock_db_session = MagicMock()
            mock_db_session.get_session.return_value = _make_session_cm(session)
            mock_db_session.close = AsyncMock()
            with __import__('unittest.mock', fromlist=['patch']).patch(
                'scripts.seed_initial_data.DatabaseConfig'
            ), __import__('unittest.mock', fromlist=['patch']).patch(
                'scripts.seed_initial_data.DatabaseSession', return_value=mock_db_session
            ):
                return await seed_module.seed_all(test_config_file)

    result1 = await run_seed()
    result2 = await run_seed()

    assert result1 is not None
    assert result2 is not None
    assert result1["winery"].id == result2["winery"].id
    assert result1["admin_user"].id == result2["admin_user"].id

    # Verify only one of each in DB
    async with factory() as session:
        winery_count = len((await session.execute(select(Winery))).scalars().all())
        user_count = len((await session.execute(select(User))).scalars().all())

    assert winery_count == 1, f"Expected 1 winery, found {winery_count}"
    assert user_count == 1, f"Expected 1 user, found {user_count}"


@pytest.mark.asyncio
async def test_seed_all_integration_password_hashing(test_config_file, async_engine, async_session):
    """Integration test: Verify password is properly hashed."""
    import scripts.seed_initial_data as seed_module
    from unittest.mock import MagicMock, AsyncMock

    mock_db_session = MagicMock()
    mock_db_session.get_session.return_value = _make_session_cm(async_session)
    mock_db_session.close = AsyncMock()

    with __import__('unittest.mock', fromlist=['patch']).patch(
        'scripts.seed_initial_data.DatabaseConfig'
    ), __import__('unittest.mock', fromlist=['patch']).patch(
        'scripts.seed_initial_data.DatabaseSession', return_value=mock_db_session
    ):
        result = await seed_module.seed_all(test_config_file)

    admin_user = result["admin_user"]

    assert admin_user.password_hash.startswith('$2b$'), \
        "Password should be hashed with bcrypt"

    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    assert pwd_context.verify("testpass123", admin_user.password_hash), \
        "Password hash should verify against original password"
    assert not pwd_context.verify("wrongpassword", admin_user.password_hash), \
        "Wrong password should not verify"
