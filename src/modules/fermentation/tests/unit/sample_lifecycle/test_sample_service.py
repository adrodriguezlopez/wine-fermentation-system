"""
Test suite for SampleService implementation.

Tests business logic orchestration for sample management.
Following TDD approach with comprehensive test coverage.

Test Structure:
- TestAddSample: Sample creation with validation
- TestGetSample: Single sample retrieval
- TestGetSamplesByFermentation: List samples for fermentation
- TestGetLatestSample: Latest sample retrieval with optional type filter
- TestGetSamplesInTimerange: Time-based sample queries
- TestValidateSampleData: Pre-creation validation (dry-run)
- TestServiceImplementsInterface: Interface compliance verification
"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta

from src.modules.fermentation.src.service_component.services.sample_service import SampleService
from src.modules.fermentation.src.service_component.interfaces.sample_service_interface import ISampleService
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.dtos.sample_dtos import SampleCreate
from src.modules.fermentation.src.domain.enums.sample_type import SampleType
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.service_component.errors import (
    ValidationError,
    NotFoundError,
    BusinessRuleViolation
)
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import (
    ValidationResult,
    ValidationError as ValidationErrorModel
)


# ==================================================================================
# FIXTURES
# ==================================================================================

@pytest.fixture
def mock_sample_repo():
    """Mock ISampleRepository for testing."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_validation_orchestrator():
    """Mock IValidationOrchestrator for testing."""
    orchestrator = AsyncMock()
    return orchestrator


