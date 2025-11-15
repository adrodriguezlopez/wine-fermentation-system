"""
Test fixtures for API tests

Following TDD: This conftest will provide:
1. TestClient for FastAPI app
2. Mock authentication (bypass real auth for testing)
3. Test database setup
4. Mock services (FermentationService, SampleService)
"""

import pytest
import pytest_asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums.user_role import UserRole
from src.shared.infra.orm.base_entity import Base
from src.shared.infra.database.fastapi_session import initialize_database, get_db_session
from src.shared.infra.database.config import DatabaseConfig

# Import all entities to register them in Base.metadata
# This is necessary for create_all() to work properly with FK constraints
from src.shared.auth.domain.entities.user import User
from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
# Import sample entities
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample


# =============================================================================
# TEST 1: Verify TestClient fixture exists and returns a client
# =============================================================================
def test_client_fixture_exists(client):
    """Test: TestClient fixture should be available and configured"""
    assert client is not None
    assert hasattr(client, 'get')
    assert hasattr(client, 'post')


# =============================================================================
# TEST 2: Verify mock_user_context fixture provides UserContext
# =============================================================================
def test_mock_user_context_fixture(mock_user_context):
    """Test: mock_user_context should provide a valid UserContext"""
    assert isinstance(mock_user_context, UserContext)
    assert mock_user_context.user_id == 1
    assert mock_user_context.winery_id == 1
    assert mock_user_context.email == "test@winery.com"
    assert mock_user_context.role == UserRole.WINEMAKER


# =============================================================================
# TEST 3: Verify test database fixture
# =============================================================================
@pytest.mark.asyncio
async def test_test_db_fixture(test_db_session: AsyncSession):
    """Test: test_db_session should provide an AsyncSession"""
    from sqlalchemy import text
    
    assert isinstance(test_db_session, AsyncSession)
    assert test_db_session.bind is not None
    
    # Try a simple query to verify it works
    result = await test_db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


# =============================================================================
# FIXTURES (implemented to make tests pass - TDD GREEN phase)
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Session-level fixture: Initialize database for testing.
    
    Sets DATABASE_URL environment variable to use in-memory SQLite for all tests.
    Initializes fastapi_session module once per test session.
    """
    # Set DATABASE_URL for tests (SQLite in-memory)
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    
    # Initialize database configuration
    # This will be used by get_db_session in endpoints
    initialize_database()
    
    yield
    
    # Cleanup after all tests
    os.environ.pop("DATABASE_URL", None)


# =============================================================================
# DATABASE FIXTURES - Session-scoped (create DB once, reuse for all tests)
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Session-scoped: Create database engine ONCE for all tests.
    
    Uses SQLite in-memory with shared cache so all tests use the same DB.
    Tables are created once at session start.
    """
    # Use shared cache so all connections see the same DB
    engine = create_async_engine(
        "sqlite+aiosqlite:///file:test_db?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False, "uri": True},
        poolclass=StaticPool,
    )
    
    # Create ALL tables once at session start
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup at session end
    await engine.dispose()


@pytest_asyncio.fixture
async def override_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Function-scoped: Provide clean session for each test.
    
    Reuses the same database (test_engine) but cleans data between tests.
    Much more efficient than creating/destroying DB per test.
    """
    # Create session from shared engine
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()
    
    # Clean all data after each test (preserve schema)
    async with test_engine.begin() as conn:
        # Delete data from tables in reverse dependency order
        # Only delete from tables that actually exist in the DB
        try:
            await conn.execute(text("DELETE FROM fermentation_lot_sources"))
            await conn.execute(text("DELETE FROM fermentation_notes"))
            await conn.execute(text("DELETE FROM fermentations"))
            await conn.execute(text("DELETE FROM harvest_lots"))
            await conn.execute(text("DELETE FROM users"))
            await conn.execute(text("DELETE FROM wineries"))
            await conn.commit()
        except Exception:
            # If any table doesn't exist, just rollback and continue
            await conn.rollback()


def create_test_app(user_override: UserContext = None, db_override: AsyncSession = None):
    """
    Helper function to create FastAPI test app with optional overrides
    
    Args:
        user_override: Optional UserContext to override auth dependency
        db_override: Optional AsyncSession to override database dependency
    
    Returns:
        FastAPI app configured for testing
    """
    from fastapi import FastAPI, Depends
    from src.shared.auth.domain.dtos import UserContext as UC
    from src.shared.auth.infra.api.dependencies import get_current_user, require_winemaker
    from src.shared.infra.database.fastapi_session import get_db_session as real_get_db_session
    from src.modules.fermentation.src.api.routers.fermentation_router import router as fermentation_router
    from src.modules.fermentation.src.api.routers.sample_router import router as sample_router, samples_router
    
    # Create minimal FastAPI app for testing
    app = FastAPI(title="Fermentation API - Test")
    
    # Include routers (sample router first for route specificity)
    app.include_router(sample_router)
    app.include_router(samples_router)  # New: non-nested sample endpoints
    app.include_router(fermentation_router)
    
    # Test endpoint to verify client works
    @app.get("/test")
    def test_endpoint(user: UC = Depends(get_current_user)):
        return {"status": "ok", "user_id": user.user_id}
    
    # Override auth if user provided
    if user_override:
        app.dependency_overrides[get_current_user] = lambda: user_override
        app.dependency_overrides[require_winemaker] = lambda: user_override
    
    # Override database session if provided
    if db_override:
        async def override_get_db():
            yield db_override
        app.dependency_overrides[real_get_db_session] = override_get_db
    
    return app


@pytest.fixture
def mock_user_context():
    """
    Fixture: Mock UserContext for testing without real auth
    
    Returns a winemaker user by default (can create fermentations)
    
    GREEN: Implementation that makes test_mock_user_context_fixture pass
    """
    return UserContext(
        user_id=1,
        winery_id=1,
        email="test@winery.com",
        role=UserRole.WINEMAKER
    )


@pytest_asyncio.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture: Test database session (SQLite in-memory)
    
    GREEN: Implementation with SQLite in-memory database
    
    Note: We don't create all tables to avoid FK constraints issues.
    Individual tests should create only the tables they need.
    """
    # Use unique DB name for complete isolation
    import uuid
    db_name = f"test_{uuid.uuid4().hex}"
    
    # Create async engine with SQLite in-memory
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_name}?mode=memory&cache=shared",
        connect_args={"check_same_thread": False, "uri": True},
        poolclass=StaticPool,
    )
    
    # Don't create tables here - let each test decide what it needs
    # This avoids FK constraint issues with tables we don't need
    
    # Create session
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
    
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def client(mock_user_context, override_db_session):
    """
    Fixture: FastAPI TestClient with default mock user (WINEMAKER) and test DB.
    
    Uses create_test_app helper with both mock_user_context and DB overrides.
    """
    app = create_test_app(user_override=mock_user_context, db_override=override_db_session)
    return TestClient(app)


@pytest_asyncio.fixture
async def unauthenticated_client(override_db_session):
    """
    Fixture: FastAPI TestClient WITHOUT authentication override but WITH test DB.
    
    This client will trigger real auth dependencies, causing 401 errors
    when endpoints require authentication.
    
    Used for testing authentication requirements.
    """
    app = create_test_app(user_override=None, db_override=override_db_session)  # No auth override
    return TestClient(app)
