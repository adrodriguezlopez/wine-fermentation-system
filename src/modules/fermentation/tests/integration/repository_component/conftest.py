"""
Fixtures for repository_component integration tests.

This conftest provides fixtures for tests that need SampleRepository,
which is kept separate due to single-table inheritance metadata conflicts (ADR-011/ADR-013).

The sample entity models (SugarSample, DensitySample, CelsiusTemperatureSample) are imported
here locally to avoid global metadata registration issues.
"""

import pytest_asyncio
from src.shared.testing.integration.fixtures import create_repository_fixture
from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository

# Create sample_repository fixture
# This is separate from the main conftest to avoid metadata conflicts
sample_repository = create_repository_fixture(SampleRepository)


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