@pytest.fixture
def mock_fermentation_repo():
    """Mock IFermentationRepository for testing."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def sample_service(mock_sample_repo, mock_validation_orchestrator, mock_fermentation_repo):
    """SampleService instance with mocked dependencies."""
    return SampleService(
        sample_repo=mock_sample_repo,
        validation_orchestrator=mock_validation_orchestrator,
        fermentation_repo=mock_fermentation_repo
    )


@pytest.fixture
def sample_fermentation():
    """Sample fermentation entity for testing (mocked to avoid SQLAlchemy relationship issues)."""
    fermentation = Mock(spec=Fermentation)
    fermentation.id = 1
    fermentation.winery_id = 100
    fermentation.vessel_name = "Tank A"
    fermentation.variety = "Cabernet Sauvignon"
    fermentation.vintage_year = 2025
    fermentation.input_mass_kg = 1000.0
    fermentation.status = FermentationStatus.ACTIVE
    fermentation.start_date = datetime(2025, 10, 1)
    fermentation.created_at = datetime(2025, 10, 1)
    fermentation.updated_at = datetime(2025, 10, 1)
    return fermentation


@pytest.fixture
def sample_create_dto():
    """Sample creation DTO for testing."""
    return SampleCreate(
        sample_type=SampleType.SUGAR,
        value=15.5,
        units="Brix",
        recorded_at=datetime(2025, 10, 21, 10, 0, 0)
    )


@pytest.fixture
def sample_entity():
    """Sample BaseSample entity for testing (mocked to avoid SQLAlchemy relationship issues)."""
    sample = Mock(spec=BaseSample)
    sample.id = 1
    sample.fermentation_id = 1
    sample.sample_type = SampleType.SUGAR.value
    sample.value = 15.5
    sample.units = "Brix"
    sample.recorded_at = datetime(2025, 10, 21, 10, 0, 0)
    sample.recorded_by_user_id = 1
    sample.is_deleted = False
    return sample


@pytest.fixture
def valid_validation_result():
    """Valid ValidationResult (no errors)."""
    return ValidationResult(is_valid=True, errors=[], warnings=[])


@pytest.fixture
def invalid_validation_result():
    """Invalid ValidationResult with errors."""
    return ValidationResult(
        is_valid=False,
        errors=[
            ValidationErrorModel(
                field="value",
                message="Sugar value out of range",
                code="VALUE_OUT_OF_RANGE"
            )
        ],
        warnings=[]
    )


# ==================================================================================
# TEST: Service implements interface correctly
# ==================================================================================

class TestServiceImplementsInterface:
    """Verify SampleService correctly implements ISampleService."""
    
    def test_service_implements_interface(self, sample_service):
        """SampleService should implement ISampleService."""
        assert isinstance(sample_service, ISampleService)
    
    def test_service_has_all_methods(self, sample_service):
        """SampleService should have all required methods."""
        required_methods = [
            'add_sample',
            'get_sample',
            'get_samples_by_fermentation',
            'get_latest_sample',
            'get_samples_in_timerange',
            'validate_sample_data'
        ]
        
        for method_name in required_methods:
            assert hasattr(sample_service, method_name), f"Missing method: {method_name}"
            assert callable(getattr(sample_service, method_name))


# ==================================================================================
# TEST: add_sample() - Sample creation with validation
# ==================================================================================

class TestAddSample:
    """Test add_sample() method - TDD approach."""
    
    @pytest.mark.asyncio
    async def test_add_sample_happy_path(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_validation_orchestrator,
        mock_sample_repo,
        sample_fermentation,
        sample_create_dto,
        sample_entity,
        valid_validation_result
    ):
        """Should create sample when fermentation exists and validation passes."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_validation_orchestrator.validate_sample_complete.return_value = valid_validation_result
        mock_sample_repo.upsert_sample.return_value = sample_entity
        
        # Mock the factory method to avoid SQLAlchemy instantiation issues
        sample_service._create_sample_entity = Mock(return_value=sample_entity)
        
        # Act
        result = await sample_service.add_sample(
            fermentation_id=1,
            winery_id=100,
            user_id=1,
            data=sample_create_dto
        )
        
        # Assert
        assert result == sample_entity
        mock_fermentation_repo.get_by_id.assert_awaited_once_with(
            fermentation_id=1,
            winery_id=100
        )
        sample_service._create_sample_entity.assert_called_once_with(
            fermentation_id=1,
            user_id=1,
            data=sample_create_dto
        )
        mock_validation_orchestrator.validate_sample_complete.assert_awaited_once()
        mock_sample_repo.upsert_sample.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_add_sample_fermentation_not_found(
        self,
        sample_service,
        mock_fermentation_repo,
        sample_create_dto
    ):
        """Should raise NotFoundError when fermentation doesn't exist."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="Fermentation .* not found"):
            await sample_service.add_sample(
                fermentation_id=999,
                winery_id=100,
                user_id=1,
                data=sample_create_dto
            )
        
        mock_fermentation_repo.get_by_id.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_add_sample_fermentation_completed(
        self,
        sample_service,
        mock_fermentation_repo,
        sample_fermentation,
        sample_create_dto
    ):
        """Should raise BusinessRuleViolation when fermentation is completed."""
        # Arrange
        sample_fermentation.status = FermentationStatus.COMPLETED
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        
        # Act & Assert
        with pytest.raises(BusinessRuleViolation, match="Cannot add sample.*COMPLETED"):
            await sample_service.add_sample(
                fermentation_id=1,
                winery_id=100,
                user_id=1,
                data=sample_create_dto
            )
    
    @pytest.mark.asyncio
    async def test_add_sample_validation_fails(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_validation_orchestrator,
        sample_fermentation,
        sample_create_dto,
        sample_entity,
        invalid_validation_result
    ):
        """Should raise ValidationError when sample validation fails."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_validation_orchestrator.validate_sample_complete.return_value = invalid_validation_result
        
        # Mock the factory method
        sample_service._create_sample_entity = Mock(return_value=sample_entity)
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Sample validation failed"):
            await sample_service.add_sample(
                fermentation_id=1,
                winery_id=100,
                user_id=1,
                data=sample_create_dto
            )
        
        mock_validation_orchestrator.validate_sample_complete.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_add_sample_repository_error(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_validation_orchestrator,
        mock_sample_repo,
        sample_fermentation,
        sample_create_dto,
        sample_entity,
        valid_validation_result
    ):
        """Should propagate RepositoryError from repository."""
        # Arrange
        from src.modules.fermentation.src.repository_component.errors import RepositoryError
        
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_validation_orchestrator.validate_sample_complete.return_value = valid_validation_result
        mock_sample_repo.upsert_sample.side_effect = RepositoryError("Database error")
        
        # Mock the factory method
        sample_service._create_sample_entity = Mock(return_value=sample_entity)
        
        # Act & Assert
        with pytest.raises(RepositoryError, match="Database error"):
            await sample_service.add_sample(
                fermentation_id=1,
                winery_id=100,
                user_id=1,
                data=sample_create_dto
            )


