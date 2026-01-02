"""
API test fixtures for Fruit Origin module.

Extends shared test fixtures with fruit_origin-specific setup.
"""
import pytest
import pytest_asyncio
import sys
import os
from pathlib import Path
from typing import AsyncGenerator

# Add project root to Python path to use src.shared imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums.user_role import UserRole
from src.shared.auth.infra.api.dependencies import get_current_user
from src.shared.infra.database.fastapi_session import get_db_session, initialize_database
from src.shared.infra.orm.base_entity import Base
from src.modules.fruit_origin.src.api_component.routers.vineyard_router import router as vineyard_router
from src.modules.fruit_origin.src.api_component.routers.harvest_lot_router import router as harvest_lot_router
from src.modules.fruit_origin.src.api_component.error_handlers import register_error_handlers

# Import entities for Base.metadata
from src.shared.auth.domain.entities.user import User
from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Session-level fixture: Initialize database for testing."""
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    initialize_database()
    yield
    os.environ.pop("DATABASE_URL", None)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Session-scoped: Create database engine ONCE for all tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///file:test_db?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False, "uri": True},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def override_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Function-scoped: Provide clean session for each test."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
    
    # Clean all data after each test
    async with test_engine.begin() as conn:
        try:
            await conn.execute(text("DELETE FROM harvest_lots"))
            await conn.execute(text("DELETE FROM vineyard_blocks"))
            await conn.execute(text("DELETE FROM vineyards"))
            await conn.execute(text("DELETE FROM users"))
            await conn.execute(text("DELETE FROM wineries"))
            await conn.commit()
        except Exception:
            await conn.rollback()


@pytest.fixture
def mock_user_context():
    """
    Fixture: Mock UserContext for testing without real auth.
    
    Returns a winemaker user by default (can create fermentations).
    """
    return UserContext(
        user_id=1,
        winery_id=1,
        email="test@winery.com",
        role=UserRole.WINEMAKER
    )


def create_fruit_origin_test_app(
    user_override: UserContext = None,
    db_override: AsyncSession = None
) -> FastAPI:
    """
    Create FastAPI test app for Fruit Origin module.
    
    Args:
        user_override: Optional UserContext to override auth dependency
        db_override: Optional AsyncSession to override database dependency
        
    Returns:
        Configured FastAPI app for testing
    """
    app = FastAPI(title="Fruit Origin API - Test")
    
    # Include routers
    app.include_router(vineyard_router)
    app.include_router(harvest_lot_router)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Override auth if user provided
    if user_override:
        app.dependency_overrides[get_current_user] = lambda: user_override
    
    # Override database session if provided
    if db_override:
        async def override_get_db():
            yield db_override
        app.dependency_overrides[get_db_session] = override_get_db
    
    return app


@pytest_asyncio.fixture
async def fruit_origin_client(mock_user_context, override_db_session):
    """
    Fixture: FastAPI TestClient for Fruit Origin API with authenticated user.
    
    Uses mock WINEMAKER user and test database.
    """
    app = create_fruit_origin_test_app(
        user_override=mock_user_context,
        db_override=override_db_session
    )
    return TestClient(app)


@pytest_asyncio.fixture
async def unauthenticated_fruit_origin_client(override_db_session):
    """
    Fixture: FastAPI TestClient WITHOUT authentication override.
    
    Used for testing authentication requirements (401 errors).
    """
    app = create_fruit_origin_test_app(
        user_override=None,
        db_override=override_db_session
    )
    return TestClient(app)
