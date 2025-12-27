"""
Unit tests for FruitOriginService - Harvest Lot Operations.

Following TDD approach as documented in ADR-014.
Tests verify business rules (harvest date validation, cross-winery access).
"""

import pytest
from unittest.mock import Mock, create_autospec
from datetime import date, datetime, timezone

# Service under test
from src.modules.fruit_origin.src.service_component.services.fruit_origin_service import FruitOriginService

# Domain entities
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock

# DTOs
from src.modules.fruit_origin.src.domain.dtos.harvest_lot_dtos import HarvestLotCreate

# Repositories
from src.modules.fruit_origin.src.domain.repositories.vineyard_repository_interface import IVineyardRepository
from src.modules.fruit_origin.src.domain.repositories.harvest_lot_repository_interface import IHarvestLotRepository

# Errors (ADR-026)
from src.shared.domain.errors import (
    InvalidHarvestDate,
    VineyardBlockNotFound,
    HarvestLotNotFound,
    DuplicateCodeError,
)


class TestHarvestLotOperations:
    """Test suite for harvest lot operations in FruitOriginService."""
    
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
    def valid_harvest_lot_data(self) -> HarvestLotCreate:
        """Valid DTO for creating a harvest lot."""
        return HarvestLotCreate(
            block_id=1,
            code="LOT-2025-001",
            harvest_date=date(2025, 3, 15),
            weight_kg=5000.0,
            grape_variety="Chardonnay",
            notes="Premium fruit from north slope"
        )
    
    @pytest.fixture
    def expected_harvest_lot_entity(self) -> Mock:
        """Expected harvest lot entity from repository."""
        lot = Mock(spec=HarvestLot)
        lot.id = 1
        lot.winery_id = 1
        lot.block_id = 1
        lot.code = "LOT-2025-001"
        lot.harvest_date = date(2025, 3, 15)
        lot.weight_kg = 5000.0
        lot.is_deleted = False
        return lot
    
    # ==================================================================================
    # CREATE HARVEST LOT TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_create_harvest_lot_success(
        self,
        service: FruitOriginService,
        mock_harvest_lot_repo: Mock,
        valid_harvest_lot_data: HarvestLotCreate,
        expected_harvest_lot_entity: Mock
    ):
        """
        GIVEN valid harvest lot data with past harvest date
        WHEN create_harvest_lot is called
        THEN it creates lot successfully
        
        SUCCESS CRITERIA (ADR-014):
        ✓ Harvest date validation passes (not in future)
        ✓ Repository.create() is called
        ✓ Returns HarvestLot entity
        """
        # Arrange
        winery_id = 1
        user_id = 42
        mock_harvest_lot_repo.create.return_value = expected_harvest_lot_entity
        
        # Act
        result = await service.create_harvest_lot(
            winery_id=winery_id,
            user_id=user_id,
            data=valid_harvest_lot_data
        )
        
        # Assert
        mock_harvest_lot_repo.create.assert_called_once_with(
            winery_id=winery_id,
            data=valid_harvest_lot_data
        )
        assert result == expected_harvest_lot_entity
        assert result.code == "LOT-2025-001"
    
    @pytest.mark.asyncio
    async def test_create_harvest_lot_future_date_rejected(
        self,
        service: FruitOriginService,
        mock_harvest_lot_repo: Mock
    ):
        """
        GIVEN harvest date is in the future
        WHEN create_harvest_lot is called
        THEN it raises InvalidHarvestDate
        
        BUSINESS RULE (ADR-014):
        ✓ Harvest date cannot be in future (data quality)
        ✓ Error raised BEFORE repository call
        """
        # Arrange
        winery_id = 1
        user_id = 42
        future_date = date(2026, 12, 31)  # Future date
        harvest_lot_data = HarvestLotCreate(
            block_id=1,
            code="LOT-2026-001",
            harvest_date=future_date,
            weight_kg=5000.0
        )
        
        # Act & Assert
        with pytest.raises(InvalidHarvestDate) as exc_info:
            await service.create_harvest_lot(
                winery_id=winery_id,
                user_id=user_id,
                data=harvest_lot_data
            )
        
        assert "future" in str(exc_info.value).lower()
        # Repository should NOT be called
        mock_harvest_lot_repo.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_harvest_lot_today_allowed(
        self,
        service: FruitOriginService,
        mock_harvest_lot_repo: Mock,
        expected_harvest_lot_entity: Mock
    ):
        """
        GIVEN harvest date is today
        WHEN create_harvest_lot is called
        THEN it creates lot successfully (today is valid)
        """
        # Arrange
        winery_id = 1
        user_id = 42
        today = date.today()
        harvest_lot_data = HarvestLotCreate(
            block_id=1,
            code="LOT-TODAY",
            harvest_date=today,
            weight_kg=5000.0
        )
        mock_harvest_lot_repo.create.return_value = expected_harvest_lot_entity
        
        # Act
        result = await service.create_harvest_lot(
            winery_id=winery_id,
            user_id=user_id,
            data=harvest_lot_data
        )
        
        # Assert
        assert result is not None
        mock_harvest_lot_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_harvest_lot_vineyard_block_not_found(
        self,
        service: FruitOriginService,
        mock_harvest_lot_repo: Mock,
        valid_harvest_lot_data: HarvestLotCreate
    ):
        """
        GIVEN vineyard block does not exist
        WHEN create_harvest_lot is called
        THEN it raises VineyardBlockNotFound
        
        VALIDATION (ADR-014):
        ✓ Foreign key constraint caught and converted to domain error
        """
        # Arrange
        winery_id = 1
        user_id = 42
        # Simulate FK constraint violation
        mock_harvest_lot_repo.create.side_effect = Exception(
            "FOREIGN KEY constraint failed: block_id"
        )
        
        # Act & Assert
        with pytest.raises(VineyardBlockNotFound) as exc_info:
            await service.create_harvest_lot(
                winery_id=winery_id,
                user_id=user_id,
                data=valid_harvest_lot_data
            )
        
        assert str(valid_harvest_lot_data.block_id) in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_harvest_lot_duplicate_code_raises_error(
        self,
        service: FruitOriginService,
        mock_harvest_lot_repo: Mock,
        valid_harvest_lot_data: HarvestLotCreate
    ):
        """
        GIVEN harvest lot code already exists for winery
        WHEN create_harvest_lot is called
        THEN repository raises DuplicateCodeError
        """
        # Arrange
        winery_id = 1
        user_id = 42
        mock_harvest_lot_repo.create.side_effect = DuplicateCodeError(
            f"Harvest lot with code '{valid_harvest_lot_data.code}' already exists"
        )
        
        # Act & Assert
        with pytest.raises(DuplicateCodeError):
            await service.create_harvest_lot(
                winery_id=winery_id,
                user_id=user_id,
                data=valid_harvest_lot_data
            )
    
    # ==================================================================================
    # GET HARVEST LOT TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_get_harvest_lot_found(
        self,
        service: FruitOriginService,
        mock_harvest_lot_repo: Mock,
        expected_harvest_lot_entity: Mock
    ):
        """
        GIVEN harvest lot exists for winery
        WHEN get_harvest_lot is called
        THEN it returns the lot entity
        """
        # Arrange
        lot_id = 1
        winery_id = 1
        mock_harvest_lot_repo.get_by_id.return_value = expected_harvest_lot_entity
        
        # Act
        result = await service.get_harvest_lot(lot_id, winery_id)
        
        # Assert
        mock_harvest_lot_repo.get_by_id.assert_called_once_with(
            lot_id=lot_id,
            winery_id=winery_id
        )
        assert result == expected_harvest_lot_entity
    
    @pytest.mark.asyncio
    async def test_get_harvest_lot_not_found(
        self,
        service: FruitOriginService,
        mock_harvest_lot_repo: Mock
    ):
        """
        GIVEN harvest lot does not exist
        WHEN get_harvest_lot is called
        THEN it returns None
        
        SECURITY (ADR-025):
        ✓ Returns None if lot doesn't belong to winery
        """
        # Arrange
        lot_id = 999
        winery_id = 1
        mock_harvest_lot_repo.get_by_id.return_value = None
        
        # Act
        result = await service.get_harvest_lot(lot_id, winery_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_harvest_lot_cross_winery_denied(
        self,
        service: FruitOriginService,
        mock_harvest_lot_repo: Mock
    ):
        """
        GIVEN harvest lot belongs to different winery
        WHEN get_harvest_lot is called
        THEN repository filters by winery_id (returns None)
        
        SECURITY (ADR-025):
        ✓ Multi-tenancy enforced at repository level
        """
        # Arrange
        lot_id = 1
        winery_id = 2  # Different winery
        mock_harvest_lot_repo.get_by_id.return_value = None
        
        # Act
        result = await service.get_harvest_lot(lot_id, winery_id)
        
        # Assert
        assert result is None
        mock_harvest_lot_repo.get_by_id.assert_called_once_with(
            lot_id=lot_id,
            winery_id=winery_id
        )
    
    # ==================================================================================
    # LIST HARVEST LOTS TESTS
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_list_harvest_lots_by_winery(
        self,
        service: FruitOriginService,
        mock_harvest_lot_repo: Mock
    ):
        """
        GIVEN winery has harvest lots
        WHEN list_harvest_lots is called without vineyard filter
        THEN it returns all lots for winery
        """
        # Arrange
        winery_id = 1
        lot1 = Mock(spec=HarvestLot, id=1, code="LOT-001")
        lot2 = Mock(spec=HarvestLot, id=2, code="LOT-002")
        mock_harvest_lot_repo.get_by_winery.return_value = [lot1, lot2]
        
        # Act
        result = await service.list_harvest_lots(winery_id)
        
        # Assert
        assert len(result) == 2
        mock_harvest_lot_repo.get_by_winery.assert_called_once_with(winery_id)
    
    @pytest.mark.asyncio
    async def test_list_harvest_lots_by_vineyard(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock,
        mock_harvest_lot_repo: Mock
    ):
        """
        GIVEN vineyard has harvest lots
        WHEN list_harvest_lots is called with vineyard_id filter
        THEN it returns only lots for that vineyard
        
        LOGIC:
        1. Get vineyard to get all blocks
        2. Get lots for each block
        3. Aggregate results
        """
        # Arrange
        winery_id = 1
        vineyard_id = 1
        
        # Vineyard with 2 blocks
        block1 = Mock(spec=VineyardBlock, id=1)
        block2 = Mock(spec=VineyardBlock, id=2)
        vineyard = Mock(spec=Vineyard, id=1, blocks=[block1, block2])
        mock_vineyard_repo.get_by_id.return_value = vineyard
        
        # Block 1 has 2 lots, Block 2 has 1 lot
        lot1 = Mock(spec=HarvestLot, id=1, code="LOT-001", block_id=1)
        lot2 = Mock(spec=HarvestLot, id=2, code="LOT-002", block_id=1)
        lot3 = Mock(spec=HarvestLot, id=3, code="LOT-003", block_id=2)
        
        def get_by_block_side_effect(block_id, winery_id):
            if block_id == 1:
                return [lot1, lot2]
            elif block_id == 2:
                return [lot3]
            return []
        
        mock_harvest_lot_repo.get_by_block.side_effect = get_by_block_side_effect
        
        # Act
        result = await service.list_harvest_lots(winery_id, vineyard_id=vineyard_id)
        
        # Assert
        assert len(result) == 3
        mock_vineyard_repo.get_by_id.assert_called_once_with(vineyard_id, winery_id)
        assert mock_harvest_lot_repo.get_by_block.call_count == 2
    
    @pytest.mark.asyncio
    async def test_list_harvest_lots_vineyard_not_found(
        self,
        service: FruitOriginService,
        mock_vineyard_repo: Mock,
        mock_harvest_lot_repo: Mock
    ):
        """
        GIVEN vineyard does not exist
        WHEN list_harvest_lots is called with vineyard_id
        THEN it returns empty list
        """
        # Arrange
        winery_id = 1
        vineyard_id = 999
        mock_vineyard_repo.get_by_id.return_value = None
        
        # Act
        result = await service.list_harvest_lots(winery_id, vineyard_id=vineyard_id)
        
        # Assert
        assert result == []
    
    @pytest.mark.asyncio
    async def test_list_harvest_lots_empty(
        self,
        service: FruitOriginService,
        mock_harvest_lot_repo: Mock
    ):
        """
        GIVEN winery has no harvest lots
        WHEN list_harvest_lots is called
        THEN it returns empty list
        """
        # Arrange
        winery_id = 1
        mock_harvest_lot_repo.get_by_winery.return_value = []
        
        # Act
        result = await service.list_harvest_lots(winery_id)
        
        # Assert
        assert result == []
    
    # ==================================================================================
    # EDGE CASES & BUSINESS RULES
    # ==================================================================================
    
    @pytest.mark.asyncio
    async def test_create_harvest_lot_cross_winery_vineyard_allowed(
        self,
        service: FruitOriginService,
        mock_harvest_lot_repo: Mock,
        expected_harvest_lot_entity: Mock
    ):
        """
        GIVEN vineyard block belongs to different winery
        WHEN create_harvest_lot is called
        THEN it allows creation (buying grapes scenario)
        
        BUSINESS RULE (ADR-014):
        ✓ Cross-winery vineyard access is ALLOWED
        ✓ Harvest lot still belongs to creating winery
        """
        # Arrange
        winery_id = 1  # Creating winery
        user_id = 42
        harvest_lot_data = HarvestLotCreate(
            block_id=999,  # Block from different winery (allowed)
            code="LOT-PURCHASED",
            harvest_date=date(2025, 3, 15),
            weight_kg=5000.0
        )
        mock_harvest_lot_repo.create.return_value = expected_harvest_lot_entity
        
        # Act
        result = await service.create_harvest_lot(
            winery_id=winery_id,
            user_id=user_id,
            data=harvest_lot_data
        )
        
        # Assert
        # No vineyard validation - just create
        mock_harvest_lot_repo.create.assert_called_once()
        assert result.winery_id == 1  # Belongs to creating winery