# ==================================================================================
# TEST: get_sample() - Single sample retrieval
# ==================================================================================

class TestGetSample:
    """Test get_sample() method - TDD approach."""
    
    @pytest.mark.asyncio
    async def test_get_sample_happy_path(
        self,
        sample_service,
        mock_sample_repo,
        sample_entity
    ):
        """Should retrieve sample when it exists."""
        # Arrange
        mock_sample_repo.get_sample_by_id.return_value = sample_entity
        
        # Act
        result = await sample_service.get_sample(
            sample_id=1,
            fermentation_id=1,
            winery_id=100
        )
        
        # Assert
        assert result == sample_entity
        mock_sample_repo.get_sample_by_id.assert_awaited_once_with(
            sample_id=1,
            fermentation_id=1
        )
    
    @pytest.mark.asyncio
    async def test_get_sample_not_found(
        self,
        sample_service,
        mock_sample_repo
    ):
        """Should return None when sample doesn't exist."""
        # Arrange
        from src.modules.fermentation.src.repository_component.errors import EntityNotFoundError
        mock_sample_repo.get_sample_by_id.side_effect = EntityNotFoundError("Sample not found")
        
        # Act
        result = await sample_service.get_sample(
            sample_id=999,
            fermentation_id=1,
            winery_id=100
        )
        
        # Assert
        assert result is None
        mock_sample_repo.get_sample_by_id.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_get_sample_repository_error(
        self,
        sample_service,
        mock_sample_repo
    ):
        """Should propagate RepositoryError from repository."""
        # Arrange
        from src.modules.fermentation.src.repository_component.errors import RepositoryError
        mock_sample_repo.get_sample_by_id.side_effect = RepositoryError("Database error")
        
        # Act & Assert
        with pytest.raises(RepositoryError, match="Database error"):
            await sample_service.get_sample(
                sample_id=1,
                fermentation_id=1,
                winery_id=100
            )


# ==================================================================================
# TEST: get_samples_by_fermentation() - List samples
# ==================================================================================

