"""
Unit tests for WineryService.

Following TDD approach as documented in ADR-016.
Tests verify business logic, validation, and error handling (ADR-026).
"""

import pytest
from unittest.mock import Mock, create_autospec, AsyncMock

# Service under test
from src.modules.winery.src.service_component.services.winery_service import WineryService
from src.modules.winery.src.service_component.interfaces.winery_service_interface import IWineryService

# Domain entities
from src.modules.winery.src.domain.entities.winery import Winery

# DTOs
from src.modules.winery.src.domain.dtos.winery_dtos import WineryCreate, WineryUpdate

# Repositories
from src.modules.winery.src.domain.repositories.winery_repository_interface import IWineryRepository
from src.modules.fruit_origin.src.domain.repositories.vineyard_repository_interface import IVineyardRepository
from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository

# Errors (ADR-026)
from src.shared.domain.errors import (
    WineryNotFound,
    WineryHasActiveDataError,
    DuplicateCodeError,
    InvalidWineryData,
)


class TestWineryService:
    """Test suite for winery CRUD operations in WineryService."""
    
    @pytest.fixture
    def mock_winery_repo(self) -> Mock:
        """Mock winery repository."""
        return create_autospec(IWineryRepository, instance=True)
    
    @pytest.fixture
    def mock_vineyard_repo(self) -> Mock:
        """Mock vineyard repository (for deletion protection)."""
        return create_autospec(IVineyardRepository, instance=True)
    
    @pytest.fixture
    def mock_fermentation_repo(self) -> Mock:
        """Mock fermentation repository (for deletion protection)."""
        return create_autospec(IFermentationRepository, instance=True)
    
    @pytest.fixture
    def service(
        self,
        mock_winery_repo: Mock,
        mock_vineyard_repo: Mock,
        mock_fermentation_repo: Mock
    ) -> WineryService:
        """Service instance with mocked dependencies."""
        return WineryService(
            winery_repo=mock_winery_repo,
            vineyard_repo=mock_vineyard_repo,
            fermentation_repo=mock_fermentation_repo
        )
    
    @pytest.fixture
    def valid_winery_data(self) -> WineryCreate:
        """Valid DTO for creating a winery."""
        return WineryCreate(
            code="BODEGA-001",
            name="Bodega Test",
            location="Mendoza, Argentina",
            notes="Test winery for unit tests"
        )
    
    @pytest.fixture
    def expected_winery_entity(self) -> Mock:
        """Expected winery entity from repository."""
        winery = Mock(spec=Winery)
        winery.id = 1
        winery.code = "BODEGA-001"
        winery.name = "Bodega Test"
        winery.location = "Mendoza, Argentina"
        winery.notes = "Test winery for unit tests"
        winery.created_at = None
        winery.updated_at = None
        return winery
    
    # ==================================================================================
    # CREATE WINERY TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_create_winery_success(
        self,
        service: WineryService,
        mock_winery_repo: Mock,
        valid_winery_data: WineryCreate,
        expected_winery_entity: Mock
    ):
        """
        GIVEN valid winery data
        WHEN create_winery is called
        THEN it validates, creates entity, persists and returns it
        
        SUCCESS CRITERIA (ADR-016):
        ✓ Validates required fields
        ✓ Validates code format
        ✓ Checks code uniqueness
        ✓ Repository.create() is called with Winery entity
        ✓ Returns Winery entity with all fields
        """
        # Arrange
        mock_winery_repo.get_by_code = AsyncMock(return_value=None)  # Code not exists
        mock_winery_repo.create = AsyncMock(return_value=expected_winery_entity)
        
        # Act
        result = await service.create_winery(data=valid_winery_data)
        
        # Assert
        mock_winery_repo.get_by_code.assert_called_once_with("BODEGA-001")
        mock_winery_repo.create.assert_called_once()
        
        # Verify entity passed to create has correct values
        created_entity = mock_winery_repo.create.call_args[0][0]
        assert created_entity.code == "BODEGA-001"
        assert created_entity.name == "Bodega Test"
        assert created_entity.location == "Mendoza, Argentina"
        
        assert result == expected_winery_entity
        assert result.id == 1
        assert result.code == "BODEGA-001"
    
    @pytest.mark.asyncio
    async def test_create_winery_missing_code_raises_error(
        self,
        service: WineryService
    ):
        """
        GIVEN winery data without code
        WHEN create_winery is called
        THEN it raises InvalidWineryData
        
        VALIDATION (ADR-016):
        ✓ Code is required field
        ✓ Error is domain error (not HTTPException)
        """
        # Arrange
        invalid_data = WineryCreate(code="", name="Test Winery")
        
        # Act & Assert
        with pytest.raises(InvalidWineryData) as exc_info:
            await service.create_winery(data=invalid_data)
        
        assert "Code is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_winery_missing_name_raises_error(
        self,
        service: WineryService
    ):
        """
        GIVEN winery data without name
        WHEN create_winery is called
        THEN it raises InvalidWineryData
        
        VALIDATION (ADR-016):
        ✓ Name is required field
        """
        # Arrange
        invalid_data = WineryCreate(code="TEST-001", name="")
        
        # Act & Assert
        with pytest.raises(InvalidWineryData) as exc_info:
            await service.create_winery(data=invalid_data)
        
        assert "Name is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_winery_invalid_code_format_raises_error(
        self,
        service: WineryService
    ):
        """
        GIVEN winery data with invalid code format
        WHEN create_winery is called
        THEN it raises InvalidWineryData
        
        VALIDATION (ADR-016):
        ✓ Code must be uppercase alphanumeric + hyphens
        ✓ Lowercase, spaces, special chars not allowed
        """
        # Arrange
        invalid_data = WineryCreate(code="bodega-001", name="Test Winery")  # lowercase
        
        # Act & Assert
        with pytest.raises(InvalidWineryData) as exc_info:
            await service.create_winery(data=invalid_data)
        
        assert "Code must be uppercase alphanumeric" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_winery_duplicate_code_raises_error(
        self,
        service: WineryService,
        mock_winery_repo: Mock,
        valid_winery_data: WineryCreate
    ):
        """
        GIVEN winery code already exists
        WHEN create_winery is called
        THEN it raises DuplicateCodeError
        
        BUSINESS RULES (ADR-016):
        ✓ Code uniqueness is global (across all wineries)
        ✓ Error is domain error
        """
        # Arrange
        existing_winery = Mock(spec=Winery)
        existing_winery.id = 999
        existing_winery.code = "BODEGA-001"
        mock_winery_repo.get_by_code = AsyncMock(return_value=existing_winery)
        
        # Act & Assert
        with pytest.raises(DuplicateCodeError) as exc_info:
            await service.create_winery(data=valid_winery_data)
        
        assert "BODEGA-001" in str(exc_info.value)
        assert "already exists" in str(exc_info.value)
    
    # ==================================================================================
    # GET WINERY TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_get_winery_success(
        self,
        service: WineryService,
        mock_winery_repo: Mock,
        expected_winery_entity: Mock
    ):
        """
        GIVEN winery exists
        WHEN get_winery is called
        THEN it returns the winery entity
        """
        # Arrange
        winery_id = 1
        mock_winery_repo.get_by_id = AsyncMock(return_value=expected_winery_entity)
        
        # Act
        result = await service.get_winery(winery_id=winery_id)
        
        # Assert
        mock_winery_repo.get_by_id.assert_called_once_with(winery_id)
        assert result == expected_winery_entity
        assert result.id == 1
    
    @pytest.mark.asyncio
    async def test_get_winery_not_found_raises_error(
        self,
        service: WineryService,
        mock_winery_repo: Mock
    ):
        """
        GIVEN winery does not exist
        WHEN get_winery is called
        THEN it raises WineryNotFound
        """
        # Arrange
        winery_id = 999
        mock_winery_repo.get_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(WineryNotFound) as exc_info:
            await service.get_winery(winery_id=winery_id)
        
        assert str(winery_id) in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_winery_by_code_success(
        self,
        service: WineryService,
        mock_winery_repo: Mock,
        expected_winery_entity: Mock
    ):
        """
        GIVEN winery exists with code
        WHEN get_winery_by_code is called
        THEN it returns the winery entity
        """
        # Arrange
        code = "BODEGA-001"
        mock_winery_repo.get_by_code = AsyncMock(return_value=expected_winery_entity)
        
        # Act
        result = await service.get_winery_by_code(code=code)
        
        # Assert
        mock_winery_repo.get_by_code.assert_called_once_with(code)
        assert result == expected_winery_entity
        assert result.code == "BODEGA-001"
    
    @pytest.mark.asyncio
    async def test_get_winery_by_code_not_found_raises_error(
        self,
        service: WineryService,
        mock_winery_repo: Mock
    ):
        """
        GIVEN winery does not exist with code
        WHEN get_winery_by_code is called
        THEN it raises WineryNotFound
        """
        # Arrange
        code = "NONEXISTENT"
        mock_winery_repo.get_by_code = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(WineryNotFound) as exc_info:
            await service.get_winery_by_code(code=code)
        
        assert code in str(exc_info.value)
    
    # ==================================================================================
    # LIST WINERIES TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_list_wineries_empty(
        self,
        service: WineryService,
        mock_winery_repo: Mock
    ):
        """
        GIVEN no wineries exist
        WHEN list_wineries is called
        THEN it returns empty list
        """
        # Arrange
        mock_winery_repo.list_all = AsyncMock(return_value=[])
        
        # Act
        result = await service.list_wineries()
        
        # Assert
        mock_winery_repo.list_all.assert_called_once_with(skip=0, limit=100)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_list_wineries_with_pagination(
        self,
        service: WineryService,
        mock_winery_repo: Mock
    ):
        """
        GIVEN wineries exist
        WHEN list_wineries is called with pagination
        THEN it returns paginated list
        """
        # Arrange
        winery1 = Mock(spec=Winery)
        winery1.id = 1
        winery1.code = "BODEGA-001"
        
        winery2 = Mock(spec=Winery)
        winery2.id = 2
        winery2.code = "BODEGA-002"
        
        mock_winery_repo.list_all = AsyncMock(return_value=[winery1, winery2])
        
        # Act
        result = await service.list_wineries(skip=10, limit=20)
        
        # Assert
        mock_winery_repo.list_all.assert_called_once_with(skip=10, limit=20)
        assert len(result) == 2
        assert result[0].code == "BODEGA-001"
        assert result[1].code == "BODEGA-002"
    
    # ==================================================================================
    # UPDATE WINERY TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_update_winery_success(
        self,
        service: WineryService,
        mock_winery_repo: Mock,
        expected_winery_entity: Mock
    ):
        """
        GIVEN winery exists
        WHEN update_winery is called
        THEN it updates and returns updated entity
        
        BUSINESS RULES (ADR-016):
        ✓ Code is immutable (cannot be updated)
        ✓ Name, location, notes can be updated
        """
        # Arrange
        winery_id = 1
        update_data = WineryUpdate(
            name="Updated Name",
            location="New Location"
        )
        
        # Mock existing winery
        existing_winery = Mock(spec=Winery)
        existing_winery.id = 1
        existing_winery.code = "BODEGA-001"
        existing_winery.name = "Old Name"
        existing_winery.location = "Old Location"
        existing_winery.notes = "Old Notes"
        
        # Mock updated winery
        updated_winery = Mock(spec=Winery)
        updated_winery.id = 1
        updated_winery.code = "BODEGA-001"  # Code unchanged
        updated_winery.name = "Updated Name"
        updated_winery.location = "New Location"
        updated_winery.notes = "Old Notes"
        
        mock_winery_repo.get_by_id = AsyncMock(return_value=existing_winery)
        mock_winery_repo.update = AsyncMock(return_value=updated_winery)
        
        # Act
        result = await service.update_winery(winery_id=winery_id, data=update_data)
        
        # Assert
        mock_winery_repo.get_by_id.assert_called_once_with(winery_id)
        mock_winery_repo.update.assert_called_once_with(winery_id, update_data)
        
        # Verify result is the updated winery returned by repository
        assert result.name == "Updated Name"
        assert result.location == "New Location"
    
    @pytest.mark.asyncio
    async def test_update_winery_not_found_raises_error(
        self,
        service: WineryService,
        mock_winery_repo: Mock
    ):
        """
        GIVEN winery does not exist
        WHEN update_winery is called
        THEN it raises WineryNotFound
        """
        # Arrange
        winery_id = 999
        update_data = WineryUpdate(name="New Name")
        mock_winery_repo.get_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(WineryNotFound):
            await service.update_winery(winery_id=winery_id, data=update_data)
    
    @pytest.mark.asyncio
    async def test_update_winery_empty_name_raises_error(
        self,
        service: WineryService,
        mock_winery_repo: Mock
    ):
        """
        GIVEN winery exists
        WHEN update_winery is called with empty name
        THEN it raises InvalidWineryData
        """
        # Arrange
        winery_id = 1
        update_data = WineryUpdate(name="   ")  # Empty after strip
        
        existing_winery = Mock(spec=Winery)
        existing_winery.id = 1
        mock_winery_repo.get_by_id = AsyncMock(return_value=existing_winery)
        
        # Act & Assert
        with pytest.raises(InvalidWineryData) as exc_info:
            await service.update_winery(winery_id=winery_id, data=update_data)
        
        assert "Name cannot be empty" in str(exc_info.value)
    
    # ==================================================================================
    # DELETE WINERY TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_delete_winery_success(
        self,
        service: WineryService,
        mock_winery_repo: Mock,
        mock_vineyard_repo: Mock,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN winery exists with no active data
        WHEN delete_winery is called
        THEN it deletes successfully
        
        DELETION PROTECTION (ADR-016):
        ✓ Checks for active vineyards
        ✓ Checks for active fermentations
        ✓ Only deletes if no active data
        """
        # Arrange
        winery_id = 1
        winery = Mock(spec=Winery)
        winery.id = 1
        winery.code = "BODEGA-001"
        
        mock_winery_repo.get_by_id = AsyncMock(return_value=winery)
        mock_vineyard_repo.get_by_winery = AsyncMock(return_value=[])  # No vineyards
        mock_fermentation_repo.get_by_winery = AsyncMock(return_value=[])  # No fermentations
        mock_winery_repo.delete = AsyncMock()
        
        # Act
        await service.delete_winery(winery_id=winery_id)
        
        # Assert
        mock_winery_repo.get_by_id.assert_called_once_with(winery_id)
        mock_vineyard_repo.get_by_winery.assert_called_once_with(winery_id)
        mock_fermentation_repo.get_by_winery.assert_called_once_with(winery_id)
        mock_winery_repo.delete.assert_called_once_with(winery_id)
    
    @pytest.mark.asyncio
    async def test_delete_winery_not_found_raises_error(
        self,
        service: WineryService,
        mock_winery_repo: Mock
    ):
        """
        GIVEN winery does not exist
        WHEN delete_winery is called
        THEN it raises WineryNotFound
        """
        # Arrange
        winery_id = 999
        mock_winery_repo.get_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(WineryNotFound):
            await service.delete_winery(winery_id=winery_id)
    
    @pytest.mark.asyncio
    async def test_delete_winery_with_active_vineyards_raises_error(
        self,
        service: WineryService,
        mock_winery_repo: Mock,
        mock_vineyard_repo: Mock,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN winery has active vineyards
        WHEN delete_winery is called
        THEN it raises WineryHasActiveDataError
        
        DELETION PROTECTION (ADR-016):
        ✓ Two-layer protection: service validation + DB constraints
        ✓ Clear error message for user
        """
        # Arrange
        winery_id = 1
        winery = Mock(spec=Winery)
        winery.id = 1
        winery.code = "BODEGA-001"
        
        vineyard = Mock()
        vineyard.id = 1
        
        mock_winery_repo.get_by_id = AsyncMock(return_value=winery)
        mock_vineyard_repo.get_by_winery = AsyncMock(return_value=[vineyard])  # Has vineyard
        mock_fermentation_repo.get_by_winery = AsyncMock(return_value=[])
        
        # Act & Assert
        with pytest.raises(WineryHasActiveDataError) as exc_info:
            await service.delete_winery(winery_id=winery_id)
        
        assert "vineyards" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_winery_with_active_fermentations_raises_error(
        self,
        service: WineryService,
        mock_winery_repo: Mock,
        mock_vineyard_repo: Mock,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN winery has active fermentations
        WHEN delete_winery is called
        THEN it raises WineryHasActiveDataError
        """
        # Arrange
        winery_id = 1
        winery = Mock(spec=Winery)
        winery.id = 1
        winery.code = "BODEGA-001"
        
        fermentation = Mock()
        fermentation.id = 1
        
        mock_winery_repo.get_by_id = AsyncMock(return_value=winery)
        mock_vineyard_repo.get_by_winery = AsyncMock(return_value=[])
        mock_fermentation_repo.get_by_winery = AsyncMock(return_value=[fermentation])  # Has fermentation
        
        # Act & Assert
        with pytest.raises(WineryHasActiveDataError) as exc_info:
            await service.delete_winery(winery_id=winery_id)
        
        assert "fermentations" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_winery_with_both_active_data_types_raises_error(
        self,
        service: WineryService,
        mock_winery_repo: Mock,
        mock_vineyard_repo: Mock,
        mock_fermentation_repo: Mock
    ):
        """
        GIVEN winery has active vineyards AND fermentations
        WHEN delete_winery is called
        THEN it raises WineryHasActiveDataError with both mentioned
        """
        # Arrange
        winery_id = 1
        winery = Mock(spec=Winery)
        winery.id = 1
        winery.code = "BODEGA-001"
        
        vineyard = Mock()
        fermentation = Mock()
        
        mock_winery_repo.get_by_id = AsyncMock(return_value=winery)
        mock_vineyard_repo.get_by_winery = AsyncMock(return_value=[vineyard])
        mock_fermentation_repo.get_by_winery = AsyncMock(return_value=[fermentation])
        
        # Act & Assert
        with pytest.raises(WineryHasActiveDataError) as exc_info:
            await service.delete_winery(winery_id=winery_id)
        
        error_msg = str(exc_info.value)
        assert "vineyards" in error_msg
        assert "fermentations" in error_msg
    
    # ==================================================================================
    # UTILITY OPERATIONS TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_winery_exists_true(
        self,
        service: WineryService,
        mock_winery_repo: Mock
    ):
        """
        GIVEN winery exists
        WHEN winery_exists is called
        THEN it returns True
        """
        # Arrange
        winery_id = 1
        winery = Mock(spec=Winery)
        mock_winery_repo.get_by_id = AsyncMock(return_value=winery)
        
        # Act
        result = await service.winery_exists(winery_id=winery_id)
        
        # Assert
        assert result is True
        mock_winery_repo.get_by_id.assert_called_once_with(winery_id)
    
    @pytest.mark.asyncio
    async def test_winery_exists_false(
        self,
        service: WineryService,
        mock_winery_repo: Mock
    ):
        """
        GIVEN winery does not exist
        WHEN winery_exists is called
        THEN it returns False
        """
        # Arrange
        winery_id = 999
        mock_winery_repo.get_by_id = AsyncMock(return_value=None)
        
        # Act
        result = await service.winery_exists(winery_id=winery_id)
        
        # Assert
        assert result is False
        mock_winery_repo.get_by_id.assert_called_once_with(winery_id)
    
    @pytest.mark.asyncio
    async def test_count_wineries(
        self,
        service: WineryService,
        mock_winery_repo: Mock
    ):
        """
        GIVEN wineries exist
        WHEN count_wineries is called
        THEN it returns total count
        """
        # Arrange
        mock_winery_repo.count = AsyncMock(return_value=42)
        
        # Act
        result = await service.count_wineries()
        
        # Assert
        assert result == 42
        mock_winery_repo.count.assert_called_once()
