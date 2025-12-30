"""
Fixtures for winery module integration tests.

Uses shared testing infrastructure from src/shared/testing/integration.
"""

import pytest_asyncio
from unittest.mock import AsyncMock, create_autospec
from src.shared.testing.integration import create_integration_fixtures, IntegrationTestConfig
from src.shared.testing.integration.fixtures import create_repository_fixture
from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.winery.src.repository_component.repositories.winery_repository import WineryRepository
from src.modules.winery.src.service_component.services.winery_service import WineryService

# Configure integration test fixtures for winery module
config = IntegrationTestConfig(
    module_name="winery",
    models=[Winery]
)

# Create standard fixtures (test_models, db_engine, db_session)
fixtures = create_integration_fixtures(config)
globals().update(fixtures)

# Create repository fixture
winery_repository = create_repository_fixture(WineryRepository)


@pytest_asyncio.fixture
async def test_winery(test_models, db_session):
    """Create a test winery for use in tests."""
    from uuid import uuid4
    Winery = test_models['Winery']
    unique_id = uuid4().hex[:8]
    winery = Winery(
        code=f"TEST-{unique_id.upper()}",
        name=f"Test Winery {unique_id}",
        location="Test Location",
        is_deleted=False,
    )
    db_session.add(winery)
    await db_session.flush()
    await db_session.refresh(winery)
    return winery


@pytest_asyncio.fixture
async def test_winery_2(test_models, db_session):
    """Create a second test winery for multi-winery tests."""
    from uuid import uuid4
    Winery = test_models['Winery']
    unique_id = uuid4().hex[:8]
    winery = Winery(
        code=f"SEC-{unique_id.upper()}",
        name=f"Second Winery {unique_id}",
        location="Another Location",
        is_deleted=False,
    )
    db_session.add(winery)
    await db_session.flush()
    await db_session.refresh(winery)
    return winery


@pytest_asyncio.fixture
async def winery_service(winery_repository):
    """Create WineryService with real repository and mocked cross-module repos."""
    # Mock cross-module repositories for deletion protection
    mock_vineyard_repo = AsyncMock()
    mock_vineyard_repo.get_by_winery = AsyncMock(return_value=[])
    
    mock_fermentation_repo = AsyncMock()
    mock_fermentation_repo.get_by_winery = AsyncMock(return_value=[])
    
    return WineryService(
        winery_repo=winery_repository,
        vineyard_repo=mock_vineyard_repo,
        fermentation_repo=mock_fermentation_repo
    )
