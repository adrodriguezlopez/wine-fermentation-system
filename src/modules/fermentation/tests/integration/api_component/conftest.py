"""
Fixtures for Historical Data API integration tests.

Provides fixtures for testing the API layer with real database.

Updated for ADR-034: Now uses FermentationService, PatternAnalysisService, and SampleService
instead of deprecated HistoricalDataService.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from httpx import AsyncClient
from fastapi import FastAPI

from src.modules.fermentation.src.api_component.historical.routers.historical_router import (
    router,
    get_winery_id
)
# ADR-034: Use new services instead of HistoricalDataService
from src.modules.fermentation.src.api.dependencies import (
    get_fermentation_service,
    get_pattern_analysis_service,
    get_sample_service
)
from src.modules.fermentation.src.service_component.services.fermentation_service import FermentationService
from src.modules.fermentation.src.service_component.services.pattern_analysis_service import PatternAnalysisService
from src.modules.fermentation.src.service_component.services.sample_service import SampleService
from src.modules.fermentation.src.service_component.validators.fermentation_validator import FermentationValidator
from src.modules.fermentation.src.service_component.services.validation_orchestrator import ValidationOrchestrator
from src.modules.fermentation.src.service_component.services.chronology_validation_service import ChronologyValidationService
from src.modules.fermentation.src.service_component.services.value_validation_service import ValueValidationService
from src.modules.fermentation.src.service_component.services.business_rule_validation_service import BusinessRuleValidationService
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository
from src.shared.infra.repository.fastapi_session_manager import FastAPISessionManager
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus


@pytest.fixture
def app():
    """Create FastAPI app with historical router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest_asyncio.fixture
async def fermentation_service(db_session):
    """Create FermentationService with real repositories (ADR-034)."""
    session_manager = FastAPISessionManager(db_session)
    fermentation_repo = FermentationRepository(session_manager)
    validator = FermentationValidator()
    
    return FermentationService(
        fermentation_repo=fermentation_repo,
        validator=validator
    )


@pytest_asyncio.fixture
async def pattern_analysis_service(db_session):
    """Create PatternAnalysisService with real repositories (ADR-034)."""
    session_manager = FastAPISessionManager(db_session)
    fermentation_repo = FermentationRepository(session_manager)
    sample_repo = SampleRepository(session_manager)
    
    return PatternAnalysisService(
        fermentation_repo=fermentation_repo,
        sample_repo=sample_repo
    )


@pytest_asyncio.fixture
async def sample_service(db_session):
    """Create SampleService with real repositories (ADR-034)."""
    session_manager = FastAPISessionManager(db_session)
    sample_repo = SampleRepository(session_manager)
    fermentation_repo = FermentationRepository(session_manager)
    
    # Create validation orchestrator
    chronology_validator = ChronologyValidationService(sample_repository=sample_repo)
    value_validator = ValueValidationService()
    business_rules_validator = BusinessRuleValidationService(
        sample_repository=sample_repo,
        fermentation_repository=fermentation_repo
    )
    validation_orchestrator = ValidationOrchestrator(
        chronology_validator=chronology_validator,
        value_validator=value_validator,
        business_rules_validator=business_rules_validator
    )
    
    return SampleService(
        sample_repo=sample_repo,
        validation_orchestrator=validation_orchestrator,
        fermentation_repo=fermentation_repo
    )


@pytest_asyncio.fixture
async def test_client(app, fermentation_service, pattern_analysis_service, sample_service, test_user):
    """Create async test client with dependency overrides (ADR-034)."""
    def override_fermentation_service():
        return fermentation_service
    
    def override_pattern_service():
        return pattern_analysis_service
    
    def override_sample_service():
        return sample_service
    
    def override_winery_id():
        return test_user.winery_id
    
    app.dependency_overrides[get_fermentation_service] = override_fermentation_service
    app.dependency_overrides[get_pattern_analysis_service] = override_pattern_service
    app.dependency_overrides[get_sample_service] = override_sample_service
    app.dependency_overrides[get_winery_id] = override_winery_id
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
def test_models_with_samples(test_models):
    """
    Extend test_models with Sample classes for tests that need them.
    
    This imports Sample models locally to avoid global metadata registration.
    """
    from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
    from src.modules.fermentation.src.domain.entities.samples.density_sample import DensitySample
    from src.modules.fermentation.src.domain.entities.samples.celcius_temperature_sample import CelsiusTemperatureSample
    
    # Add sample models to test_models dict
    test_models['SugarSample'] = SugarSample
    test_models['DensitySample'] = DensitySample
    test_models['CelsiusTemperatureSample'] = CelsiusTemperatureSample
    
    return test_models


