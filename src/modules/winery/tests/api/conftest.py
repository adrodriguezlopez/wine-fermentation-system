"""
Test fixtures for Winery API tests.

Provides:
1. TestClient for FastAPI app with Winery routes
2. Mock authentication (ADMIN and WINEMAKER)
3. Test database setup
4. Helper utilities
"""
import pytest
import pytest_asyncio
import os
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text
from fastapi import FastAPI, Depends, HTTPException, status as http_status
from fastapi.testclient import TestClient

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums.user_role import UserRole
from src.shared.infra.orm.base_entity import Base
from src.shared.infra.database.fastapi_session import get_db_session as real_get_db_session

# Import all entities to register them in Base.metadata
from src.shared.auth.domain.entities.user import User
from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource


# =============================================================================
# SESSION-LEVEL DATABASE SETUP
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initialize database for testing (session scope)."""
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    yield
    os.environ.pop("DATABASE_URL", None)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for entire test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Session-scoped database engine with all tables created once."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///file:winery_test_db?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False, "uri": True},
        poolclass=StaticPool,
    )
    
    # Create all tables once
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Function-scoped session with data cleanup between tests."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
    
    # Clean data between tests
    async with test_engine.begin() as conn:
        try:
            await conn.execute(text("DELETE FROM fermentation_lot_sources"))
            await conn.execute(text("DELETE FROM fermentation_notes"))
            await conn.execute(text("DELETE FROM fermentations"))
            await conn.execute(text("DELETE FROM harvest_lots"))
            await conn.execute(text("DELETE FROM vineyard_blocks"))
            await conn.execute(text("DELETE FROM vineyards"))
            await conn.execute(text("DELETE FROM users"))
            await conn.execute(text("DELETE FROM wineries"))
            await conn.commit()
        except Exception:
            await conn.rollback()


# =============================================================================
# MOCK USER CONTEXTS
# =============================================================================

@pytest.fixture
def mock_admin_user():
    """Mock ADMIN user context (winery_id=1)."""
    return UserContext(
        user_id=1,
        winery_id=1,
        email="admin@winery.com",
        role=UserRole.ADMIN
    )


@pytest.fixture
def mock_winemaker_user():
    """Mock WINEMAKER user context (winery_id=1)."""
    return UserContext(
        user_id=2,
        winery_id=1,
        email="winemaker@winery.com",
        role=UserRole.WINEMAKER
    )


# =============================================================================
# FASTAPI TEST APP FACTORY
# =============================================================================

def create_winery_test_app(user_override: UserContext = None, db_override: AsyncSession = None):
    """
    Create FastAPI app with winery routes for testing.
    
    Args:
        user_override: Optional UserContext to override auth
        db_override: Optional AsyncSession to override database
    
    Returns:
        FastAPI app configured for testing
    """
    from src.shared.auth.infra.api.dependencies import get_current_user, require_admin
    from src.modules.winery.src.api_component.routers.winery_router import router as winery_router
    
    app = FastAPI(title="Winery API - Test")
    app.include_router(winery_router, prefix="/api/v1")
    
    # Override auth if provided
    if user_override:
        app.dependency_overrides[get_current_user] = lambda: user_override
        # For require_admin, only allow ADMIN role
        def mock_require_admin():
            if user_override.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
            return user_override
        app.dependency_overrides[require_admin] = mock_require_admin
    
    # Override database if provided
    if db_override:
        async def override_get_db():
            yield db_override
        app.dependency_overrides[real_get_db_session] = override_get_db
    
    return app


# =============================================================================
# CLIENT FIXTURES
# =============================================================================

@pytest.fixture
def client(mock_admin_user, db_session):
    """TestClient with ADMIN user and test database."""
    app = create_winery_test_app(user_override=mock_admin_user, db_override=db_session)
    return TestClient(app)


@pytest.fixture
def admin_client(mock_admin_user, db_session):
    """TestClient with ADMIN user (explicit fixture name)."""
    app = create_winery_test_app(user_override=mock_admin_user, db_override=db_session)
    return TestClient(app)


@pytest.fixture
def winemaker_client(mock_winemaker_user, db_session):
    """TestClient with WINEMAKER user."""
    app = create_winery_test_app(user_override=mock_winemaker_user, db_override=db_session)
    return TestClient(app)


@pytest.fixture
def unauthenticated_client(db_session):
    """TestClient WITHOUT authentication (triggers 401 errors)."""
    app = create_winery_test_app(user_override=None, db_override=db_session)
    return TestClient(app)
