"""
Fixtures for fruit_origin module integration tests.

These fixtures provide:
- Database engine and session management (reuses fermentation module pattern)
- Automatic table cleanup and rollback
- Test data fixtures (winery, vineyard, vineyard_block)
- Repository instances configured with real DB sessions

Database: SQLite in-memory (shared cache for session-scoped fixtures)
Fast and isolated - no external dependencies required.
"""

import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Database configuration - SQLite in-memory with shared cache
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:?cache=shared"

# Global dict to store model classes (populated by db_engine fixture)
TEST_MODELS = {}


@pytest.fixture(scope="session")
def test_models():
    """
    Fixture to provide access to TEST_MODELS dict.
    This ensures tests wait for db_engine to populate TEST_MODELS before using it.
    """
    return TEST_MODELS


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.
    Scope: session - reused across all tests.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def integration_test_session():
    """
    Marker for integration test session.
    
    This simply indicates that integration tests are running.
    We do NOT clear the registry/metadata as that breaks SQLAlchemy's internal state.
    
    autouse=True means this runs automatically before ANY integration test.
    """
    print("\n[FRUIT_ORIGIN INTEGRATION TESTS] Starting integration test session...")
    yield
    print("\n[FRUIT_ORIGIN INTEGRATION TESTS] Finished integration test session.")


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """
    SQLite in-memory engine for integration tests.
    
    Create and configure async database engine for test suite.
    Creates all tables before tests and drops them after.
    
    Scope: session - single engine for all tests (performance).
    Uses SQLite with shared cache to maintain state across fixtures.
    
    IMPORTANT: This fixture imports models ONLY inside the fixture function
    to avoid registry conflicts with unit tests that may have already imported them.
    """
    from src.shared.infra.orm.base_entity import Base
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Set to True for SQL query debugging
        connect_args={"check_same_thread": False},  # Required for SQLite
    )
    
    # Import ALL models here INSIDE the fixture to avoid early registration
    from src.modules.winery.src.domain.entities.winery import Winery
    from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
    from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
    from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
    
    # Store models in global dict for use by fixtures AND tests
    TEST_MODELS.update({
        'Winery': Winery,
        'Vineyard': Vineyard,
        'VineyardBlock': VineyardBlock,
        'HarvestLot': HarvestLot,
    })
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup: Drop all tables at end of session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """
    Async session for each test with automatic rollback.
    
    Each test runs in a transaction that is rolled back after the test,
    ensuring test isolation and clean state.
    
    Scope: function - new session per test.
    """
    async_session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def clean_tables(db_session):
    """
    Clean all tables before test execution.
    
    Deletes all rows from tables in correct order to respect foreign key constraints.
    """
    await db_session.execute(text("DELETE FROM harvest_lots"))
    await db_session.execute(text("DELETE FROM vineyard_blocks"))
    await db_session.execute(text("DELETE FROM vineyards"))
    await db_session.execute(text("DELETE FROM wineries"))
    await db_session.commit()


@pytest_asyncio.fixture
async def test_winery(db_session):
    """Create a test winery for integration tests."""
    Winery = TEST_MODELS['Winery']
    winery = Winery(
        name="Test Winery",
        region="Napa Valley"
    )
    db_session.add(winery)
    await db_session.flush()
    return winery


@pytest_asyncio.fixture
async def session_manager(db_session):
    """
    Create a session manager for repository tests.
    
    Returns a mock session manager that returns the test db_session.
    """
    from unittest.mock import Mock, MagicMock, AsyncMock
    
    manager = Mock()
    
    # Create async context manager that returns db_session
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=db_session)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    
    manager.get_session = Mock(return_value=mock_context)
    manager.close = AsyncMock()
    
    return manager


@pytest_asyncio.fixture
async def vineyard_repository(session_manager):
    """Create VineyardRepository instance with test session manager."""
    from src.modules.fruit_origin.src.repository_component.repositories.vineyard_repository import VineyardRepository
    return VineyardRepository(session_manager)


@pytest_asyncio.fixture
async def vineyard_block_repository(session_manager):
    """Create VineyardBlockRepository instance with test session manager."""
    from src.modules.fruit_origin.src.repository_component.repositories.vineyard_block_repository import VineyardBlockRepository
    return VineyardBlockRepository(session_manager)


@pytest_asyncio.fixture
async def harvest_lot_repository(session_manager):
    """Create HarvestLotRepository instance with test session manager."""
    from src.modules.fruit_origin.src.repository_component.repositories.harvest_lot_repository import HarvestLotRepository
    return HarvestLotRepository(session_manager)


@pytest_asyncio.fixture
async def test_vineyard(db_session, test_winery):
    """Create a test vineyard for integration tests."""
    Vineyard = TEST_MODELS['Vineyard']
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
async def test_vineyard_block(db_session, test_vineyard):
    """Create a test vineyard block for integration tests."""
    VineyardBlock = TEST_MODELS['VineyardBlock']
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
async def test_harvest_lot(db_session, test_winery, test_vineyard_block):
    """Create a test harvest lot for integration tests."""
    from datetime import date, datetime
    HarvestLot = TEST_MODELS['HarvestLot']
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
        bins_count=15,
        field_temp_c=22.5,
        notes="Test harvest lot",
        is_deleted=False
    )
    db_session.add(harvest_lot)
    await db_session.flush()
    return harvest_lot
