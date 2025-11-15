import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from service_component.services.chronology_validation_service import ChronologyValidationService
from domain.enums.sample_type import SampleType

@pytest.fixture
def mock_sample_repository():
    """Create a mock repository with async methods."""
    mock_repo = Mock()
    # Make the async methods return AsyncMock
    mock_repo.get_latest_sample_by_type = AsyncMock()
    mock_repo.get_fermentation_temperature_range = AsyncMock()
    mock_repo.get_samples_by_fermentation_id = AsyncMock()
    mock_repo.get_fermentation_start_date = AsyncMock()
    return mock_repo

@pytest.fixture
def chronology_validation_service(mock_sample_repository):
    return ChronologyValidationService(sample_repository=mock_sample_repository)

@pytest.mark.asyncio
async def test_chronology_validation_service_validates_chronology(chronology_validation_service):
    # Arrange
    new_sample = Mock()
    new_sample.sample_type = SampleType.SUGAR
    new_sample.recorded_at = datetime(2023, 10, 1, 12, 0, 0)  # Newer timestamp

    existing_sample = Mock()
    existing_sample.sample_type = SampleType.SUGAR
    existing_sample.recorded_at = datetime(2023, 10, 1, 11, 0, 0)  # Older timestamp
    
    chronology_validation_service.sample_repository.get_samples_by_fermentation_id.return_value = [existing_sample]

    # Act
    result = await chronology_validation_service.validate_sample_chronology(fermentation_id=1, new_sample=new_sample)

    # Assert
    assert result.is_valid is True
    assert result.errors == []
    chronology_validation_service.sample_repository.get_samples_by_fermentation_id.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_chronology_validation_service_invalidates_chronology(chronology_validation_service):
    # Arrange
    new_sample = Mock()
    new_sample.sample_type = SampleType.SUGAR
    new_sample.value = 10.0
    new_sample.recorded_at = datetime(2023, 10, 1, 10, 0, 0)  # Older timestamp

    existing_sample = Mock()
    existing_sample.sample_type = SampleType.SUGAR
    existing_sample.recorded_at = datetime(2023, 10, 1, 11, 0, 0)  # Newer timestamp

    chronology_validation_service.sample_repository.get_samples_by_fermentation_id.return_value = [existing_sample]

    # Act
    result = await chronology_validation_service.validate_sample_chronology(fermentation_id=1, new_sample=new_sample)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "New sample's timestamp must be after the latest sample of the same type" in result.errors[0].message
    chronology_validation_service.sample_repository.get_samples_by_fermentation_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_chronology_validation_service_handles_no_previous_samples(chronology_validation_service):
    # Arrange
    new_sample = Mock()
    new_sample.sample_type = SampleType.SUGAR
    new_sample.recorded_at = datetime(2023, 10, 1, 12, 0, 0)  # Any timestamp

    chronology_validation_service.sample_repository.get_samples_by_fermentation_id.return_value = []

    # Act
    result = await chronology_validation_service.validate_sample_chronology(fermentation_id=1, new_sample=new_sample)

    # Assert
    assert result.is_valid is True
    assert result.errors == []
    chronology_validation_service.sample_repository.get_samples_by_fermentation_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_chronology_validation_service_handles_missing_sample_type(chronology_validation_service):
    # Arrange
    new_sample = Mock()
    new_sample.sample_type = None  # Missing sample type
    new_sample.recorded_at = datetime(2023, 10, 1, 12, 0, 0)

    # Act
    result = await chronology_validation_service.validate_sample_chronology(fermentation_id=1, new_sample=new_sample)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].field == "sample_type"
    assert "Sample type is required for chronology validation" in result.errors[0].message


@pytest.mark.asyncio
async def test_chronology_validation_service_handles_missing_timestamp(chronology_validation_service):
    # Arrange
    new_sample = Mock()
    new_sample.sample_type = SampleType.SUGAR
    new_sample.recorded_at = None  # Missing timestamp

    # Act
    result = await chronology_validation_service.validate_sample_chronology(fermentation_id=1, new_sample=new_sample)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].field == "recorded_at"
    assert "Sample timestamp is required for chronology validation" in result.errors[0].message


