"""
Unit tests for API dependencies.

Tests FastAPI dependency injection functions to ensure proper service/repository initialization.
ADR-033: Phase 1 - API Layer coverage improvement.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent / "src"))

from src.modules.fermentation.src.api.dependencies import (
    get_fermentation_validator,
    get_fermentation_repository,
    get_fermentation_service,
    get_sample_repository,
    get_chronology_validator,
    get_value_validator,
    get_business_rules_validator,
    get_validation_orchestrator,
    get_sample_service,
    get_unit_of_work
)


# ==================== Tests for Fermentation Dependencies ====================


def test_get_fermentation_validator():
    """Should return FermentationValidator instance."""
    validator = get_fermentation_validator()
    
    assert validator is not None
    # Verify it's a validator by checking class name
    assert 'Validator' in validator.__class__.__name__
    # Stateless - multiple calls should return new instances
    validator2 = get_fermentation_validator()
    assert validator is not validator2


@pytest.mark.asyncio
async def test_get_fermentation_repository():
    """Should return FermentationRepository with session manager."""
    mock_session = Mock(spec=AsyncSession)
    
    repository = await get_fermentation_repository(mock_session)
    
    assert repository is not None
    assert 'Repository' in repository.__class__.__name__


@pytest.mark.asyncio
async def test_get_fermentation_service():
    """Should return FermentationService with injected dependencies."""
    mock_session = Mock(spec=AsyncSession)
    
    repository = await get_fermentation_repository(mock_session)
    validator = get_fermentation_validator()
    
    service = await get_fermentation_service(repository, validator)
    
    assert service is not None
    assert 'Service' in service.__class__.__name__


# ==================== Tests for Sample Dependencies ====================


@pytest.mark.asyncio
async def test_get_sample_repository():
    """Should return SampleRepository with session manager."""
    mock_session = Mock(spec=AsyncSession)
    
    repository = await get_sample_repository(mock_session)
    
    assert repository is not None
    assert 'Repository' in repository.__class__.__name__


@pytest.mark.asyncio
async def test_get_chronology_validator():
    """Should return ChronologyValidationService with sample repository."""
    mock_session = Mock(spec=AsyncSession)
    
    sample_repo = await get_sample_repository(mock_session)
    validator = await get_chronology_validator(sample_repo)
    
    assert validator is not None
    assert 'Validation' in validator.__class__.__name__ or 'Service' in validator.__class__.__name__


def test_get_value_validator():
    """Should return ValueValidationService instance."""
    validator = get_value_validator()
    
    assert validator is not None
    assert 'Validation' in validator.__class__.__name__ or 'Service' in validator.__class__.__name__
    # Stateless - multiple calls should return new instances
    validator2 = get_value_validator()
    assert validator is not validator2


@pytest.mark.asyncio
async def test_get_business_rules_validator():
    """Should return BusinessRuleValidationService with repositories."""
    mock_session = Mock(spec=AsyncSession)
    
    sample_repo = await get_sample_repository(mock_session)
    fermentation_repo = await get_fermentation_repository(mock_session)
    
    validator = await get_business_rules_validator(sample_repo, fermentation_repo)
    
    assert validator is not None
    assert 'Validation' in validator.__class__.__name__ or 'Service' in validator.__class__.__name__


@pytest.mark.asyncio
async def test_get_validation_orchestrator():
    """Should return ValidationOrchestrator with all validators."""
    mock_session = Mock(spec=AsyncSession)
    
    sample_repo = await get_sample_repository(mock_session)
    fermentation_repo = await get_fermentation_repository(mock_session)
    
    chronology_validator = await get_chronology_validator(sample_repo)
    value_validator = get_value_validator()
    business_rules_validator = await get_business_rules_validator(sample_repo, fermentation_repo)
    
    orchestrator = await get_validation_orchestrator(
        chronology_validator,
        value_validator,
        business_rules_validator
    )
    
    assert orchestrator is not None
    assert 'Orchestrator' in orchestrator.__class__.__name__


@pytest.mark.asyncio
async def test_get_sample_service():
    """Should return SampleService with all dependencies."""
    mock_session = Mock(spec=AsyncSession)
    
    # Build dependency chain
    sample_repo = await get_sample_repository(mock_session)
    fermentation_repo = await get_fermentation_repository(mock_session)
    
    chronology_validator = await get_chronology_validator(sample_repo)
    value_validator = get_value_validator()
    business_rules_validator = await get_business_rules_validator(sample_repo, fermentation_repo)
    
    validation_orchestrator = await get_validation_orchestrator(
        chronology_validator,
        value_validator,
        business_rules_validator
    )
    
    service = await get_sample_service(sample_repo, validation_orchestrator, fermentation_repo)
    
    assert service is not None
    assert 'Service' in service.__class__.__name__


# ==================== Tests for UnitOfWork ====================


@pytest.mark.asyncio
async def test_get_unit_of_work():
    """Should return UnitOfWork with session manager."""
    mock_session = Mock(spec=AsyncSession)
    
    uow = await get_unit_of_work(mock_session)
    
    assert uow is not None
    assert 'UnitOfWork' in uow.__class__.__name__


# ==================== Integration Tests - Full Dependency Chain ====================


@pytest.mark.asyncio
async def test_full_fermentation_dependency_chain():
    """Should resolve full fermentation service dependency chain."""
    mock_session = Mock(spec=AsyncSession)
    
    # Simulate FastAPI dependency resolution
    repository = await get_fermentation_repository(mock_session)
    validator = get_fermentation_validator()
    service = await get_fermentation_service(repository, validator)
    
    # Verify all components are properly initialized
    assert service is not None
    assert repository is not None
    assert validator is not None


@pytest.mark.asyncio
async def test_full_sample_dependency_chain():
    """Should resolve full sample service dependency chain."""
    mock_session = Mock(spec=AsyncSession)
    
    # Simulate FastAPI dependency resolution (complete chain)
    sample_repo = await get_sample_repository(mock_session)
    fermentation_repo = await get_fermentation_repository(mock_session)
    
    chronology_validator = await get_chronology_validator(sample_repo)
    value_validator = get_value_validator()
    business_rules_validator = await get_business_rules_validator(sample_repo, fermentation_repo)
    
    validation_orchestrator = await get_validation_orchestrator(
        chronology_validator,
        value_validator,
        business_rules_validator
    )
    
    service = await get_sample_service(sample_repo, validation_orchestrator, fermentation_repo)
    
    # Verify all components in chain
    assert service is not None
    assert sample_repo is not None
    assert fermentation_repo is not None
    assert chronology_validator is not None
    assert value_validator is not None
    assert business_rules_validator is not None
    assert validation_orchestrator is not None


@pytest.mark.asyncio
async def test_dependencies_use_same_session():
    """Should use the same session across multiple repository dependencies."""
    mock_session = Mock(spec=AsyncSession)
    
    # Multiple repositories should work with same session
    sample_repo = await get_sample_repository(mock_session)
    fermentation_repo = await get_fermentation_repository(mock_session)
    uow = await get_unit_of_work(mock_session)
    
    # All should be initialized successfully with same session
    assert sample_repo is not None
    assert fermentation_repo is not None
    assert uow is not None


@pytest.mark.asyncio
async def test_stateless_validators_are_independent():
    """Should return independent instances for stateless validators."""
    # Stateless validators should return new instances
    validator1 = get_fermentation_validator()
    validator2 = get_fermentation_validator()
    
    value_validator1 = get_value_validator()
    value_validator2 = get_value_validator()
    
    assert validator1 is not validator2
    assert value_validator1 is not value_validator2