class TestGetSamplesByFermentation:
    """Test get_samples_by_fermentation() method - TDD approach."""
    
    @pytest.mark.asyncio
    async def test_get_samples_by_fermentation_happy_path(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_sample_repo,
        sample_fermentation,
        sample_entity
    ):
        """Should return list of samples when fermentation exists."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_sample_repo.get_samples_by_fermentation_id.return_value = [sample_entity]
        
        # Act
        result = await sample_service.get_samples_by_fermentation(
            fermentation_id=1,
            winery_id=100
        )
        
        # Assert
        assert result == [sample_entity]
        mock_fermentation_repo.get_by_id.assert_awaited_once_with(
            fermentation_id=1,
            winery_id=100
        )
        mock_sample_repo.get_samples_by_fermentation_id.assert_awaited_once_with(
            fermentation_id=1
        )
    
    @pytest.mark.asyncio
    async def test_get_samples_by_fermentation_not_found(
        self,
        sample_service,
        mock_fermentation_repo
    ):
        """Should raise NotFoundError when fermentation doesn't exist."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="Fermentation .* not found"):
            await sample_service.get_samples_by_fermentation(
                fermentation_id=999,
                winery_id=100
            )
    
    @pytest.mark.asyncio
    async def test_get_samples_by_fermentation_empty_list(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_sample_repo,
        sample_fermentation
    ):
        """Should return empty list when no samples exist."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_sample_repo.get_samples_by_fermentation_id.return_value = []
        
        # Act
        result = await sample_service.get_samples_by_fermentation(
            fermentation_id=1,
            winery_id=100
        )
        
        # Assert
        assert result == []
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_samples_by_fermentation_repository_error(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_sample_repo,
        sample_fermentation
    ):
        """Should propagate RepositoryError from repository."""
        # Arrange
        from src.modules.fermentation.src.repository_component.errors import RepositoryError
        
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_sample_repo.get_samples_by_fermentation_id.side_effect = RepositoryError("Database error")
        
        # Act & Assert
        with pytest.raises(RepositoryError, match="Database error"):
            await sample_service.get_samples_by_fermentation(
                fermentation_id=1,
                winery_id=100
            )


# ==================================================================================
# TEST: get_latest_sample() - Latest sample retrieval
# ==================================================================================

class TestGetLatestSample:
    """Test get_latest_sample() method - TDD approach."""
    
    @pytest.mark.asyncio
    async def test_get_latest_sample_happy_path(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_sample_repo,
        sample_fermentation,
        sample_entity
    ):
        """Should return latest sample when samples exist."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_sample_repo.get_latest_sample.return_value = sample_entity
        
        # Act
        result = await sample_service.get_latest_sample(
            fermentation_id=1,
            winery_id=100
        )
        
        # Assert
        assert result == sample_entity
        mock_fermentation_repo.get_by_id.assert_awaited_once()
        mock_sample_repo.get_latest_sample.assert_awaited_once_with(
            fermentation_id=1
        )
    
    @pytest.mark.asyncio
    async def test_get_latest_sample_with_type_filter(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_sample_repo,
        sample_fermentation,
        sample_entity
    ):
        """Should filter by sample_type when provided."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_sample_repo.get_latest_sample_by_type.return_value = sample_entity
        
        # Act
        result = await sample_service.get_latest_sample(
            fermentation_id=1,
            winery_id=100,
            sample_type=SampleType.SUGAR
        )
        
        # Assert
        assert result == sample_entity
        mock_sample_repo.get_latest_sample_by_type.assert_awaited_once_with(
            fermentation_id=1,
            sample_type=SampleType.SUGAR
        )
    
    @pytest.mark.asyncio
    async def test_get_latest_sample_no_samples(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_sample_repo,
        sample_fermentation
    ):
        """Should return None when no samples exist."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_sample_repo.get_latest_sample.return_value = None
        
        # Act
        result = await sample_service.get_latest_sample(
            fermentation_id=1,
            winery_id=100
        )
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_latest_sample_fermentation_not_found(
        self,
        sample_service,
        mock_fermentation_repo
    ):
        """Should raise NotFoundError when fermentation doesn't exist."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="Fermentation .* not found"):
            await sample_service.get_latest_sample(
                fermentation_id=999,
                winery_id=100
            )
    
    @pytest.mark.asyncio
    async def test_get_latest_sample_repository_error(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_sample_repo,
        sample_fermentation
    ):
        """Should propagate RepositoryError from repository."""
        # Arrange
        from src.modules.fermentation.src.repository_component.errors import RepositoryError
        
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_sample_repo.get_latest_sample.side_effect = RepositoryError("Database error")
        
        # Act & Assert
        with pytest.raises(RepositoryError, match="Database error"):
            await sample_service.get_latest_sample(
                fermentation_id=1,
                winery_id=100
            )


# ==================================================================================
# TEST: get_samples_in_timerange() - Time-based queries
# ==================================================================================

class TestGetSamplesInTimerange:
    """Test get_samples_in_timerange() method - TDD approach."""
    
    @pytest.mark.asyncio
    async def test_get_samples_in_timerange_happy_path(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_sample_repo,
        sample_fermentation,
        sample_entity
    ):
        """Should return samples within timerange."""
        # Arrange
        start = datetime(2025, 10, 1)
        end = datetime(2025, 10, 21)
        samples = [sample_entity]
        
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_sample_repo.get_samples_in_timerange.return_value = samples
        
        # Act
        result = await sample_service.get_samples_in_timerange(
            fermentation_id=1,
            winery_id=100,
            start=start,
            end=end
        )
        
        # Assert
        assert result == samples
        mock_fermentation_repo.get_by_id.assert_awaited_once()
        mock_sample_repo.get_samples_in_timerange.assert_awaited_once_with(
            fermentation_id=1,
            start_time=start,
            end_time=end
        )
    
    @pytest.mark.asyncio
    async def test_get_samples_in_timerange_invalid_range(
        self,
        sample_service
    ):
        """Should raise ValidationError when start >= end."""
        # Arrange
        start = datetime(2025, 10, 21)
        end = datetime(2025, 10, 1)  # Before start
        
        # Act & Assert
        with pytest.raises(ValidationError, match="start.*must be before.*end"):
            await sample_service.get_samples_in_timerange(
                fermentation_id=1,
                winery_id=100,
                start=start,
                end=end
            )
    
    @pytest.mark.asyncio
    async def test_get_samples_in_timerange_fermentation_not_found(
        self,
        sample_service,
        mock_fermentation_repo
    ):
        """Should raise NotFoundError when fermentation doesn't exist."""
        # Arrange
        start = datetime(2025, 10, 1)
        end = datetime(2025, 10, 21)
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="Fermentation .* not found"):
            await sample_service.get_samples_in_timerange(
                fermentation_id=999,
                winery_id=100,
                start=start,
                end=end
            )
    
    @pytest.mark.asyncio
    async def test_get_samples_in_timerange_empty_list(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_sample_repo,
        sample_fermentation
    ):
        """Should return empty list when no samples in range."""
        # Arrange
        start = datetime(2025, 10, 1)
        end = datetime(2025, 10, 21)
        
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_sample_repo.get_samples_in_timerange.return_value = []
        
        # Act
        result = await sample_service.get_samples_in_timerange(
            fermentation_id=1,
            winery_id=100,
            start=start,
            end=end
        )
        
        # Assert
        assert result == []
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_samples_in_timerange_repository_error(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_sample_repo,
        sample_fermentation
    ):
        """Should propagate RepositoryError from repository."""
        # Arrange
        from src.modules.fermentation.src.repository_component.errors import RepositoryError
        
        start = datetime(2025, 10, 1)
        end = datetime(2025, 10, 21)
        
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_sample_repo.get_samples_in_timerange.side_effect = RepositoryError("Database error")
        
        # Act & Assert
        with pytest.raises(RepositoryError, match="Database error"):
            await sample_service.get_samples_in_timerange(
                fermentation_id=1,
                winery_id=100,
                start=start,
                end=end
            )