@pytest.mark.asyncio
async def test_chronology_validation_service_handles_repository_exception(chronology_validation_service):
    # Arrange
    new_sample = Mock()
    new_sample.sample_type = SampleType.SUGAR
    new_sample.recorded_at = datetime(2023, 10, 1, 12, 0, 0)

    chronology_validation_service.sample_repository.get_samples_by_fermentation_id.side_effect = Exception("Database error")

    # Act
    result = await chronology_validation_service.validate_sample_chronology(fermentation_id=1, new_sample=new_sample)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].field == "chronology"
    assert "Chronology validation failed: Database error" in result.errors[0].message
    chronology_validation_service.sample_repository.get_samples_by_fermentation_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_chronology_validation_service_handles_missing_repository():
    # Arrange
    service = ChronologyValidationService(sample_repository=None)
    new_sample = Mock()
    new_sample.sample_type = SampleType.SUGAR
    new_sample.recorded_at = datetime(2023, 10, 1, 12, 0, 0)

    # Act
    result = await service.validate_sample_chronology(fermentation_id=1, new_sample=new_sample)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].field == "repository"
    assert "Sample repository is not available for chronology validation" in result.errors[0].message


@pytest.mark.asyncio
async def test_chronology_validation_validate_fermentation_timeline(chronology_validation_service):
    # Arrange
    fermentation_start = datetime(2023, 10, 1, 10, 0, 0)
    sample_time = datetime(2023, 10, 1, 12, 0, 0)

    chronology_validation_service.sample_repository.get_fermentation_start_date.return_value = fermentation_start

    # Act
    result = await chronology_validation_service.validate_fermentation_timeline(fermentation_id=1, sample_timestamp=sample_time)

    # Assert
    assert result.is_valid is True
    assert result.errors == []
    chronology_validation_service.sample_repository.get_fermentation_start_date.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_chronology_validation_validate_fermentation_timeline_invalid(chronology_validation_service):
    # Arrange
    fermentation_start = datetime(2023, 10, 1, 10, 0, 0)
    sample_time = datetime(2023, 10, 1, 9, 0, 0)  # Before start

    chronology_validation_service.sample_repository.get_fermentation_start_date.return_value = fermentation_start

    # Act
    result = await chronology_validation_service.validate_fermentation_timeline(fermentation_id=1, sample_timestamp=sample_time)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Sample timestamp cannot be before fermentation start date" in result.errors[0].message
    chronology_validation_service.sample_repository.get_fermentation_start_date.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_chronology_validation_validate_fermentation_timeline_handles_missing_timestamp(chronology_validation_service):
    # Arrange
    sample_time = None  # Missing timestamp

    # Act
    result = await chronology_validation_service.validate_fermentation_timeline(fermentation_id=1, sample_timestamp=sample_time)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].field == "recorded_at"
    assert "Sample timestamp is required for fermentation timeline validation" in result.errors[0].message


@pytest.mark.asyncio
async def test_chronology_validation_validate_fermentation_timeline_handles_repository_exception(chronology_validation_service):
    # Arrange
    sample_time = datetime(2023, 10, 1, 12, 0, 0)

    chronology_validation_service.sample_repository.get_fermentation_start_date.side_effect = Exception("Database error")

    # Act
    result = await chronology_validation_service.validate_fermentation_timeline(fermentation_id=1, sample_timestamp=sample_time)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].field == "fermentation_timeline"
    assert "Fermentation timeline validation failed: Database error" in result.errors[0].message
    chronology_validation_service.sample_repository.get_fermentation_start_date.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_chronology_validation_validate_fermentation_timeline_handles_missing_repository():
    # Arrange
    service = ChronologyValidationService(sample_repository=None)
    sample_time = datetime(2023, 10, 1, 12, 0, 0)

    # Act
    result = await service.validate_fermentation_timeline(fermentation_id=1, sample_timestamp=sample_time)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].field == "repository"
    assert "Sample repository is not available for fermentation timeline validation" in result.errors[0].message


@pytest.mark.asyncio
async def test_chronology_validation_validate_fermentation_timeline_handles_no_previous_samples(chronology_validation_service):
    # Arrange
    fermentation_start = None
    sample_time = datetime(2023, 10, 1, 12, 0, 0)

    chronology_validation_service.sample_repository.get_fermentation_start_date.return_value = fermentation_start

    # Act
    result = await chronology_validation_service.validate_fermentation_timeline(fermentation_id=1, sample_timestamp=sample_time)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].field == "fermentation_start"
    assert "Fermentation start date not found for the given ID" in result.errors[0].message
    chronology_validation_service.sample_repository.get_fermentation_start_date.assert_called_once_with(1)
