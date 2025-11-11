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

def create_test_app(user_override: UserContext = None):
    """
    Helper function to create FastAPI test app with optional user override
    
    Args:
        user_override: Optional UserContext to override auth dependency
    
    Returns:
        FastAPI app configured for testing
    """
    from fastapi import FastAPI, Depends
    from src.shared.auth.domain.dtos import UserContext as UC
    from src.shared.auth.infra.api.dependencies import get_current_user, require_winemaker
    from src.modules.fermentation.src.api.routers.fermentation_router import router as fermentation_router
    
    # Create minimal FastAPI app for testing
    app = FastAPI(title="Fermentation API - Test")
    
    # Include fermentation router
    app.include_router(fermentation_router)
    
    # Test endpoint to verify client works
    @app.get("/test")
    def test_endpoint(user: UC = Depends(get_current_user)):
        return {"status": "ok", "user_id": user.user_id}
    
    # Override auth if user provided
    if user_override:
        app.dependency_overrides[get_current_user] = lambda: user_override
        app.dependency_overrides[require_winemaker] = lambda: user_override
    
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
    # Create async engine with SQLite in-memory
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
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


@pytest.fixture
def client(mock_user_context):
    """
    Fixture: FastAPI TestClient with default mock user (WINEMAKER)
    
    Uses create_test_app helper with mock_user_context override
    """
    app = create_test_app(user_override=mock_user_context)
    return TestClient(app)


@pytest.fixture
def unauthenticated_client():
    """
    Fixture: FastAPI TestClient WITHOUT authentication override
    
    This client will trigger real auth dependencies, causing 401 errors
    when endpoints require authentication.
    
    Used for testing authentication requirements.
    """
    app = create_test_app(user_override=None)  # No auth override
    return TestClient(app)
