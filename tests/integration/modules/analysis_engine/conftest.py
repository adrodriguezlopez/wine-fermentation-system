"""
Fixtures for analysis_engine module integration tests.

Uses shared testing infrastructure from src/shared/testing/integration.
Uses PostgreSQL test database (localhost:5433) to support JSONB columns.
"""

import sys
from pathlib import Path

# Add project root and src/ to sys.path so 'src.*' imports resolve regardless
# of which directory pytest is invoked from.
# This file is at: tests/integration/modules/analysis_engine/conftest.py
# → 4 parents up = project root
_project_root = Path(__file__).parent.parent.parent.parent.parent
for _p in [str(_project_root), str(_project_root / "src")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Pre-import fermentation entities so SQLAlchemy mapper cascade resolves correctly
# when the shared Base configures all mappers at once.
try:
    import src.shared.auth.domain.entities.user  # noqa: F401
    import src.modules.fermentation.src.domain.entities.fermentation  # noqa: F401
    import src.modules.fermentation.src.domain.entities.fermentation_note  # noqa: F401
    import src.modules.fermentation.src.domain.entities.fermentation_lot_source  # noqa: F401
    import src.modules.fermentation.src.domain.entities.samples.base_sample  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_protocol  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_step  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_execution  # noqa: F401
    import src.modules.fermentation.src.domain.entities.step_completion  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_alert  # noqa: F401
except Exception:
    pass  # Degrade gracefully if fermentation module is not available

import pytest
import pytest_asyncio
from uuid import uuid4
from src.shared.testing.integration import create_integration_fixtures, IntegrationTestConfig
from src.shared.testing.integration.fixtures import create_repository_fixture
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.entities.recommendation import Recommendation
from src.modules.analysis_engine.src.domain.entities.recommendation_template import RecommendationTemplate
from src.modules.analysis_engine.src.repository_component.repositories.analysis_repository import AnalysisRepository
from src.modules.analysis_engine.src.repository_component.repositories.anomaly_repository import AnomalyRepository
from src.modules.analysis_engine.src.repository_component.repositories.recommendation_repository import RecommendationRepository
from src.modules.analysis_engine.src.repository_component.repositories.recommendation_template_repository import RecommendationTemplateRepository

# Configure integration test fixtures for analysis_engine module
# Using PostgreSQL test database (port 5433) to support JSONB columns
# All entities now use Entity = ORM pattern (no separate models)
config = IntegrationTestConfig(
    module_name="analysis_engine",
    models=[Analysis, Anomaly, Recommendation, RecommendationTemplate],
    test_database_url="postgresql+asyncpg://postgres:postgres@localhost:5433/wine_fermentation_test"
)

# Create standard fixtures (test_models, db_engine, db_session)
fixtures = create_integration_fixtures(config)
globals().update(fixtures)

# Create repository fixtures
analysis_repository = create_repository_fixture(AnalysisRepository)
anomaly_repository = create_repository_fixture(AnomalyRepository)
recommendation_repository = create_repository_fixture(RecommendationRepository)
recommendation_template_repository = create_repository_fixture(RecommendationTemplateRepository)


# Test data fixtures
@pytest.fixture
def winery_id():
    """Provide a UUID for testing multi-tenant winery isolation."""
    return uuid4()


@pytest.fixture
def fermentation_id():
    """Provide a UUID for testing fermentation associations."""
    return uuid4()
