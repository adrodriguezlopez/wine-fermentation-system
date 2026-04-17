"""
Integration test fixtures for analysis_engine module.

Uses real PostgreSQL (localhost:5433/wine_fermentation_test) because:
- JSONB columns (Analysis.comparison_result, Analysis.confidence_level, Anomaly.deviation_score)
  require PostgreSQL — SQLite has no JSONB support.
- ComparisonService.find_similar_fermentations() queries the Fermentation table
  from the fermentation module, so both modules' ORM models must be registered
  together and the real DB dialect must handle the cross-table query.

Prerequisites:
    docker compose -f docker-compose.inttest.yml up --wait

Key design notes:
- Fermentation uses BaseEntity (integer PKs, winery_id = int FK to wineries.id).
- Analysis uses Base (UUID PKs, winery_id = UUID, no FK to fermentations table).
  The two modules are deliberately decoupled: analysis stores fermentation_id as a
  plain UUID, and ComparisonService looks up Fermentation rows independently.
- The full fermentation dependency chain (Winery → User → Fermentation) must be
  present so FK constraints are satisfied on CREATE TABLE and INSERT.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from uuid import uuid4

from src.shared.testing.integration import (
    IntegrationTestConfig,
    create_integration_fixtures,
)

# ── Fermentation-module models (cross-module dep for ComparisonService) ────────
from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.shared.auth.domain.entities.user import User
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource

# ── Analysis-engine models ─────────────────────────────────────────────────────
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.entities.recommendation import Recommendation
from src.modules.analysis_engine.src.domain.entities.recommendation_template import RecommendationTemplate
from src.modules.analysis_engine.src.domain.entities.protocol_advisory import ProtocolAdvisory

# PostgreSQL is required — analysis_engine uses JSONB, and ComparisonService
# queries need the real PostgreSQL dialect.
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/wine_fermentation_test"

config = IntegrationTestConfig(
    module_name="analysis_engine",
    models=[
        # Fermentation dependency chain (must come first: FK order)
        Winery,
        Vineyard,
        VineyardBlock,
        HarvestLot,
        User,
        Fermentation,
        FermentationNote,
        FermentationLotSource,
        # Analysis-engine models
        RecommendationTemplate,
        Analysis,
        Anomaly,
        Recommendation,
        ProtocolAdvisory,
    ],
    test_database_url=TEST_DATABASE_URL,
)

fixtures = create_integration_fixtures(config)
globals().update(fixtures)


# ── Convenience fixtures for building test data ────────────────────────────────


@pytest_asyncio.fixture
async def test_winery(test_models, db_session):
    """Create a test Winery row (required FK for Fermentation + User)."""
    Winery = test_models["Winery"]
    winery = Winery(
        code=f"AE-{uuid4().hex[:8].upper()}",
        name="Analysis Engine Test Winery",
        location="Test Valley",
    )
    db_session.add(winery)
    await db_session.flush()
    return winery


@pytest_asyncio.fixture
async def test_user(test_models, db_session, test_winery):
    """Create a test User row (required FK for Fermentation)."""
    User = test_models["User"]
    user = User(
        username=f"ae_user_{uuid4().hex[:6]}",
        email=f"ae_{uuid4().hex[:6]}@test.com",
        full_name="Analysis Engine Test User",
        password_hash="hashed_password",
        winery_id=test_winery.id,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def test_fermentation(test_models, db_session, test_user):
    """
    Create a test Fermentation row.

    NOTE: Fermentation uses BaseEntity (integer PK) and stores winery_id as an
    integer FK to wineries.id.  ComparisonService queries Fermentation by
    winery_id — but Analysis stores winery_id as a UUID.  These are different
    key spaces; the integration tests use the Fermentation.winery_id (int) only
    for satisfying FK constraints, and pass a separate UUID winery_id to the
    analysis-engine services.
    """
    from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus

    Fermentation = test_models["Fermentation"]
    fermentation = Fermentation(
        winery_id=test_user.winery_id,
        fermented_by_user_id=test_user.id,
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code=f"V-{uuid4().hex[:6]}",
        input_mass_kg=500.0,
        initial_sugar_brix=24.0,
        initial_density=1.100,
        start_date=datetime.now(),
        status=FermentationStatus.ACTIVE.value,
    )
    db_session.add(fermentation)
    await db_session.flush()
    return fermentation


@pytest_asyncio.fixture
def analysis_winery_id():
    """
    A fixed UUID used as winery_id for Analysis entities.

    Analysis-engine services operate in UUID-space (ADR-035: no cross-module
    ORM FK).  This fixture provides a stable UUID for assertions.
    """
    return uuid4()


@pytest_asyncio.fixture
def analysis_fermentation_id():
    """
    A fixed UUID used as fermentation_id for Analysis entities (UUID-space).
    """
    return uuid4()
