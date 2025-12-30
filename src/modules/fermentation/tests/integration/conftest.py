"""
Fixtures for fermentation module integration tests.

Uses shared testing infrastructure from src/shared/testing/integration.
"""

import pytest_asyncio
from datetime import datetime
from src.shared.testing.integration import create_integration_fixtures, IntegrationTestConfig
from src.shared.testing.integration.fixtures import create_repository_fixture
from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.shared.auth.domain.entities.user import User
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource
# NOTE: SampleRepository import commented out due to single-table inheritance metadata conflicts (ADR-011/ADR-013)
# Sample tests use their own conftest in repository_component/ to avoid global metadata registration
# from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
from src.modules.fermentation.src.repository_component.repositories.fermentation_note_repository import FermentationNoteRepository
from src.modules.fruit_origin.src.repository_component.repositories.harvest_lot_repository import HarvestLotRepository

# Configure integration test fixtures for fermentation module
# NOTE: Sample models (SugarSample, DensitySample, CelsiusTemperatureSample) are NOT included
# due to single-table inheritance causing metadata conflicts. Sample tests import them directly.
config = IntegrationTestConfig(
    module_name="fermentation",
    models=[Winery, Vineyard, VineyardBlock, HarvestLot, User, Fermentation, FermentationNote, FermentationLotSource]
)

# Create standard fixtures (test_models, db_engine, db_session)
fixtures = create_integration_fixtures(config)
globals().update(fixtures)

# Create repository fixtures
# NOTE: sample_repository fixture commented out - Sample tests use their own fixtures (ADR-011/ADR-013)
# sample_repository = create_repository_fixture(SampleRepository)
fermentation_repository = create_repository_fixture(FermentationRepository)
harvest_lot_repository = create_repository_fixture(HarvestLotRepository)

# Alias for fermentation_note tests that use 'repository' fixture name
repository = create_repository_fixture(FermentationNoteRepository)


@pytest_asyncio.fixture
async def test_winery(test_models, db_session):
    """Create a test winery for integration tests."""
    from uuid import uuid4
    Winery = test_models['Winery']
    winery = Winery(
        code=f"TEST-{uuid4().hex[:8].upper()}",
        name="Test Winery",
        location="Napa Valley"
    )
    db_session.add(winery)
    await db_session.flush()
    return winery


@pytest_asyncio.fixture
async def test_vineyard(test_models, db_session, test_winery):
    """Create a test vineyard for integration tests."""
    Vineyard = test_models['Vineyard']
    vineyard = Vineyard(
        id=1,
        winery_id=test_winery.id,
        code="VYD001",
        name="Test Vineyard",
        notes="Test vineyard for integration tests"
    )
    db_session.add(vineyard)
    await db_session.flush()
    return vineyard


@pytest_asyncio.fixture
async def test_vineyard_block(test_models, db_session, test_vineyard):
    """Create a test vineyard block for integration tests."""
    VineyardBlock = test_models['VineyardBlock']
    block = VineyardBlock(
        id=1,
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
async def test_user(test_models, db_session, test_winery):
    """Create a test user for integration tests."""
    User = test_models['User']
    user = User(
        username="testuser",
        email="test@winery.com",
        full_name="Test User",
        password_hash="hashed_password_here",
        winery_id=test_winery.id,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def test_fermentation(test_models, db_session, test_user):
    """Create a test fermentation for integration tests."""
    Fermentation = test_models['Fermentation']
    from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
    
    fermentation = Fermentation(
        winery_id=test_user.winery_id,
        fermented_by_user_id=test_user.id,
        vintage_year=2024,
        yeast_strain="Test Yeast Strain",
        vessel_code="V001",
        input_mass_kg=100.0,
        initial_sugar_brix=22.5,
        initial_density=1.095,
        start_date=datetime.now(),
        status=FermentationStatus.ACTIVE.value,
    )
    db_session.add(fermentation)
    await db_session.flush()
    return fermentation


@pytest_asyncio.fixture
async def test_harvest_lot(test_models, db_session, test_winery, test_vineyard_block):
    """Create a test harvest lot for integration tests."""
    from datetime import date
    HarvestLot = test_models['HarvestLot']
    
    harvest_lot = HarvestLot(
        id=1,
        winery_id=test_winery.id,
        block_id=test_vineyard_block.id,
        code="HL2024001",
        harvest_date=date(2024, 9, 15),
        weight_kg=1500.0,
        brix_at_harvest=24.5,
        grape_variety="Cabernet Sauvignon",
        is_deleted=False
    )
    db_session.add(harvest_lot)
    await db_session.flush()
    return harvest_lot


@pytest_asyncio.fixture
async def uow(session_manager_factory):
    """Create a UnitOfWork instance for integration tests."""
    from src.modules.fermentation.src.repository_component.unit_of_work import UnitOfWork
    
    # Create a simple wrapper that implements ISessionManager interface
    # The session_manager_factory fixture returns a callable that returns an AsyncContextManager
    # but UnitOfWork expects an object with get_session() method
    class SessionManagerWrapper:
        def __init__(self, session_func):
            self._session_func = session_func
        
        async def get_session(self):
            """Return the async context manager for the session."""
            return self._session_func()
        
        async def close(self):
            """No-op for test fixture."""
            pass
    
    wrapped_manager = SessionManagerWrapper(session_manager_factory)
    return UnitOfWork(session_manager=wrapped_manager)
