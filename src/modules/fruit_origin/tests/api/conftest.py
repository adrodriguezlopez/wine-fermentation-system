"""
API test fixtures for Fruit Origin module.

Extends shared test fixtures with fruit_origin-specific setup.
"""
import pytest
import pytest_asyncio
import sys
from pathlib import Path

# Add project root to Python path to use src.shared imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums.user_role import UserRole
from src.shared.auth.infra.api.dependencies import get_current_user
from src.shared.infra.database.fastapi_session import get_db_session
from src.modules.fruit_origin.src.api_component.routers.vineyard_router import router as vineyard_router
from src.modules.fruit_origin.src.api_component.routers.harvest_lot_router import router as harvest_lot_router
from src.modules.fruit_origin.src.api_component.error_handlers import register_error_handlers


# Import shared fixtures from global conftest
pytest_plugins = ["tests.api.conftest"]


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