@pytest_asyncio.fixture
async def historical_fermentation(test_models, db_session, test_user):
    """Create a test fermentation with data_source='HISTORICAL'."""
    Fermentation = test_models['Fermentation']
    
    fermentation = Fermentation(
        winery_id=test_user.winery_id,
        fermented_by_user_id=test_user.id,
        vintage_year=2023,
        yeast_strain="EC-1118",
        vessel_code="HIST-001",
        input_mass_kg=1000.0,
        initial_sugar_brix=24.5,
        initial_density=1.105,
        start_date=datetime(2023, 9, 1, 8, 0, 0),
        status=FermentationStatus.COMPLETED,
        data_source="HISTORICAL"  # Critical for filtering
    )
    
    db_session.add(fermentation)
    await db_session.flush()
    return fermentation


@pytest_asyncio.fixture
async def historical_samples(test_models_with_samples, db_session, historical_fermentation, test_user):
    """Create test samples for historical fermentation."""
    DensitySample = test_models_with_samples['DensitySample']
    SugarSample = test_models_with_samples['SugarSample']
    
    # Initial readings
    density1 = DensitySample(
        fermentation_id=historical_fermentation.id,
        recorded_by_user_id=test_user.id,
        recorded_at=datetime(2023, 9, 1, 9, 0, 0),
        value=1.105,
        data_source="HISTORICAL"
    )
    sugar1 = SugarSample(
        fermentation_id=historical_fermentation.id,
        recorded_by_user_id=test_user.id,
        recorded_at=datetime(2023, 9, 1, 9, 0, 0),
        value=24.5,
        data_source="HISTORICAL"
    )
    
    # Final readings
    density2 = DensitySample(
        fermentation_id=historical_fermentation.id,
        recorded_by_user_id=test_user.id,
        recorded_at=datetime(2023, 9, 15, 9, 0, 0),
        value=0.993,
        data_source="HISTORICAL"
    )
    sugar2 = SugarSample(
        fermentation_id=historical_fermentation.id,
        recorded_by_user_id=test_user.id,
        recorded_at=datetime(2023, 9, 15, 9, 0, 0),
        value=0.5,
        data_source="HISTORICAL"
    )
    
    db_session.add_all([density1, sugar1, density2, sugar2])
    await db_session.flush()
    
    return [density1, sugar1, density2, sugar2]


@pytest_asyncio.fixture
async def multiple_historical_fermentations(test_models, db_session, test_user):
    """Create multiple historical fermentations for aggregation tests."""
    Fermentation = test_models['Fermentation']
    
    fermentations = []
    for i in range(5):
        ferm = Fermentation(
            winery_id=test_user.winery_id,
            fermented_by_user_id=test_user.id,
            vintage_year=2023,
            yeast_strain="EC-1118" if i % 2 == 0 else "D47",
            vessel_code=f"HIST-{i+10:03d}",
            input_mass_kg=800.0 + (i * 100),
            initial_sugar_brix=23.0 + i,
            initial_density=1.095 + (i * 0.005),
            start_date=datetime(2023, 9, 1 + i, 8, 0, 0),
            status=FermentationStatus.COMPLETED if i < 4 else FermentationStatus.STUCK,
            data_source="HISTORICAL"
        )
        fermentations.append(ferm)
        db_session.add(ferm)
    
    await db_session.flush()
    return fermentations


@pytest_asyncio.fixture
async def other_winery_fermentation(test_models, db_session):
    """Create a fermentation in a different winery for isolation tests."""
    Fermentation = test_models['Fermentation']
    User = test_models['User']
    Winery = test_models['Winery']
    
    # Create another winery
    from uuid import uuid4
    other_winery = Winery(
        code=f"OTHER-{uuid4().hex[:8].upper()}",
        name="Other Winery",
        location="Sonoma"
    )
    db_session.add(other_winery)
    await db_session.flush()
    
    # Create user in other winery
    other_user = User(
        id=99999,
        winery_id=other_winery.id,
        username="other_user",
        email="other@example.com",
        password_hash="fake_hash_for_test",
        full_name="Other User",
        role="viewer"
    )
    db_session.add(other_user)
    await db_session.flush()
    
    # Create fermentation in other winery
    ferm = Fermentation(
        winery_id=other_winery.id,
        fermented_by_user_id=other_user.id,
        vintage_year=2023,
        yeast_strain="RC-212",
        vessel_code="OTHER-001",
        input_mass_kg=500.0,
        initial_sugar_brix=22.0,
        initial_density=1.092,
        start_date=datetime(2023, 8, 1, 8, 0, 0),
        status=FermentationStatus.COMPLETED,
        data_source="HISTORICAL"
    )
    db_session.add(ferm)
    await db_session.flush()
    
    return ferm
