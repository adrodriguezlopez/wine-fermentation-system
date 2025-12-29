"""
Unit tests for FruitOriginService - Vineyard Operations.

Following TDD approach as documented in ADR-014.
Tests verify business logic, security (ADR-025), and error handling (ADR-026).
"""

import pytest
from unittest.mock import Mock, create_autospec, AsyncMock
from datetime import date, datetime
from typing import Optional, List

# Service under test
from src.modules.fruit_origin.src.service_component.services.fruit_origin_service import FruitOriginService
from src.modules.fruit_origin.src.service_component.interfaces.fruit_origin_service_interface import IFruitOriginService

# Domain entities
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock

# DTOs
from src.modules.fruit_origin.src.domain.dtos.vineyard_dtos import VineyardCreate, VineyardUpdate
from src.modules.fruit_origin.src.domain.dtos.harvest_lot_dtos import HarvestLotCreate

# Repositories
from src.modules.fruit_origin.src.domain.repositories.vineyard_repository_interface import IVineyardRepository
from src.modules.fruit_origin.src.domain.repositories.harvest_lot_repository_interface import IHarvestLotRepository

# Errors (ADR-026)
from src.shared.domain.errors import (
    VineyardNotFound,
    VineyardHasActiveLotsError,
    VineyardBlockNotFound,
    InvalidHarvestDate,
    DuplicateCodeError,
)


