import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from service_component.services.business_rule_validation_service import BusinessRuleValidationService
from domain.enums.sample_type import SampleType

@pytest.fixture
def mock_sample_repository():
    """Create a mock repository with async methods."""
    mock_repo = Mock()
    # Make the async methods return AsyncMock
    mock_repo.get_latest_sample_by_type = AsyncMock()
    return mock_repo

@pytest.fixture
def mock_fermentation_repository():
    mock_repo = Mock()
    mock_repo.get_fermentation_temperature_range = AsyncMock()

    return mock_repo

@pytest.fixture
def business_validation_service(mock_sample_repository, mock_fermentation_repository):
    return BusinessRuleValidationService(sample_repository=mock_sample_repository, fermentation_repository=mock_fermentation_repository)

@pytest.mark.asyncio
async def test_business_rule_validation_service_validates_sugar_trend_decreasing(business_validation_service):
    # Arrange
    previous_sample = Mock()
    previous_sample.value = 12.0  # Previous sugar level higher than current
    business_validation_service.sample_repository.get_latest_sample_by_type.return_value = previous_sample

    # Act
    result = await business_validation_service.validate_sugar_trend(current=10.0, fermentation_id=1)

    # Assert
    assert result.is_valid is True
    assert result.errors == []
    business_validation_service.sample_repository.get_latest_sample_by_type.assert_called_once_with(1, SampleType.SUGAR)

@pytest.mark.asyncio
async def test_business_rule_validation_service_invalidates_sugar_trend_increasing(business_validation_service):
    # Arrange
    previous_sample = Mock()
    previous_sample.value = 12.0  # Previous sugar level lower than current (invalid trend)
    business_validation_service.sample_repository.get_latest_sample_by_type.return_value = previous_sample

    # Act
    result = await business_validation_service.validate_sugar_trend(current=13.0, fermentation_id=1)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Increasing trend is not allowed" in result.errors[0].message

@pytest.mark.asyncio
async def test_business_rule_validation_service_handles_no_previous_sample(business_validation_service):
    # Arrange
    business_validation_service.sample_repository.get_latest_sample_by_type.return_value = None  # No previous sample

    # Act
    result = await business_validation_service.validate_sugar_trend(current=10.0, fermentation_id=1)

    # Assert
    assert result.is_valid is True
    assert result.errors == []

@pytest.mark.asyncio
async def test_business_rule_validation_service_handles_missing_sample_repository():
    # Arrange
    service = BusinessRuleValidationService(sample_repository=None, fermentation_repository=None)  # No repository

    # Act
    result = await service.validate_sugar_trend(current=10.0, fermentation_id=1)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Sample repository is not available for business rule validation" in result.errors[0].message


@pytest.mark.asyncio
async def test_business_rule_validation_service_handles_missing_fermentation_repository():
    # Arrange
    mock_sample_repo = Mock()
    mock_sample_repo.get_latest_sample_by_type = AsyncMock(return_value=None)  # No previous sample
    service = BusinessRuleValidationService(sample_repository=mock_sample_repo, fermentation_repository=None)  # No fermentation repository

    # Act
    result = await service.validate_temperature_range(temperature=25.0, fermentation_id=1)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Fermentation repository is not available for business rule validation" in result.errors[0].message


@pytest.mark.asyncio
async def test_business_rule_validation_service_validates_temperature_within_range(business_validation_service):
    # Arrange
    business_validation_service.fermentation_repository.get_fermentation_temperature_range.return_value = (18.0, 30.0)  # Acceptable range

    # Act
    result = await business_validation_service.validate_temperature_range(temperature=25.0, fermentation_id=1)

    # Assert
    assert result.is_valid is True
    assert result.errors == []

@pytest.mark.asyncio
async def test_business_rule_validation_service_invalidates_temperature_out_of_range(business_validation_service):
    # Arrange
    business_validation_service.fermentation_repository.get_fermentation_temperature_range.return_value = (18.0, 30.0)  # Acceptable range

    # Act
    result = await business_validation_service.validate_temperature_range(temperature=35.0, fermentation_id=1)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Temperature 35.0 is out of acceptable range (18.0 - 30.0)" in result.errors[0].message


@pytest.mark.asyncio
async def test_business_rule_validation_service_handles_no_temperature_range(business_validation_service):
    # Arrange
    business_validation_service.fermentation_repository.get_fermentation_temperature_range.return_value = None  # No range defined

    # Act
    result = await business_validation_service.validate_temperature_range(temperature=25.0, fermentation_id=1)

    # Assert
    assert result.is_valid is True
    assert result.errors == []

@pytest.mark.asyncio
async def test_business_rule_validation_service_handles_missing_repository_temp(mock_sample_repository):
    # Arrange
    service = BusinessRuleValidationService(sample_repository=mock_sample_repository, fermentation_repository=None)  # No repository

    # Act
    result = await service.validate_temperature_range(temperature=25.0, fermentation_id=1)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Fermentation repository is not available for business rule validation" in result.errors[0].message