# ==================================================================================
# TEST: validate_sample_data() - Pre-creation validation
# ==================================================================================

class TestValidateSampleData:
    """Test validate_sample_data() method - TDD approach."""
    
    @pytest.mark.asyncio
    async def test_validate_sample_data_valid(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_validation_orchestrator,
        sample_fermentation,
        sample_create_dto,
        sample_entity,
        valid_validation_result
    ):
        """Should return valid result when sample data is valid."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_validation_orchestrator.validate_sample_complete.return_value = valid_validation_result
        
        # Mock the factory method
        sample_service._create_sample_entity = Mock(return_value=sample_entity)
        
        # Act
        result = await sample_service.validate_sample_data(
            fermentation_id=1,
            winery_id=1,
            data=sample_create_dto
        )
        
        # Assert
        assert result == valid_validation_result
        assert result.is_valid is True
        mock_fermentation_repo.get_by_id.assert_awaited_once()
        mock_validation_orchestrator.validate_sample_complete.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_validate_sample_data_invalid(
        self,
        sample_service,
        mock_fermentation_repo,
        mock_validation_orchestrator,
        sample_fermentation,
        sample_create_dto,
        sample_entity,
        invalid_validation_result
    ):
        """Should return invalid result when sample data is invalid."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = sample_fermentation
        mock_validation_orchestrator.validate_sample_complete.return_value = invalid_validation_result
        
        # Mock the factory method
        sample_service._create_sample_entity = Mock(return_value=sample_entity)
        
        # Act
        result = await sample_service.validate_sample_data(
            fermentation_id=1,
            winery_id=1,
            data=sample_create_dto
        )
        
        # Assert
        assert result == invalid_validation_result
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_validate_sample_data_fermentation_not_found(
        self,
        sample_service,
        mock_fermentation_repo,
        sample_create_dto
    ):
        """Should raise NotFoundError when fermentation doesn't exist."""
        # Arrange
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError, match="Fermentation .* not found"):
            await sample_service.validate_sample_data(
                fermentation_id=999,
                winery_id=1,
                data=sample_create_dto
            )