class TestVineyardOperations:
    """Test suite for vineyard CRUD operations in FruitOriginService."""
    
    @pytest.fixture
    def mock_vineyard_repo(self) -> Mock:
        """Mock vineyard repository."""
        return create_autospec(IVineyardRepository, instance=True)
    
    @pytest.fixture
    def mock_harvest_lot_repo(self) -> Mock:
        """Mock harvest lot repository."""
        return create_autospec(IHarvestLotRepository, instance=True)
    
    @pytest.fixture
    def service(
        self,
        mock_vineyard_repo: Mock,
        mock_harvest_lot_repo: Mock
    ) -> FruitOriginService:
        """Service instance with mocked dependencies."""
        return FruitOriginService(
            vineyard_repo=mock_vineyard_repo,
            harvest_lot_repo=mock_harvest_lot_repo
        )
    
    @pytest.fixture
    def valid_vineyard_data(self) -> VineyardCreate:
        """Valid DTO for creating a vineyard."""
        return VineyardCreate(
            code="VIN-001",
            name="North Ridge Vineyard",
            notes="Premium Chardonnay site"
        )
    
    @pytest.fixture
    def expected_vineyard_entity(self) -> Mock:
        """Expected vineyard entity from repository."""
        vineyard = Mock(spec=Vineyard)
        vineyard.id = 1
        vineyard.winery_id = 1
        vineyard.code = "VIN-001"
        vineyard.name = "North Ridge Vineyard"
        vineyard.notes = "Premium Chardonnay site"
        vineyard.is_deleted = False
        vineyard.blocks = []
        return vineyard
    
    # ==================================================================================
    # CREATE VINEYARD TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_create_vineyard_success(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock,
        valid_vineyard_data: VineyardCreate,
        expected_vineyard_entity: Mock
    ):
        """
        GIVEN valid vineyard data
        WHEN create_vineyard is called
        THEN it delegates to repository and returns created entity
        
        SUCCESS CRITERIA (ADR-014):
        ✓ Repository.create() is called with winery_id and data
        ✓ Returns Vineyard entity
        ✓ Entity has all fields populated
        """
        # Arrange
        winery_id = 1
        user_id = 42
        mock_vineyard_repo.create.return_value = expected_vineyard_entity
        
        # Act
        result = await service.create_vineyard(
            winery_id=winery_id,
            user_id=user_id,
            data=valid_vineyard_data
        )
        
        # Assert
        mock_vineyard_repo.create.assert_called_once_with(
            winery_id=winery_id,
            data=valid_vineyard_data
        )
        assert result == expected_vineyard_entity
        assert result.id == 1
        assert result.winery_id == 1
        assert result.code == "VIN-001"
    
    @pytest.mark.asyncio
    async def test_create_vineyard_duplicate_code_raises_error(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock,
        valid_vineyard_data: VineyardCreate
    ):
        """
        GIVEN vineyard code already exists for winery
        WHEN create_vineyard is called
        THEN it raises DuplicateCodeError
        
        SECURITY (ADR-025):
        ✓ Error is domain error (not HTTPException)
        ✓ winery_id is part of uniqueness constraint
        """
        # Arrange
        winery_id = 1
        user_id = 42
        mock_vineyard_repo.create.side_effect = DuplicateCodeError(
            f"Vineyard with code '{valid_vineyard_data.code}' already exists for winery {winery_id}"
        )
        
        # Act & Assert
        with pytest.raises(DuplicateCodeError) as exc_info:
            await service.create_vineyard(
                winery_id=winery_id,
                user_id=user_id,
                data=valid_vineyard_data
            )
        
        assert "VIN-001" in str(exc_info.value)
        assert str(winery_id) in str(exc_info.value)
    
    # ==================================================================================
    # GET VINEYARD TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_get_vineyard_found(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock,
        expected_vineyard_entity: Mock
    ):
        """
        GIVEN vineyard exists for winery
        WHEN get_vineyard is called
        THEN it returns the vineyard entity
        """
        # Arrange
        vineyard_id = 1
        winery_id = 1
        mock_vineyard_repo.get_by_id.return_value = expected_vineyard_entity
        
        # Act
        result = await service.get_vineyard(vineyard_id, winery_id)
        
        # Assert
        mock_vineyard_repo.get_by_id.assert_called_once_with(
            vineyard_id=vineyard_id,
            winery_id=winery_id
        )
        assert result == expected_vineyard_entity
    
    @pytest.mark.asyncio
    async def test_get_vineyard_not_found(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock
    ):
        """
        GIVEN vineyard does not exist
        WHEN get_vineyard is called
        THEN it returns None
        
        SECURITY (ADR-025):
        ✓ Returns None if vineyard doesn't belong to winery (not error)
        """
        # Arrange
        vineyard_id = 999
        winery_id = 1
        mock_vineyard_repo.get_by_id.return_value = None
        
        # Act
        result = await service.get_vineyard(vineyard_id, winery_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_vineyard_cross_winery_denied(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock
    ):
        """
        GIVEN vineyard belongs to different winery
        WHEN get_vineyard is called
        THEN repository filters by winery_id (returns None)
        
        SECURITY (ADR-025):
        ✓ Multi-tenancy enforced at repository level
        ✓ Service just returns None (no cross-winery leak)
        """
        # Arrange
        vineyard_id = 1
        winery_id = 2  # Different winery
        mock_vineyard_repo.get_by_id.return_value = None  # Repository filters
        
        # Act
        result = await service.get_vineyard(vineyard_id, winery_id)
        
        # Assert
        assert result is None
        mock_vineyard_repo.get_by_id.assert_called_once_with(
            vineyard_id=vineyard_id,
            winery_id=winery_id
        )
    
    # ==================================================================================
    # LIST VINEYARDS TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_list_vineyards_empty(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock
    ):
        """
        GIVEN winery has no vineyards
        WHEN list_vineyards is called
        THEN it returns empty list
        """
        # Arrange
        winery_id = 1
        mock_vineyard_repo.get_by_winery.return_value = []
        
        # Act
        result = await service.list_vineyards(winery_id)
        
        # Assert
        assert result == []
        mock_vineyard_repo.get_by_winery.assert_called_once_with(winery_id=winery_id)
    
    @pytest.mark.asyncio
    async def test_list_vineyards_multiple(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock
    ):
        """
        GIVEN winery has multiple vineyards
        WHEN list_vineyards is called
        THEN it returns all active vineyards
        """
        # Arrange
        winery_id = 1
        vineyard1 = Mock(spec=Vineyard, id=1, code="VIN-001", is_deleted=False)
        vineyard2 = Mock(spec=Vineyard, id=2, code="VIN-002", is_deleted=False)
        mock_vineyard_repo.get_by_winery.return_value = [vineyard1, vineyard2]
        
        # Act
        result = await service.list_vineyards(winery_id)
        
        # Assert
        assert len(result) == 2
        assert result[0].code == "VIN-001"
        assert result[1].code == "VIN-002"
    
    @pytest.mark.asyncio
    async def test_list_vineyards_excludes_deleted(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock
    ):
        """
        GIVEN winery has deleted and active vineyards
        WHEN list_vineyards is called without include_deleted
        THEN it returns only active vineyards
        """
        # Arrange
        winery_id = 1
        vineyard1 = Mock(spec=Vineyard, id=1, code="VIN-001", is_deleted=False)
        vineyard2 = Mock(spec=Vineyard, id=2, code="VIN-002", is_deleted=True)
        mock_vineyard_repo.get_by_winery.return_value = [vineyard1, vineyard2]
        
        # Act
        result = await service.list_vineyards(winery_id, include_deleted=False)
        
        # Assert
        assert len(result) == 1
        assert result[0].code == "VIN-001"
    
    @pytest.mark.asyncio
    async def test_list_vineyards_includes_deleted_when_requested(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock
    ):
        """
        GIVEN winery has deleted vineyards
        WHEN list_vineyards is called with include_deleted=True
        THEN it returns all vineyards including deleted
        """
        # Arrange
        winery_id = 1
        vineyard1 = Mock(spec=Vineyard, id=1, code="VIN-001", is_deleted=False)
        vineyard2 = Mock(spec=Vineyard, id=2, code="VIN-002", is_deleted=True)
        mock_vineyard_repo.get_by_winery.return_value = [vineyard1, vineyard2]
        
        # Act
        result = await service.list_vineyards(winery_id, include_deleted=True)
        
        # Assert
        assert len(result) == 2
    
    # ==================================================================================
    # UPDATE VINEYARD TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_update_vineyard_success(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock
    ):
        """
        GIVEN vineyard exists
        WHEN update_vineyard is called
        THEN it updates via repository and returns updated entity
        """
        # Arrange
        vineyard_id = 1
        winery_id = 1
        user_id = 42
        update_data = VineyardUpdate(name="Updated Name", notes="New notes")
        updated_vineyard = Mock(spec=Vineyard)
        updated_vineyard.id = 1
        updated_vineyard.name = "Updated Name"
        updated_vineyard.notes = "New notes"
        mock_vineyard_repo.update.return_value = updated_vineyard
        
        # Act
        result = await service.update_vineyard(
            vineyard_id=vineyard_id,
            winery_id=winery_id,
            user_id=user_id,
            data=update_data
        )
        
        # Assert
        mock_vineyard_repo.update.assert_called_once_with(
            vineyard_id=vineyard_id,
            winery_id=winery_id,
            data=update_data
        )
        assert result.name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_update_vineyard_not_found_raises_error(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock
    ):
        """
        GIVEN vineyard does not exist
        WHEN update_vineyard is called
        THEN it raises VineyardNotFound
        
        ERROR HANDLING (ADR-026):
        ✓ Raises domain error (not HTTPException)
        """
        # Arrange
        vineyard_id = 999
        winery_id = 1
        user_id = 42
        update_data = VineyardUpdate(name="Updated Name")
        mock_vineyard_repo.update.return_value = None  # Not found
        
        # Act & Assert
        with pytest.raises(VineyardNotFound) as exc_info:
            await service.update_vineyard(
                vineyard_id=vineyard_id,
                winery_id=winery_id,
                user_id=user_id,
                data=update_data
            )
        
        assert str(vineyard_id) in str(exc_info.value)
    
    # ==================================================================================
    # DELETE VINEYARD TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_delete_vineyard_success_no_active_lots(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock,
        mock_harvest_lot_repo: Mock
    ):
        """
        GIVEN vineyard exists with no active harvest lots
        WHEN delete_vineyard is called
        THEN it soft deletes successfully
        
        BUSINESS RULE (ADR-014):
        ✓ Can delete vineyard if no active lots
        """
        # Arrange
        vineyard_id = 1
        winery_id = 1
        user_id = 42
        
        # Vineyard exists with no blocks (no harvest lots possible)
        vineyard = Mock(spec=Vineyard, id=1, blocks=[])
        mock_vineyard_repo.get_by_id.return_value = vineyard
        mock_vineyard_repo.delete.return_value = True
        
        # Mock get_session() to return async context manager
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=AsyncMock(fetchall=Mock(return_value=[])))
        
        async def mock_get_session():
            class AsyncContextManager:
                async def __aenter__(self):
                    return mock_session
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return AsyncContextManager()
        
        mock_vineyard_repo.get_session = mock_get_session
        
        # Act
        result = await service.delete_vineyard(vineyard_id, winery_id, user_id)
        
        # Assert
        assert result is True
        mock_vineyard_repo.delete.assert_called_once_with(vineyard_id, winery_id)
    
    @pytest.mark.asyncio
    async def test_delete_vineyard_has_active_lots_raises_error(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock,
        mock_harvest_lot_repo: Mock
    ):
        """
        GIVEN vineyard has active harvest lots
        WHEN delete_vineyard is called
        THEN it raises VineyardHasActiveLotsError
        
        BUSINESS RULE (ADR-014):
        ✓ Cannot delete vineyard if has active lots (cascade validation)
        """
        # Arrange
        vineyard_id = 1
        winery_id = 1
        user_id = 42
        
        # Vineyard exists with blocks that have active lots
        block = Mock(spec=VineyardBlock, id=1)
        vineyard = Mock(spec=Vineyard, id=1, blocks=[block])
        mock_vineyard_repo.get_by_id.return_value = vineyard
        
        # Mock get_session() to return async context manager with block IDs
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=AsyncMock(fetchall=Mock(return_value=[(1,)])))
        
        async def mock_get_session():
            class AsyncContextManager:
                async def __aenter__(self):
                    return mock_session
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return AsyncContextManager()
        
        mock_vineyard_repo.get_session = mock_get_session
        
        # Block has active harvest lots
        active_lot = Mock(spec=HarvestLot, id=1, is_deleted=False)
        mock_harvest_lot_repo.get_by_block.return_value = [active_lot]
        
        # Act & Assert
        with pytest.raises(VineyardHasActiveLotsError) as exc_info:
            await service.delete_vineyard(vineyard_id, winery_id, user_id)
        
        assert str(vineyard_id) in str(exc_info.value)
        assert "1" in str(exc_info.value)  # active_lots_count
        # Delete should NOT be called
        mock_vineyard_repo.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_vineyard_not_found_raises_error(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock
    ):
        """
        GIVEN vineyard does not exist
        WHEN delete_vineyard is called
        THEN it raises VineyardNotFound
        """
        # Arrange
        vineyard_id = 999
        winery_id = 1
        user_id = 42
        mock_vineyard_repo.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(VineyardNotFound):
            await service.delete_vineyard(vineyard_id, winery_id, user_id)
    
    @pytest.mark.asyncio
    async def test_delete_vineyard_ignores_deleted_lots(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock,
        mock_harvest_lot_repo: Mock
    ):
        """
        GIVEN vineyard has only deleted (soft-deleted) harvest lots
        WHEN delete_vineyard is called
        THEN it allows deletion (only active lots block deletion)
        
        BUSINESS RULE (ADR-014):
        ✓ Deleted lots don't block vineyard deletion
        """
        # Arrange
        vineyard_id = 1
        winery_id = 1
        user_id = 42
        
        # Vineyard with blocks
        block = Mock(spec=VineyardBlock, id=1)
        vineyard = Mock(spec=Vineyard, id=1, blocks=[block])
        mock_vineyard_repo.get_by_id.return_value = vineyard
        
        # Mock get_session() to return async context manager with block IDs
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=AsyncMock(fetchall=Mock(return_value=[(1,)])))
        
        async def mock_get_session():
            class AsyncContextManager:
                async def __aenter__(self):
                    return mock_session
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return AsyncContextManager()
        
        mock_vineyard_repo.get_session = mock_get_session
        
        # Block has only deleted lots
        deleted_lot = Mock(spec=HarvestLot, id=1, is_deleted=True)
        mock_harvest_lot_repo.get_by_block.return_value = [deleted_lot]
        mock_vineyard_repo.delete.return_value = True
        
        # Act
        result = await service.delete_vineyard(vineyard_id, winery_id, user_id)
        
        # Assert
        assert result is True
        mock_vineyard_repo.delete.assert_called_once()
