"""
Fixtures for fruit_origin module integration tests.

Uses shared testing infrastructure from src/shared/testing/integration.
"""

import pytest_asyncio
from shared.testing.integration import create_integration_fixtures, IntegrationTestConfig
from shared.testing.integration.fixtures import create_repository_fixture
from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.modules.fruit_origin.src.repository_component.repositories.vineyard_repository import VineyardRepository
from src.modules.fruit_origin.src.repository_component.repositories.vineyard_block_repository import VineyardBlockRepository
from src.modules.fruit_origin.src.repository_component.repositories.harvest_lot_repository import HarvestLotRepository

# Configure integration test fixtures for fruit_origin module
config = IntegrationTestConfig(
    module_name="fruit_origin",
    models=[Winery, Vineyard, VineyardBlock, HarvestLot]
)

# Create standard fixtures (test_models, db_engine, db_session)
fixtures = create_integration_fixtures(config)
globals().update(fixtures)

# Create repository fixtures
vineyard_repository = create_repository_fixture(VineyardRepository)
vineyard_block_repository = create_repository_fixture(VineyardBlockRepository)
harvest_lot_repository = create_repository_fixture(HarvestLotRepository)


@pytest_asyncio.fixture
async def test_winery(test_models, db_session):
    """Create a test winery for integration tests."""
    Winery = test_models['Winery']
    winery = Winery(
        name="Test Winery",
        region="Napa Valley"
    )
    db_session.add(winery)
    await db_session.flush()
    return winery

@pytest_asyncio.fixture
async def test_vineyard(test_models, db_session, test_winery):
    """Create a test vineyard for integration tests."""
    Vineyard = test_models['Vineyard']
    vineyard = Vineyard(
        winery_id=test_winery.id,
        code="VYD001",
        name="Test Vineyard",
        notes="Test vineyard for integration tests",
        is_deleted=False
    )
    db_session.add(vineyard)
    await db_session.flush()
    return vineyard


@pytest_asyncio.fixture
async def test_vineyard_block(test_models, db_session, test_vineyard):
    """Create a test vineyard block for integration tests."""
    VineyardBlock = test_models['VineyardBlock']
    block = VineyardBlock(
        vineyard_id=test_vineyard.id,
        code="BLK001",
        soil_type="Clay loam",
        area_ha=2.5,
        is_deleted=False
    )
    db_session.add(block)
    await db_session.flush()
    return block


@pytest_asyncio.fixture
async def test_harvest_lot(test_models, db_session, test_winery, test_vineyard_block):
    """Create a test harvest lot for integration tests."""
    from datetime import date, datetime
    HarvestLot = test_models['HarvestLot']
    harvest_lot = HarvestLot(
        winery_id=test_winery.id,
        block_id=test_vineyard_block.id,
        code="HL-TEST-001",
        harvest_date=date(2024, 3, 15),
        weight_kg=1500.0,
        brix_at_harvest=24.5,
        brix_method="refractometer",
        brix_measured_at=datetime(2024, 3, 15, 10, 30),
        grape_variety="Cabernet Sauvignon",
        clone="337",
        rootstock="101-14",
        pick_method="hand",
        pick_start_time="08:00:00",
        pick_end_time="12:30:00",
        bins_count=15,
        field_temp_c=22.5,
        notes="Test harvest lot",
        is_deleted=False
    )
    db_session.add(harvest_lot)
    await db_session.flush()
    return harvest_lot
