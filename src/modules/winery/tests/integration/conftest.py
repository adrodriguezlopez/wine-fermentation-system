"""
Fixtures for winery module integration tests.

Uses shared testing infrastructure from src/shared/testing/integration.
"""

import pytest_asyncio
from src.shared.testing.integration import create_integration_fixtures, IntegrationTestConfig
from src.shared.testing.integration.fixtures import create_repository_fixture
from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.winery.src.repository_component.repositories.winery_repository import WineryRepository

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
    winery = Winery(
        name=f"Test Winery {uuid4().hex[:8]}",
        region="Test Region",
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
    winery = Winery(
        name=f"Second Winery {uuid4().hex[:8]}",
        region="Another Region",
        is_deleted=False,
    )
    db_session.add(winery)
    await db_session.flush()
    await db_session.refresh(winery)
    return winery
