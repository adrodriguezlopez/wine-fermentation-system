"""
Fixtures for integration tests with in-memory SQLite database.

These fixtures provide:
- Database engine and session management
- Automatic table cleanup and rollback
- Test data fixtures (winery, user, fermentation)
- Repository instances configured with real DB sessions

Database: SQLite in-memory (shared cache for session-scoped fixtures)
Fast and isolated - no external dependencies required.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, String
from sqlalchemy.orm import Mapped, mapped_column

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
    print("\n[INTEGRATION TESTS] Starting integration test session...")
    yield
    print("\n[INTEGRATION TESTS] Finished integration test session.")


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
    # Import directly from modules (NOT from __init__.py) to avoid double registration
    from src.modules.winery.src.domain.entities.winery import Winery
    from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
    from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
    from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
    from src.shared.auth.domain.entities.user import User
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
    from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
    from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource
    from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
    from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
    from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
    from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample

    
    # Store models in global dict for use by fixtures AND tests
    # This ensures models are only imported ONCE, avoiding SQLAlchemy registry conflicts
    TEST_MODELS.update({
        'Winery': Winery,
        'Vineyard': Vineyard,
        'VineyardBlock': VineyardBlock,
        'HarvestLot': HarvestLot,
        'User': User,
        'Fermentation': Fermentation,
        'BaseSample': BaseSample,
        'SugarSample': SugarSample,
        'DensitySample': DensitySample,
        'CelsiusTemperatureSample': CelsiusTemperatureSample,
    })
    
    # SQLAlchemy will create all tables
    # Drop first to ensure clean state (important for SQLite which persists schema)
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
    # Create session factory
    async_session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_factory() as session:
        # Start transaction
        async with session.begin():
            yield session
            # Automatic rollback on exit
            await session.rollback()


@pytest_asyncio.fixture
async def clean_tables(db_session):
    """
    Clean all tables before test execution.
    
    Deletes all rows from tables in correct order to respect foreign key constraints.
    Use this when you need a completely clean database state.
    
    Note: Uses DELETE instead of TRUNCATE for SQLite compatibility.
    """
    # Delete in order (respecting FK constraints - children first, parents last)
    await db_session.execute(text("DELETE FROM samples"))
    await db_session.execute(text("DELETE FROM fermentation_notes"))
    await db_session.execute(text("DELETE FROM fermentation_lot_sources"))
    await db_session.execute(text("DELETE FROM fermentations"))
    await db_session.execute(text("DELETE FROM users"))
    await db_session.execute(text("DELETE FROM harvest_lots"))
    await db_session.execute(text("DELETE FROM vineyard_blocks"))
    await db_session.execute(text("DELETE FROM vineyards"))
    await db_session.execute(text("DELETE FROM wineries"))
    await db_session.commit()


@pytest_asyncio.fixture
async def test_winery(db_session):
    """
    Create a test winery for integration tests.
    
    Returns a Winery entity persisted in the database.
    """
    Winery = TEST_MODELS['Winery']
    winery = Winery(
        name="Test Winery",
        region="Napa Valley"
    )
    db_session.add(winery)
    await db_session.flush()  # Flush to get ID without committing transaction
    return winery


@pytest_asyncio.fixture
async def test_vineyard(db_session, test_winery):
    """
    Create a test vineyard for integration tests.
    
    Returns a Vineyard entity persisted in the database.
    Depends on test_winery fixture.
    """
    Vineyard = TEST_MODELS['Vineyard']
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
async def test_vineyard_block(db_session, test_vineyard):
    """
    Create a test vineyard block for integration tests.
    
    Returns a VineyardBlock entity persisted in the database.
    Depends on test_vineyard fixture.
    """
    VineyardBlock = TEST_MODELS['VineyardBlock']
    block = VineyardBlock(
        id=1,
        vineyard_id=test_vineyard.id,
        code="BLK001",
        soil_type="Clay loam",
        area_ha=2.5,
        is_deleted=False  # Explicitly set for soft-delete consistency
    )
    db_session.add(block)
    await db_session.flush()
    return block


@pytest_asyncio.fixture
async def test_user(db_session, test_winery):
    """
    Create a test user for integration tests.
    
    Returns a User entity persisted in the database.
    Depends on test_winery fixture.
    """
    User = TEST_MODELS['User']
    
    user = User(
        username="testuser",
        email="test@winery.com",
        full_name="Test User",
        password_hash="hashed_password_here",
        winery_id=test_winery.id,
    )
    db_session.add(user)
    await db_session.flush()  # Flush to get ID without committing transaction
    return user


@pytest_asyncio.fixture
async def test_fermentation(db_session, test_user):
    """
    Create a test fermentation for integration tests.
    
    Returns a Fermentation entity persisted in the database.
    Depends on test_user fixture.
    """
    Fermentation = TEST_MODELS['Fermentation']
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
    await db_session.flush()  # Flush to get ID without committing transaction
    return fermentation


@pytest_asyncio.fixture
async def test_harvest_lot(db_session, test_winery, test_vineyard_block):
    """
    Create a test harvest lot for integration tests.
    
    Returns a HarvestLot entity persisted in the database.
    Depends on test_winery and test_vineyard_block fixtures.
    """
    from datetime import date
    HarvestLot = TEST_MODELS['HarvestLot']
    
    harvest_lot = HarvestLot(
        id=1,
        winery_id=test_winery.id,
        block_id=test_vineyard_block.id,
        code="HL2024001",
        harvest_date=date(2024, 9, 15),
        weight_kg=1500.0,
        brix_at_harvest=24.5,
        grape_variety="Cabernet Sauvignon",
        is_deleted=False  # Explicitly set for soft-delete consistency
    )
    db_session.add(harvest_lot)
    await db_session.flush()
    return harvest_lot


@pytest_asyncio.fixture
async def sample_repository(db_session):
    """
    SampleRepository instance configured with test database session.
    
    Uses a mock SessionManager that returns the test session,
    allowing repository to work with the transactional test session.
    """
    from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository
    from contextlib import asynccontextmanager
    
    # Mock SessionManager to use test session
    class TestSessionManager:
        """Mock session manager for testing."""
        
        def __init__(self, session):
            self._session = session
        
        @asynccontextmanager
        async def get_session(self):
            """Return async context manager that yields test session."""
            yield self._session
        
        async def close(self):
            """No-op - session managed by test fixture."""
            pass
    
    session_manager = TestSessionManager(db_session)
    return SampleRepository(session_manager)


@pytest_asyncio.fixture
async def fermentation_repository(db_session):
    """
    FermentationRepository instance configured with test database session.
    
    Uses a mock SessionManager that returns the test session.
    """
    from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
    from contextlib import asynccontextmanager
    
    # Mock SessionManager (same pattern as sample_repository)
    class TestSessionManager:
        def __init__(self, session):
            self._session = session
        
        @asynccontextmanager
        async def get_session(self):
            """Return async context manager that yields test session."""
            yield self._session
        
        async def close(self):
            """No-op - session managed by test fixture."""
            pass
    
    session_manager = TestSessionManager(db_session)
    return FermentationRepository(session_manager)


@pytest_asyncio.fixture
async def harvest_lot_repository(db_session):
    """
    HarvestLotRepository instance configured with test database session.
    
    Uses a mock SessionManager that returns the test session,
    allowing repository to work with the transactional test session.
    """
    from src.modules.fruit_origin.src.repository_component.repositories.harvest_lot_repository import HarvestLotRepository
    from contextlib import asynccontextmanager
    
    # Mock SessionManager (same pattern as other repositories)
    class TestSessionManager:
        def __init__(self, session):
            self._session = session
        
        @asynccontextmanager
        async def get_session(self):
            """Return async context manager that yields test session."""
            yield self._session
        
        async def close(self):
            """No-op - session managed by test fixture."""
            pass
    
    session_manager = TestSessionManager(db_session)
    return HarvestLotRepository(session_manager)
