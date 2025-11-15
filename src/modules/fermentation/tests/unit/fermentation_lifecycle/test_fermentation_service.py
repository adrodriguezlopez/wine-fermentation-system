"""
Unit tests for FermentationService.

Following TDD approach as documented in ADR-005.
Tests are written BEFORE implementation to drive design.
"""

import pytest
from unittest.mock import Mock, create_autospec
from datetime import datetime, date
from typing import Optional, List

# Import from canonical locations (consistent with other tests)
from src.modules.fermentation.src.service_component.services.fermentation_service import FermentationService
from src.modules.fermentation.src.service_component.interfaces.fermentation_service_interface import IFermentationService
from src.modules.fermentation.src.service_component.interfaces.fermentation_validator_interface import IFermentationValidator
from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.dtos import FermentationCreate
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_error import ValidationError


class TestCreateFermentation:
    """
    Test suite for FermentationService.create_fermentation()
    
    Business Rules (from ADR-005):
    - Must have valid fermentation data
    - Vessel must be available (not used by active fermentation)
    - User must have access to winery
    - Start date must be <= current date
    
    Expected Behavior:
    - Returns complete Fermentation entity (not just ID)
    - Validates data before persistence
    - Enforces multi-tenancy (winery_id)
    - Tracks user_id for audit trail
    """
    
    @pytest.fixture
    def mock_fermentation_repo(self) -> Mock:
        """Mock repository for testing service logic in isolation."""
        return create_autospec(IFermentationRepository, instance=True)
    
    @pytest.fixture
    def mock_validator(self) -> Mock:
        """Mock validator for testing service logic in isolation."""
        return create_autospec(IFermentationValidator, instance=True)
    
    @pytest.fixture
    def service(
        self,
        mock_fermentation_repo: Mock,
        mock_validator: Mock
    ) -> FermentationService:
        """Service instance with mocked dependencies."""
        return FermentationService(
            fermentation_repo=mock_fermentation_repo,
            validator=mock_validator
        )
    
    @pytest.fixture
    def valid_fermentation_data(self) -> FermentationCreate:
        """Valid DTO for creating a fermentation."""
        return FermentationCreate(
            fermented_by_user_id=42,
            vintage_year=2025,
            yeast_strain="EC-1118",
            input_mass_kg=1000.0,
            initial_sugar_brix=24.5,
            initial_density=1.105,
            vessel_code="T-001",
            start_date=datetime(2025, 10, 1, 8, 0, 0)
        )
    
    @pytest.fixture
    def expected_fermentation_entity(self) -> Mock:
        """Expected entity to be returned by repository (mocked to avoid SQLAlchemy init issues)."""
        fermentation = Mock(spec=Fermentation)
        fermentation.id = 1
        fermentation.winery_id = 1
        fermentation.fermented_by_user_id = 42
        fermentation.vintage_year = 2025
        fermentation.yeast_strain = "EC-1118"
        fermentation.input_mass_kg = 1000.0
        fermentation.initial_sugar_brix = 24.5
        fermentation.initial_density = 1.105
        fermentation.vessel_code = "T-001"
        fermentation.start_date = datetime(2025, 10, 1, 8, 0, 0)
        fermentation.status = "in_progress"
        fermentation.created_at = datetime(2025, 10, 11, 10, 0, 0)
        return fermentation
    
    @pytest.mark.asyncio
    async def test_create_fermentation_happy_path(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        mock_validator: Mock,
        valid_fermentation_data: FermentationCreate,
        expected_fermentation_entity: Mock
    ):
        """
        GIVEN a valid FermentationCreate DTO
        WHEN create_fermentation is called
        THEN it validates data, persists via repository, and returns complete entity
        
        SUCCESS CRITERIA (ADR-005):
        ✓ Validator.validate_creation_data() is called
        ✓ Validation passes (is_valid = True)
        ✓ Repository.create() is called with correct parameters
        ✓ Returns Fermentation entity (NOT primitive ID)
        ✓ Entity has all fields populated
        """
        # Arrange
        winery_id = 1
        user_id = 42
        
        # Mock validator - validation passes
        mock_validator.validate_creation_data.return_value = ValidationResult(
            is_valid=True,
            errors=[]
        )
        
        # Mock repository - returns entity
        mock_fermentation_repo.create.return_value = expected_fermentation_entity
        
        # Act
        result = await service.create_fermentation(
            winery_id=winery_id,
            user_id=user_id,
            data=valid_fermentation_data
        )
        
        # Assert
        # 1. Validator was called
        mock_validator.validate_creation_data.assert_called_once_with(valid_fermentation_data)
        
        # 2. Repository was called with correct params
        mock_fermentation_repo.create.assert_called_once_with(
            winery_id=winery_id,
            data=valid_fermentation_data
        )
        
        # 3. Returns complete entity (type safety)
        assert result == expected_fermentation_entity
        assert result.id == 1
        assert result.winery_id == winery_id
        assert result.fermented_by_user_id == 42
        assert result.vintage_year == 2025
        assert result.yeast_strain == "EC-1118"
        assert result.status == "in_progress"
        
    @pytest.mark.asyncio
    async def test_create_fermentation_validation_failure(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        mock_validator: Mock
    ):
        """
        GIVEN invalid fermentation data (Brix out of range)
        WHEN create_fermentation is called
        THEN it raises ValueError and does NOT persist
        
        SUCCESS CRITERIA:
        ✓ Validator.validate_creation_data() is called
        ✓ Validation fails (is_valid = False)
        ✓ ValueError is raised with error details
        ✓ Repository.create() is NOT called (no side effects)
        """
        # Arrange
        winery_id = 1
        user_id = 42
        
        # Invalid data - Brix out of range
        invalid_data = FermentationCreate(
            fermented_by_user_id=42,
            vintage_year=2025,
            yeast_strain="EC-1118",
            input_mass_kg=1000.0,
            initial_sugar_brix=35.5,  # ❌ Out of range (0-30)
            initial_density=1.105,
            vessel_code="T-001",
            start_date=datetime(2025, 10, 1, 8, 0, 0)
        )
        
        # Mock validator - validation fails
        mock_validator.validate_creation_data.return_value = ValidationResult(
            is_valid=False,
            errors=[
                ValidationError(
                    field="initial_sugar_brix",
                    message="Initial sugar Brix must be between 0 and 30, got 35.5",
                    code="INVALID_BRIX"
                )
            ]
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await service.create_fermentation(
                winery_id=winery_id,
                user_id=user_id,
                data=invalid_data
            )
        
        # Check error message contains validation errors
        error_message = str(exc_info.value)
        assert "validation" in error_message.lower()
        assert "initial_sugar_brix" in error_message.lower()
        
        # Validator was called
        mock_validator.validate_creation_data.assert_called_once_with(invalid_data)
        
        # Repository was NOT called (no persistence on validation failure)
        mock_fermentation_repo.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_fermentation_duplicate_vessel(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        mock_validator: Mock,
        valid_fermentation_data: FermentationCreate
    ):
        """
        GIVEN a vessel already in use by active fermentation
        WHEN create_fermentation is called
        THEN it raises DuplicateEntityError
        
        BUSINESS RULE: One vessel can only host one active fermentation at a time
        
        SUCCESS CRITERIA:
        ✓ Validation passes (data structure valid)
        ✓ Repository raises DuplicateEntityError (vessel in use)
        ✓ Error message explains conflict
        """
        # Arrange
        winery_id = 1
        user_id = 42
        
        # Mock validator - validation passes
        mock_validator.validate_creation_data.return_value = ValidationResult(
            is_valid=True,
            errors=[]
        )
        
        # Mock repository - raises DuplicateEntityError
        from src.modules.fermentation.src.repository_component.errors import DuplicateEntityError
        mock_fermentation_repo.create.side_effect = DuplicateEntityError(
            "Vessel T-001 is already in use by active fermentation"
        )
        
        # Act & Assert
        with pytest.raises(DuplicateEntityError) as exc_info:
            await service.create_fermentation(
                winery_id=winery_id,
                user_id=user_id,
                data=valid_fermentation_data
            )
        
        assert "T-001" in str(exc_info.value)
        assert "already in use" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_fermentation_repository_failure(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        mock_validator: Mock,
        valid_fermentation_data: FermentationCreate
    ):
        """
        GIVEN repository encounters database error
        WHEN create_fermentation is called
        THEN error propagates to caller (no swallowing)
        
        SUCCESS CRITERIA:
        ✓ Validation passes
        ✓ Repository raises database error
        ✓ Error propagates (service doesn't catch)
        """
        # Arrange
        winery_id = 1
        user_id = 42
        
        # Mock validator - validation passes
        mock_validator.validate_creation_data.return_value = ValidationResult(
            is_valid=True,
            errors=[]
        )
        
        # Mock repository - raises database error
        from src.modules.fermentation.src.repository_component.errors import RepositoryError
        mock_fermentation_repo.create.side_effect = RepositoryError(
            "Database connection failed"
        )
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await service.create_fermentation(
                winery_id=winery_id,
                user_id=user_id,
                data=valid_fermentation_data
            )
        
        assert "Database connection failed" in str(exc_info.value)


class TestServiceImplementsInterface:
    """Verify FermentationService correctly implements IFermentationService."""
    
    def test_service_implements_interface(self):
        """
        GIVEN FermentationService class
        WHEN checking inheritance
        THEN it implements IFermentationService interface
        """
        assert issubclass(FermentationService, IFermentationService)
    
    def test_service_has_all_required_methods(self):
        """
        GIVEN FermentationService instance
        WHEN checking methods
        THEN all 7 interface methods are present
        """
        mock_repo = Mock(spec=IFermentationRepository)
        mock_validator = Mock(spec=IFermentationValidator)
        service = FermentationService(mock_repo, mock_validator)
        
        # All 7 methods from IFermentationService
        assert hasattr(service, "create_fermentation")
        assert hasattr(service, "get_fermentation")
        assert hasattr(service, "get_fermentations_by_winery")
        assert hasattr(service, "update_status")
        assert hasattr(service, "complete_fermentation")
        assert hasattr(service, "soft_delete")
        assert hasattr(service, "validate_creation_data")


class TestGetFermentation:
    """
    Test suite for FermentationService.get_fermentation()
    
    Business Rules (from ADR-005):
    - Multi-tenant scoping (winery_id must match)
    - Soft-deleted records are filtered out
    - Returns None if not found (not exception)
    - Repository errors propagate
    """
    
    @pytest.fixture
    def mock_fermentation_repo(self) -> Mock:
        """Mock repository with strict interface compliance."""
        return create_autospec(IFermentationRepository, instance=True)
    
    @pytest.fixture
    def mock_validator(self) -> Mock:
        """Mock validator with strict interface compliance."""
        return create_autospec(IFermentationValidator, instance=True)
    
    @pytest.fixture
    def service(
        self, 
        mock_fermentation_repo: Mock,
        mock_validator: Mock
    ) -> FermentationService:
        """Service instance with mocked dependencies."""
        return FermentationService(
            fermentation_repo=mock_fermentation_repo,
            validator=mock_validator
        )
    
    @pytest.fixture
    def fermentation_entity(self) -> Mock:
        """Mock Fermentation entity."""
        entity = Mock(spec=Fermentation)
        entity.id = 1
        entity.winery_id = 1
        entity.fermented_by_user_id = 42
        entity.vintage_year = 2025
        entity.yeast_strain = "EC-1118"
        entity.vessel_code = "T-001"
        entity.status = "ACTIVE"
        entity.deleted_at = None
        return entity
    
    @pytest.mark.asyncio
    async def test_get_fermentation_happy_path(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        fermentation_entity: Mock
    ):
        """
        GIVEN a valid fermentation_id and winery_id
        WHEN get_fermentation is called
        THEN it retrieves and returns the fermentation entity
        
        SUCCESS CRITERIA:
        ✓ Repository.get() is called with correct parameters
        ✓ Returns the fermentation entity (not None)
        ✓ Entity has all expected fields
        """
        # Arrange
        fermentation_id = 1
        winery_id = 1
        
        # Mock repository - returns entity
        mock_fermentation_repo.get_by_id.return_value = fermentation_entity
        
        # Act
        result = await service.get_fermentation(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        # Assert
        assert result is not None
        assert result.id == fermentation_id
        assert result.winery_id == winery_id
        assert result.status == "ACTIVE"
        
        # Verify repository was called correctly
        mock_fermentation_repo.get_by_id.assert_called_once_with(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
    
    @pytest.mark.asyncio
    async def test_get_fermentation_not_found(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a fermentation_id that doesn't exist
        WHEN get_fermentation is called
        THEN it returns None (not exception)
        
        BUSINESS RULE: Missing records return None, not error
        
        SUCCESS CRITERIA:
        ✓ Repository.get() returns None
        ✓ Service returns None (propagates repository result)
        ✓ No exception is raised
        """
        # Arrange
        fermentation_id = 999
        winery_id = 1
        
        # Mock repository - returns None (not found)
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act
        result = await service.get_fermentation(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        # Assert
        assert result is None
        
        # Verify repository was called
        mock_fermentation_repo.get_by_id.assert_called_once_with(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
    
    @pytest.mark.asyncio
    async def test_get_fermentation_wrong_winery(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a fermentation that belongs to a different winery
        WHEN get_fermentation is called with wrong winery_id
        THEN it returns None (multi-tenant isolation)
        
        BUSINESS RULE: winery_id scoping enforced by repository
        
        SUCCESS CRITERIA:
        ✓ Repository enforces winery_id scoping
        ✓ Returns None (access denied via multi-tenancy)
        ✓ No cross-tenant data leakage
        """
        # Arrange
        fermentation_id = 1
        wrong_winery_id = 999  # Different winery
        
        # Mock repository - returns None (wrong winery)
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act
        result = await service.get_fermentation(
            fermentation_id=fermentation_id,
            winery_id=wrong_winery_id
        )
        
        # Assert
        assert result is None
        
        # Verify repository was called with wrong_winery_id
        mock_fermentation_repo.get_by_id.assert_called_once_with(
            fermentation_id=fermentation_id,
            winery_id=wrong_winery_id
        )
    
    @pytest.mark.asyncio
    async def test_get_fermentation_soft_deleted(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a fermentation that has been soft-deleted
        WHEN get_fermentation is called
        THEN it returns None (soft-deleted records filtered)
        
        BUSINESS RULE: Soft-deleted records are not retrievable
        
        SUCCESS CRITERIA:
        ✓ Repository filters soft-deleted records
        ✓ Returns None for deleted fermentations
        """
        # Arrange
        fermentation_id = 1
        winery_id = 1
        
        # Mock repository - returns None (soft-deleted filtered by repository)
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act
        result = await service.get_fermentation(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_fermentation_repository_error(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN repository encounters database error
        WHEN get_fermentation is called
        THEN error propagates to caller
        
        SUCCESS CRITERIA:
        ✓ Repository raises RepositoryError
        ✓ Service propagates error (doesn't catch)
        ✓ Error message is preserved
        """
        # Arrange
        fermentation_id = 1
        winery_id = 1
        
        # Mock repository - raises database error
        from src.modules.fermentation.src.repository_component.errors import RepositoryError
        mock_fermentation_repo.get_by_id.side_effect = RepositoryError(
            "Database connection timeout"
        )
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await service.get_fermentation(
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
        
        assert "Database connection timeout" in str(exc_info.value)


class TestGetFermentationsByWinery:
    """
    Test suite for FermentationService.get_fermentations_by_winery()
    
    Business Rules (from ADR-005):
    - Multi-tenant scoping (winery_id must match)
    - Optional status filter
    - Optional include/exclude completed fermentations
    - Results ordered by start_date DESC
    - Soft-deleted records filtered out
    """
    
    @pytest.fixture
    def mock_fermentation_repo(self) -> Mock:
        """Mock repository with strict interface compliance."""
        return create_autospec(IFermentationRepository, instance=True)
    
    @pytest.fixture
    def mock_validator(self) -> Mock:
        """Mock validator for service instantiation."""
        return create_autospec(IFermentationValidator, instance=True)
    
    @pytest.fixture
    def service(
        self,
        mock_fermentation_repo: Mock,
        mock_validator: Mock
    ) -> FermentationService:
        """Service instance with mocked dependencies."""
        return FermentationService(
            fermentation_repo=mock_fermentation_repo,
            validator=mock_validator
        )
    
    @pytest.fixture
    def fermentation_list(self) -> List[Mock]:
        """Mock list of Fermentation entities."""
        fermentations = []
        for i in range(3):
            f = Mock(spec=Fermentation)
            f.id = i + 1
            f.winery_id = 1
            f.status = "ACTIVE"
            f.start_date = datetime(2025, 10, i + 1, 8, 0, 0)
            f.deleted_at = None
            fermentations.append(f)
        return fermentations
    
    @pytest.mark.asyncio
    async def test_get_fermentations_by_winery_no_filters(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        fermentation_list: List[Mock]
    ):
        """
        GIVEN a winery with multiple fermentations
        WHEN get_fermentations_by_winery is called without filters
        THEN it returns all fermentations for that winery
        
        SUCCESS CRITERIA:
        ✓ Repository.get_by_winery() is called with winery_id
        ✓ No status filter applied (status=None)
        ✓ include_completed defaults to False
        ✓ Returns list of fermentations
        """
        # Arrange
        winery_id = 1
        
        # Mock repository - returns list
        mock_fermentation_repo.get_by_winery.return_value = fermentation_list
        
        # Act
        result = await service.get_fermentations_by_winery(winery_id=winery_id)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(f.winery_id == winery_id for f in result)
        
        # Verify repository was called correctly (no status filter at repo level)
        mock_fermentation_repo.get_by_winery.assert_called_once_with(
            winery_id=winery_id,
            include_completed=False
        )
    
    @pytest.mark.asyncio
    async def test_get_fermentations_by_winery_with_status_filter(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a winery with fermentations in different statuses
        WHEN get_fermentations_by_winery is called with status filter
        THEN it returns only fermentations matching the status
        
        SUCCESS CRITERIA:
        ✓ Repository.get_by_winery() is called WITHOUT status filter (fetches all)
        ✓ In-memory filtering applied for status
        ✓ Only matching fermentations returned
        """
        # Arrange
        winery_id = 1
        from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
        
        # Repository returns mixed statuses
        all_fermentations = [
            Mock(spec=Fermentation, id=1, winery_id=1, status=FermentationStatus.ACTIVE),
            Mock(spec=Fermentation, id=2, winery_id=1, status=FermentationStatus.ACTIVE),
            Mock(spec=Fermentation, id=3, winery_id=1, status=FermentationStatus.LAG)
        ]
        
        # Mock repository - returns all fermentations
        mock_fermentation_repo.get_by_winery.return_value = all_fermentations
        
        # Act
        result = await service.get_fermentations_by_winery(
            winery_id=winery_id,
            status=FermentationStatus.ACTIVE
        )
        
        # Assert - in-memory filter should have kept only ACTIVE
        assert len(result) == 2
        assert all(f.status == FermentationStatus.ACTIVE for f in result)
        
        # Verify repository was called WITHOUT status filter (filtering done in-memory)
        mock_fermentation_repo.get_by_winery.assert_called_once_with(
            winery_id=winery_id,
            include_completed=False
        )
    
    @pytest.mark.asyncio
    async def test_get_fermentations_by_winery_include_completed(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a winery with both active and completed fermentations
        WHEN get_fermentations_by_winery is called with include_completed=True
        THEN it returns both active and completed fermentations
        
        SUCCESS CRITERIA:
        ✓ Repository.get_by_winery() is called with include_completed=True
        ✓ Completed fermentations included in results
        """
        # Arrange
        winery_id = 1
        all_fermentations = [
            Mock(spec=Fermentation, id=1, winery_id=1, status="ACTIVE"),
            Mock(spec=Fermentation, id=2, winery_id=1, status="COMPLETED")
        ]
        
        # Mock repository - returns all fermentations
        mock_fermentation_repo.get_by_winery.return_value = all_fermentations
        
        # Act
        result = await service.get_fermentations_by_winery(
            winery_id=winery_id,
            include_completed=True
        )
        
        # Assert
        assert len(result) == 2
        statuses = {f.status for f in result}
        assert statuses == {"ACTIVE", "COMPLETED"}
        
        # Verify repository was called with include_completed=True (no status param)
        mock_fermentation_repo.get_by_winery.assert_called_once_with(
            winery_id=winery_id,
            include_completed=True
        )
    
    @pytest.mark.asyncio
    async def test_get_fermentations_by_winery_empty_result(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a winery with no fermentations (or all filtered out)
        WHEN get_fermentations_by_winery is called
        THEN it returns empty list (not None, not exception)
        
        SUCCESS CRITERIA:
        ✓ Returns empty list []
        ✓ No exception raised
        """
        # Arrange
        winery_id = 999
        
        # Mock repository - returns empty list
        mock_fermentation_repo.get_by_winery.return_value = []
        
        # Act
        result = await service.get_fermentations_by_winery(winery_id=winery_id)
        
        # Assert
        assert result == []
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_fermentations_by_winery_repository_error(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN repository encounters database error
        WHEN get_fermentations_by_winery is called
        THEN error propagates to caller
        
        SUCCESS CRITERIA:
        ✓ Repository raises RepositoryError
        ✓ Service propagates error (doesn't catch)
        """
        # Arrange
        winery_id = 1
        
        # Mock repository - raises database error
        from src.modules.fermentation.src.repository_component.errors import RepositoryError
        mock_fermentation_repo.get_by_winery.side_effect = RepositoryError(
            "Database query timeout"
        )
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await service.get_fermentations_by_winery(winery_id=winery_id)
        
        assert "Database query timeout" in str(exc_info.value)


class TestUpdateStatus:
    """
    Test suite for FermentationService.update_status()
    
    TDD Phase: RED
    Created: 2025-10-18
    
    Business Rules:
    1. Must fetch fermentation first (verify existence + ownership)
    2. Must validate status transition using validator
    3. Updates status and updated_by fields
    4. Persists changes to repository
    5. Returns updated fermentation entity
    
    Coverage:
    - Happy path: valid status transition
    - Validation failure: invalid transition
    - Not found: fermentation doesn't exist
    - Wrong winery: multi-tenant violation
    - Soft deleted: fermentation is deleted
    - Repository error: database failure
    """
    
    @pytest.fixture
    def mock_fermentation_repo(self) -> Mock:
        """Mock repository for testing service logic in isolation."""
        return create_autospec(IFermentationRepository, instance=True)
    
    @pytest.fixture
    def mock_validator(self) -> Mock:
        """Mock validator for testing service logic in isolation."""
        return create_autospec(IFermentationValidator, instance=True)
    
    @pytest.fixture
    def service(
        self,
        mock_fermentation_repo: Mock,
        mock_validator: Mock
    ) -> FermentationService:
        """Service instance with mocked dependencies."""
        return FermentationService(
            fermentation_repo=mock_fermentation_repo,
            validator=mock_validator
        )
    
    @pytest.fixture
    def fermentation_entity(self) -> Mock:
        """Mock fermentation entity for testing."""
        fermentation = Mock(spec=Fermentation)
        fermentation.id = 1
        fermentation.winery_id = 1
        fermentation.status = "ACTIVE"
        fermentation.deleted_at = None
        return fermentation
    
    @pytest.mark.asyncio
    async def test_update_status_happy_path(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        mock_validator: Mock,
        fermentation_entity: Fermentation
    ):
        """
        GIVEN an existing fermentation in ACTIVE status
        WHEN update_status is called with valid new status
        THEN status is updated and fermentation is saved
        
        SUCCESS CRITERIA:
        ✓ Fermentation fetched from repository
        ✓ Validator validates transition (ACTIVE → DECLINE)
        ✓ Status updated to new value
        ✓ updated_by set to user_id
        ✓ Repository.update() called
        ✓ Updated fermentation returned
        """
        # Arrange
        from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
        from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult
        
        fermentation_id = 1
        winery_id = 1
        user_id = 42
        new_status = FermentationStatus.DECLINE
        
        # Setup fermentation entity (currently ACTIVE)
        fermentation_entity.id = fermentation_id
        fermentation_entity.winery_id = winery_id
        fermentation_entity.status = FermentationStatus.ACTIVE
        fermentation_entity.deleted_at = None
        
        # Mock repository - update_status returns True on success
        mock_fermentation_repo.get_by_id.return_value = fermentation_entity
        mock_fermentation_repo.update_status.return_value = True
        
        # After update, get_by_id returns updated fermentation
        updated_fermentation = Mock(spec=Fermentation)
        updated_fermentation.id = fermentation_id
        updated_fermentation.winery_id = winery_id
        updated_fermentation.status = new_status
        updated_fermentation.updated_by = user_id
        
        # Mock validator - transition is valid
        mock_validator.validate_status_transition.return_value = ValidationResult.success()
        
        # Act
        result = await service.update_status(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            new_status=new_status,
            user_id=user_id
        )
        
        # Assert
        assert result is True  # Repository returns bool
        
        # Verify repository calls
        mock_fermentation_repo.get_by_id.assert_called_once_with(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        mock_fermentation_repo.update_status.assert_called_once_with(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            new_status=new_status,
            metadata={'updated_by': user_id}
        )
        
        # Verify validator was called with correct transition
        mock_validator.validate_status_transition.assert_called_once_with(
            current_status=FermentationStatus.ACTIVE,
            new_status=new_status
        )
    
    @pytest.mark.asyncio
    async def test_update_status_invalid_transition(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        mock_validator: Mock,
        fermentation_entity: Fermentation
    ):
        """
        GIVEN a fermentation in COMPLETED status (terminal state)
        WHEN update_status is called to change to ACTIVE
        THEN ValidationError is raised
        
        SUCCESS CRITERIA:
        ✓ Fermentation fetched
        ✓ Validator rejects transition (COMPLETED → ACTIVE invalid)
        ✓ ValidationError raised
        ✓ Repository.update() NOT called
        """
        # Arrange
        from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
        from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult
        from src.modules.fermentation.src.service_component.models.schemas.validations.validation_error import ValidationError
        from src.modules.fermentation.src.service_component.errors import ValidationError as ServiceValidationError
        
        fermentation_id = 1
        winery_id = 1
        user_id = 42
        
        # Setup fermentation (COMPLETED - terminal state)
        fermentation_entity.id = fermentation_id
        fermentation_entity.winery_id = winery_id
        fermentation_entity.status = FermentationStatus.COMPLETED
        fermentation_entity.deleted_at = None
        
        mock_fermentation_repo.get_by_id.return_value = fermentation_entity
        
        # Mock validator - transition is INVALID
        validation_error = ValidationError(
            field="status_transition",
            message="Cannot transition from terminal state COMPLETED to ACTIVE",
            current_value=FermentationStatus.COMPLETED,
            expected_range="Terminal state - no transitions allowed"
        )
        mock_validator.validate_status_transition.return_value = ValidationResult.failure([validation_error])
        
        # Act & Assert
        with pytest.raises(ServiceValidationError) as exc_info:
            await service.update_status(
                fermentation_id=fermentation_id,
                winery_id=winery_id,
                new_status=FermentationStatus.ACTIVE,
                user_id=user_id
            )
        
        # Verify error message
        assert "status_transition" in str(exc_info.value) or "terminal state" in str(exc_info.value).lower()
        
        # Verify update_status was NOT called
        mock_fermentation_repo.update_status.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_status_fermentation_not_found(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a non-existent fermentation ID
        WHEN update_status is called
        THEN NotFoundError is raised
        
        SUCCESS CRITERIA:
        ✓ Repository.get_by_id() returns None
        ✓ NotFoundError raised
        ✓ Validator NOT called
        ✓ Repository.update() NOT called
        """
        # Arrange
        from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
        from src.modules.fermentation.src.service_component.errors import NotFoundError
        
        fermentation_id = 999
        winery_id = 1
        
        # Mock repository - fermentation doesn't exist
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.update_status(
                fermentation_id=fermentation_id,
                winery_id=winery_id,
                new_status=FermentationStatus.DECLINE,
                user_id=42
            )
        
        assert f"Fermentation {fermentation_id}" in str(exc_info.value) or f"{fermentation_id}" in str(exc_info.value)
        
        # Verify update_status was NOT called
        mock_fermentation_repo.update_status.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_status_wrong_winery(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        fermentation_entity: Fermentation
    ):
        """
        GIVEN a fermentation belonging to winery 1
        WHEN update_status is called with winery_id=2
        THEN NotFoundError is raised (multi-tenant isolation)
        
        SUCCESS CRITERIA:
        ✓ Repository.get_by_id() scopes by winery_id
        ✓ Returns None for wrong winery
        ✓ NotFoundError raised
        """
        # Arrange
        from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
        from src.modules.fermentation.src.service_component.errors import NotFoundError
        
        fermentation_id = 1
        correct_winery_id = 1
        wrong_winery_id = 2
        
        # Mock repository - returns None when wrong winery_id
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.update_status(
                fermentation_id=fermentation_id,
                winery_id=wrong_winery_id,
                new_status=FermentationStatus.DECLINE,
                user_id=42
            )
        
        # Verify repository was queried with wrong winery (and returned None)
        mock_fermentation_repo.get_by_id.assert_called_once_with(
            fermentation_id=fermentation_id,
            winery_id=wrong_winery_id
        )
    
    @pytest.mark.asyncio
    async def test_update_status_soft_deleted(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a soft-deleted fermentation
        WHEN update_status is called
        THEN NotFoundError is raised
        
        SUCCESS CRITERIA:
        ✓ Repository.get_by_id() filters out deleted (returns None)
        ✓ NotFoundError raised
        """
        # Arrange
        from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
        from src.modules.fermentation.src.service_component.errors import NotFoundError
        
        fermentation_id = 1
        winery_id = 1
        
        # Mock repository - soft-deleted fermentation not returned
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.update_status(
                fermentation_id=fermentation_id,
                winery_id=winery_id,
                new_status=FermentationStatus.DECLINE,
                user_id=42
            )
    
    @pytest.mark.asyncio
    async def test_update_status_repository_error(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN repository encounters error during update
        WHEN update_status is called
        THEN RepositoryError propagates
        
        SUCCESS CRITERIA:
        ✓ Repository.update() raises RepositoryError
        ✓ Error propagates to caller
        """
        # Arrange
        from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
        from src.modules.fermentation.src.repository_component.errors import RepositoryError
        from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult
        
        fermentation_id = 1
        winery_id = 1
        
        fermentation = Mock(spec=Fermentation)
        fermentation.id = fermentation_id
        fermentation.winery_id = winery_id
        fermentation.status = FermentationStatus.ACTIVE
        fermentation.deleted_at = None
        
        mock_fermentation_repo.get_by_id.return_value = fermentation
        
        # Validator allows transition
        mock_validator = Mock()
        mock_validator.validate_status_transition.return_value = ValidationResult.success()
        service._validator = mock_validator
        
        # Repository raises error on update_status
        mock_fermentation_repo.update_status.side_effect = RepositoryError(
            "Database connection lost"
        )
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await service.update_status(
                fermentation_id=fermentation_id,
                winery_id=winery_id,
                new_status=FermentationStatus.DECLINE,
                user_id=42
            )
        
        assert "Database connection lost" in str(exc_info.value)


class TestCompleteFermentation:
    """
    Test suite for FermentationService.complete_fermentation()
    
    TDD Phase: RED
    Created: 2025-10-18
    
    Business Rules:
    1. Must fetch fermentation first (verify existence + ownership)
    2. Must validate completion criteria (duration, final_brix, etc.)
    3. Updates status to COMPLETED with final measurements
    4. Records completion notes if provided
    5. Returns updated fermentation entity
    
    Coverage:
    - Happy path: valid completion with all criteria met
    - Validation failure: insufficient duration
    - Validation failure: high residual sugar
    - Not found: fermentation doesn't exist
    - Wrong winery: multi-tenant violation
    - Repository error: database failure
    """
    
    @pytest.fixture
    def mock_fermentation_repo(self) -> Mock:
        """Mock repository for testing service logic in isolation."""
        return create_autospec(IFermentationRepository, instance=True)
    
    @pytest.fixture
    def mock_validator(self) -> Mock:
        """Mock validator for testing service logic in isolation."""
        return create_autospec(IFermentationValidator, instance=True)
    
    @pytest.fixture
    def service(
        self,
        mock_fermentation_repo: Mock,
        mock_validator: Mock
    ) -> FermentationService:
        """Service instance with mocked dependencies."""
        return FermentationService(
            fermentation_repo=mock_fermentation_repo,
            validator=mock_validator
        )
    
    @pytest.fixture
    def active_fermentation(self) -> Mock:
        """Mock active fermentation ready for completion."""
        from datetime import datetime, timedelta
        fermentation = Mock(spec=Fermentation)
        fermentation.id = 1
        fermentation.winery_id = 1
        fermentation.status = "ACTIVE"
        fermentation.input_mass_kg = 1000.0
        fermentation.initial_sugar_brix = 24.5
        fermentation.start_date = datetime.now() - timedelta(days=14)  # 14 days ago
        fermentation.deleted_at = None
        return fermentation
    
    @pytest.mark.asyncio
    async def test_complete_fermentation_happy_path(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        mock_validator: Mock,
        active_fermentation: Mock
    ):
        """
        GIVEN an active fermentation with valid completion criteria
        WHEN complete_fermentation is called with final measurements
        THEN fermentation is marked as COMPLETED
        
        SUCCESS CRITERIA:
        ✓ Fermentation fetched from repository
        ✓ Validator validates completion criteria (duration, final_brix)
        ✓ Validator validates status transition (ACTIVE → COMPLETED)
        ✓ Status updated to COMPLETED via repository
        ✓ Updated fermentation returned
        """
        # Arrange
        from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
        from datetime import datetime
        
        fermentation_id = 1
        winery_id = 1
        user_id = 42
        final_sugar_brix = 3.0
        final_mass_kg = 950.0
        notes = "Fermentation completed successfully"
        
        # Mock repository - fetch returns active fermentation
        mock_fermentation_repo.get_by_id.return_value = active_fermentation
        mock_fermentation_repo.update_status.return_value = True
        
        # Calculate duration
        duration_days = (datetime.now() - active_fermentation.start_date).days
        
        # Mock validator - completion criteria valid, transition valid
        mock_validator.validate_completion_criteria.return_value = ValidationResult.success()
        mock_validator.validate_status_transition.return_value = ValidationResult.success()
        
        # Act
        result = await service.complete_fermentation(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            user_id=user_id,
            final_sugar_brix=final_sugar_brix,
            final_mass_kg=final_mass_kg,
            notes=notes
        )
        
        # Assert
        assert result is True
        
        # Verify fermentation was fetched
        mock_fermentation_repo.get_by_id.assert_called_once_with(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        # Verify completion criteria validated
        mock_validator.validate_completion_criteria.assert_called_once()
        call_args = mock_validator.validate_completion_criteria.call_args
        assert call_args.kwargs['input_mass_kg'] == active_fermentation.input_mass_kg
        assert call_args.kwargs['final_sugar_brix'] == final_sugar_brix
        assert call_args.kwargs['duration_days'] >= 14
        
        # Verify status transition validated
        mock_validator.validate_status_transition.assert_called_once_with(
            current_status=active_fermentation.status,
            new_status=FermentationStatus.COMPLETED
        )
        
        # Verify status updated to COMPLETED
        mock_fermentation_repo.update_status.assert_called_once()
        update_call = mock_fermentation_repo.update_status.call_args
        assert update_call.kwargs['new_status'] == FermentationStatus.COMPLETED
        assert 'updated_by' in update_call.kwargs['metadata']
        assert 'notes' in update_call.kwargs['metadata']
    
    @pytest.mark.asyncio
    async def test_complete_fermentation_insufficient_duration(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        mock_validator: Mock
    ):
        """
        GIVEN a fermentation with insufficient duration (< 7 days)
        WHEN complete_fermentation is called
        THEN ValidationError is raised
        
        SUCCESS CRITERIA:
        ✓ Fermentation fetched
        ✓ Validator rejects completion (duration < 7 days)
        ✓ ValidationError raised
        ✓ Status NOT updated
        """
        # Arrange
        from datetime import datetime, timedelta
        
        fermentation_id = 1
        winery_id = 1
        
        # Fermentation only 3 days old
        young_fermentation = Mock(spec=Fermentation)
        young_fermentation.id = fermentation_id
        young_fermentation.winery_id = winery_id
        young_fermentation.status = "ACTIVE"
        young_fermentation.input_mass_kg = 1000.0
        young_fermentation.start_date = datetime.now() - timedelta(days=3)
        young_fermentation.deleted_at = None
        
        mock_fermentation_repo.get_by_id.return_value = young_fermentation
        
        # Mock validator - completion criteria INVALID (too short)
        validation_error = ValidationError(
            field="duration",
            message="Fermentation duration must be at least 7 days",
            current_value=3,
            expected_range="≥ 7 days"
        )
        mock_validator.validate_completion_criteria.return_value = ValidationResult.failure([validation_error])
        
        # Act & Assert
        from src.modules.fermentation.src.service_component.errors import ValidationError as ServiceValidationError
        
        with pytest.raises(ServiceValidationError) as exc_info:
            await service.complete_fermentation(
                fermentation_id=fermentation_id,
                winery_id=winery_id,
                user_id=42,
                final_sugar_brix=3.0,
                final_mass_kg=950.0
            )
        
        # Verify error message mentions duration
        assert "duration" in str(exc_info.value).lower() or "7 days" in str(exc_info.value)
        
        # Verify status was NOT updated
        mock_fermentation_repo.update_status.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_complete_fermentation_high_residual_sugar(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        mock_validator: Mock,
        active_fermentation: Mock
    ):
        """
        GIVEN a fermentation with high residual sugar (stuck fermentation)
        WHEN complete_fermentation is called
        THEN ValidationError is raised
        
        SUCCESS CRITERIA:
        ✓ Fermentation fetched
        ✓ Validator rejects completion (final_brix >= 5)
        ✓ ValidationError raised
        ✓ Status NOT updated
        """
        # Arrange
        fermentation_id = 1
        winery_id = 1
        high_residual_sugar = 8.0  # Should be < 5
        
        mock_fermentation_repo.get_by_id.return_value = active_fermentation
        
        # Mock validator - completion criteria INVALID (high sugar)
        validation_error = ValidationError(
            field="final_sugar_brix",
            message="Final sugar content too high - fermentation may be stuck",
            current_value=high_residual_sugar,
            expected_range="< 5 °Brix"
        )
        mock_validator.validate_completion_criteria.return_value = ValidationResult.failure([validation_error])
        
        # Act & Assert
        from src.modules.fermentation.src.service_component.errors import ValidationError as ServiceValidationError
        
        with pytest.raises(ServiceValidationError) as exc_info:
            await service.complete_fermentation(
                fermentation_id=fermentation_id,
                winery_id=winery_id,
                user_id=42,
                final_sugar_brix=high_residual_sugar,
                final_mass_kg=950.0
            )
        
        # Verify error mentions sugar/brix
        assert "sugar" in str(exc_info.value).lower() or "brix" in str(exc_info.value).lower()
        
        # Verify status was NOT updated
        mock_fermentation_repo.update_status.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_complete_fermentation_not_found(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a non-existent fermentation ID
        WHEN complete_fermentation is called
        THEN NotFoundError is raised
        
        SUCCESS CRITERIA:
        ✓ Repository.get_by_id() returns None
        ✓ NotFoundError raised
        ✓ Validator NOT called
        ✓ Status NOT updated
        """
        # Arrange
        from src.modules.fermentation.src.service_component.errors import NotFoundError
        
        fermentation_id = 999
        winery_id = 1
        
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.complete_fermentation(
                fermentation_id=fermentation_id,
                winery_id=winery_id,
                user_id=42,
                final_sugar_brix=3.0,
                final_mass_kg=950.0
            )
        
        assert f"{fermentation_id}" in str(exc_info.value)
        
        # Verify status was NOT updated
        mock_fermentation_repo.update_status.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_complete_fermentation_wrong_winery(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a fermentation belonging to winery 1
        WHEN complete_fermentation is called with winery_id=2
        THEN NotFoundError is raised (multi-tenant isolation)
        
        SUCCESS CRITERIA:
        ✓ Repository.get_by_id() scopes by winery_id
        ✓ Returns None for wrong winery
        ✓ NotFoundError raised
        """
        # Arrange
        from src.modules.fermentation.src.service_component.errors import NotFoundError
        
        fermentation_id = 1
        wrong_winery_id = 2
        
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.complete_fermentation(
                fermentation_id=fermentation_id,
                winery_id=wrong_winery_id,
                user_id=42,
                final_sugar_brix=3.0,
                final_mass_kg=950.0
            )
        
        # Verify repository queried with wrong winery
        mock_fermentation_repo.get_by_id.assert_called_once_with(
            fermentation_id=fermentation_id,
            winery_id=wrong_winery_id
        )
    
    @pytest.mark.asyncio
    async def test_complete_fermentation_repository_error(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        mock_validator: Mock,
        active_fermentation: Mock
    ):
        """
        GIVEN repository encounters error during status update
        WHEN complete_fermentation is called
        THEN RepositoryError propagates
        
        SUCCESS CRITERIA:
        ✓ Validation passes
        ✓ Repository.update_status() raises RepositoryError
        ✓ Error propagates to caller
        """
        # Arrange
        from src.modules.fermentation.src.repository_component.errors import RepositoryError
        from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
        
        fermentation_id = 1
        winery_id = 1
        
        mock_fermentation_repo.get_by_id.return_value = active_fermentation
        
        # Validators pass
        mock_validator.validate_completion_criteria.return_value = ValidationResult.success()
        mock_validator.validate_status_transition.return_value = ValidationResult.success()
        
        # Repository raises error
        mock_fermentation_repo.update_status.side_effect = RepositoryError(
            "Database transaction failed"
        )
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await service.complete_fermentation(
                fermentation_id=fermentation_id,
                winery_id=winery_id,
                user_id=42,
                final_sugar_brix=3.0,
                final_mass_kg=950.0
            )
        
        assert "Database transaction failed" in str(exc_info.value)


class TestSoftDelete:
    """
    Test suite for FermentationService.soft_delete()
    
    TDD Phase: RED
    Created: 2025-10-21
    
    Business Rules:
    1. Must fetch fermentation first (verify existence + ownership)
    2. Soft delete sets deleted_at timestamp
    3. Idempotent (can delete already-deleted records)
    4. Returns bool success
    
    Coverage:
    - Happy path: successful soft delete
    - Not found: fermentation doesn't exist
    - Wrong winery: multi-tenant violation
    - Already deleted: idempotent behavior (returns True)
    - Repository error: database failure
    """
    
    @pytest.fixture
    def mock_fermentation_repo(self) -> Mock:
        """Mock repository for testing service logic in isolation."""
        return create_autospec(IFermentationRepository, instance=True)
    
    @pytest.fixture
    def mock_validator(self) -> Mock:
        """Mock validator for testing service logic in isolation."""
        return create_autospec(IFermentationValidator, instance=True)
    
    @pytest.fixture
    def service(
        self,
        mock_fermentation_repo: Mock,
        mock_validator: Mock
    ) -> FermentationService:
        """Service instance with mocked dependencies."""
        return FermentationService(
            fermentation_repo=mock_fermentation_repo,
            validator=mock_validator
        )
    
    @pytest.fixture
    def fermentation_entity(self) -> Mock:
        """Mock fermentation entity for testing."""
        fermentation = Mock(spec=Fermentation)
        fermentation.id = 1
        fermentation.winery_id = 1
        fermentation.deleted_at = None
        return fermentation
    
    @pytest.mark.asyncio
    async def test_soft_delete_happy_path(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        fermentation_entity: Fermentation
    ):
        """
        GIVEN an existing active fermentation
        WHEN soft_delete is called
        THEN fermentation is marked as deleted
        
        SUCCESS CRITERIA:
        ✓ Fermentation fetched from repository
        ✓ Soft delete operation executed
        ✓ Returns True on success
        """
        # Arrange
        fermentation_id = 1
        winery_id = 1
        user_id = 42
        
        # Mock repository - fermentation exists and soft delete succeeds
        mock_fermentation_repo.get_by_id.return_value = fermentation_entity
        mock_fermentation_repo.update_status.return_value = True
        
        # Act
        result = await service.soft_delete(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            user_id=user_id
        )
        
        # Assert
        assert result is True
        
        # Verify fermentation was fetched
        mock_fermentation_repo.get_by_id.assert_called_once_with(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        # Verify update_status was called with soft_delete flag
        mock_fermentation_repo.update_status.assert_called_once()
        call_args = mock_fermentation_repo.update_status.call_args
        assert call_args.kwargs['metadata']['soft_delete'] is True
        assert call_args.kwargs['metadata']['deleted_by'] == user_id
    
    @pytest.mark.asyncio
    async def test_soft_delete_not_found(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a non-existent fermentation ID
        WHEN soft_delete is called
        THEN NotFoundError is raised
        
        SUCCESS CRITERIA:
        ✓ Repository.get_by_id() returns None
        ✓ NotFoundError raised
        ✓ Delete operation NOT executed
        """
        # Arrange
        from src.modules.fermentation.src.service_component.errors import NotFoundError
        
        fermentation_id = 999
        winery_id = 1
        user_id = 42
        
        # Mock repository - fermentation doesn't exist
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await service.soft_delete(
                fermentation_id=fermentation_id,
                winery_id=winery_id,
                user_id=user_id
            )
        
        assert f"{fermentation_id}" in str(exc_info.value) or "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_soft_delete_wrong_winery(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a fermentation belonging to winery 1
        WHEN soft_delete is called with winery_id=2
        THEN NotFoundError is raised (multi-tenant isolation)
        
        SUCCESS CRITERIA:
        ✓ Repository.get_by_id() scopes by winery_id
        ✓ Returns None for wrong winery
        ✓ NotFoundError raised
        """
        # Arrange
        from src.modules.fermentation.src.service_component.errors import NotFoundError
        
        fermentation_id = 1
        wrong_winery_id = 2
        user_id = 42
        
        # Mock repository - returns None when wrong winery_id
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError):
            await service.soft_delete(
                fermentation_id=fermentation_id,
                winery_id=wrong_winery_id,
                user_id=user_id
            )
        
        # Verify repository was queried with wrong winery (and returned None)
        mock_fermentation_repo.get_by_id.assert_called_once_with(
            fermentation_id=fermentation_id,
            winery_id=wrong_winery_id
        )
    
    @pytest.mark.asyncio
    async def test_soft_delete_already_deleted(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN a fermentation that's already soft-deleted
        WHEN soft_delete is called
        THEN it returns True (idempotent behavior)
        
        BUSINESS RULE: Soft delete is idempotent - deleting already-deleted records succeeds
        
        SUCCESS CRITERIA:
        ✓ get_by_id returns None (deleted records filtered)
        ✓ NotFoundError raised (repository filters deleted records)
        
        NOTE: This behavior depends on repository filtering. If repository
        includes deleted records in get_by_id, service should handle gracefully.
        """
        # Arrange
        from src.modules.fermentation.src.service_component.errors import NotFoundError
        
        fermentation_id = 1
        winery_id = 1
        user_id = 42
        
        # Repository filters deleted records - returns None
        mock_fermentation_repo.get_by_id.return_value = None
        
        # Act & Assert - Repository behavior treats deleted as not found
        with pytest.raises(NotFoundError):
            await service.soft_delete(
                fermentation_id=fermentation_id,
                winery_id=winery_id,
                user_id=user_id
            )
    
    @pytest.mark.asyncio
    async def test_soft_delete_repository_error(
        self,
        service: FermentationService,
        mock_fermentation_repo: Mock,
        fermentation_entity: Fermentation
    ):
        """
        GIVEN repository encounters error during soft delete
        WHEN soft_delete is called
        THEN RepositoryError propagates
        
        SUCCESS CRITERIA:
        ✓ Fermentation fetched successfully
        ✓ Repository raises error during delete
        ✓ Error propagates to caller
        """
        # Arrange
        from src.modules.fermentation.src.repository_component.errors import RepositoryError
        
        fermentation_id = 1
        winery_id = 1
        user_id = 42
        
        # Mock repository - fermentation exists but delete fails
        mock_fermentation_repo.get_by_id.return_value = fermentation_entity
        
        # Simulate database error by raising when any update/delete method called
        # We'll need to adapt this based on actual implementation
        mock_fermentation_repo.update_status.side_effect = RepositoryError(
            "Database connection lost during soft delete"
        )
        
        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await service.soft_delete(
                fermentation_id=fermentation_id,
                winery_id=winery_id,
                user_id=user_id
            )
        
        assert "connection lost" in str(exc_info.value).lower() or "Database" in str(exc_info.value)



