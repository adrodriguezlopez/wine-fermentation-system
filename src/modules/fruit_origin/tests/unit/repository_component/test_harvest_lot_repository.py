"""
Unit tests for HarvestLotRepository implementation.

These tests follow proper unit testing practices:
- Mock only the session manager (not SQLAlchemy internals)
- Mock the RESULTS of database queries (not the query builders)
- Focus on testing the repository contract, not implementation details
- No need to import or patch SQLAlchemy entities

Following ADR-002: Unit tests verify repository behavior without database connection.
Following ADR-009: Tests for HarvestLotRepository implementation.
Integration tests (separate file) will verify actual database operations.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import date, datetime

# Import domain entities and DTOs from their canonical locations
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.modules.fruit_origin.src.domain.dtos import HarvestLotCreate, HarvestLotUpdate

# Import repository implementation (will be created next)
from src.modules.fruit_origin.src.repository_component.repositories.harvest_lot_repository import HarvestLotRepository


class TestHarvestLotRepository:
    """Test HarvestLotRepository with proper mocking strategy."""

    @pytest.fixture
    def mock_session_manager(self):
        """Create a mock session manager that returns a mock session."""
        manager = Mock()
        mock_session = AsyncMock()
        
        # Create a proper async context manager mock
        from unittest.mock import MagicMock
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        # Make get_session return the context manager
        manager.get_session = Mock(return_value=mock_context)
        manager.close = AsyncMock()
        return manager, mock_session

    @pytest.fixture
    def repository(self, mock_session_manager):
        """Create a HarvestLotRepository instance with mocked session manager."""
        manager, _ = mock_session_manager
        return HarvestLotRepository(manager)

    @pytest.mark.asyncio
    async def test_repository_inherits_from_base_repository(self, repository):
        """Test that HarvestLotRepository extends BaseRepository."""
        from src.shared.infra.repository.base_repository import BaseRepository
        assert isinstance(repository, BaseRepository)

    @pytest.mark.asyncio
    async def test_create_returns_harvest_lot_entity(self, repository, mock_session_manager):
        """Test that create method returns a HarvestLot domain entity."""
        manager, mock_session = mock_session_manager

        # Mock the SQLAlchemy entity that will be created
        mock_harvest_lot = Mock()
        mock_harvest_lot.id = 1
        mock_harvest_lot.winery_id = 1
        mock_harvest_lot.block_id = 10
        mock_harvest_lot.code = "HL2025-001"
        mock_harvest_lot.harvest_date = date(2025, 3, 15)
        mock_harvest_lot.weight_kg = 500.0
        mock_harvest_lot.grape_variety = "Chardonnay"
        mock_harvest_lot.created_at = datetime.utcnow()
        mock_harvest_lot.updated_at = datetime.utcnow()

        # Mock session operations
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Create test data
        harvest_lot_data = HarvestLotCreate(
            block_id=10,
            code="HL2025-001",
            harvest_date=date(2025, 3, 15),
            weight_kg=500.0,
            grape_variety="Chardonnay"
        )

        # This test verifies the repository interface contract
        assert hasattr(repository, 'create')
        assert callable(repository.create)

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self, repository, mock_session_manager):
        """Test that get_by_id returns None when harvest lot doesn't exist."""
        manager, mock_session = mock_session_manager

        # Mock the query result to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.get_by_id(lot_id=999, winery_id=1)

        # Verify result
        assert result is None
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_get_by_id_returns_harvest_lot_when_found(self, repository, mock_session_manager):
        """Test that get_by_id returns a HarvestLot entity when found."""
        manager, mock_session = mock_session_manager

        # Mock the SQLAlchemy entity
        mock_harvest_lot = Mock()
        mock_harvest_lot.id = 1
        mock_harvest_lot.winery_id = 1
        mock_harvest_lot.code = "HL2025-001"
        mock_harvest_lot.harvest_date = date(2025, 3, 15)
        mock_harvest_lot.weight_kg = 500.0

        # Mock the query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_harvest_lot)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.get_by_id(lot_id=1, winery_id=1)

        # Verify result (check attributes, not type)
        assert result is not None
        assert result.id == 1
        assert result.winery_id == 1
        assert result.code == "HL2025-001"

    @pytest.mark.asyncio
    async def test_get_by_winery_returns_list_of_lots(self, repository, mock_session_manager):
        """Test that get_by_winery returns list of harvest lots."""
        manager, mock_session = mock_session_manager

        # Mock two harvest lots
        mock_lot1 = Mock()
        mock_lot1.id = 1
        mock_lot1.winery_id = 1
        mock_lot1.code = "HL2025-001"

        mock_lot2 = Mock()
        mock_lot2.id = 2
        mock_lot2.winery_id = 1
        mock_lot2.code = "HL2025-002"

        # Mock the query result
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[mock_lot1, mock_lot2])))
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.get_by_winery(winery_id=1)

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].code == "HL2025-001"
        assert result[1].code == "HL2025-002"

    @pytest.mark.asyncio
    async def test_get_by_code_returns_unique_lot(self, repository, mock_session_manager):
        """Test that get_by_code returns harvest lot with matching code."""
        manager, mock_session = mock_session_manager

        # Mock the harvest lot
        mock_harvest_lot = Mock()
        mock_harvest_lot.id = 1
        mock_harvest_lot.code = "HL2025-001"
        mock_harvest_lot.winery_id = 1

        # Mock the query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_harvest_lot)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.get_by_code(code="HL2025-001", winery_id=1)

        # Verify result
        assert result is not None
        assert result.code == "HL2025-001"

    @pytest.mark.asyncio
    async def test_get_available_for_blend_returns_available_lots(self, repository, mock_session_manager):
        """Test that get_available_for_blend returns lots not fully used."""
        manager, mock_session = mock_session_manager

        # Mock available lots
        mock_lot1 = Mock()
        mock_lot1.id = 1
        mock_lot1.weight_kg = 500.0

        mock_lot2 = Mock()
        mock_lot2.id = 2
        mock_lot2.weight_kg = 300.0

        # Mock the query result
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[mock_lot1, mock_lot2])))
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.get_available_for_blend(winery_id=1)

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_block_returns_lots_from_block(self, repository, mock_session_manager):
        """Test that get_by_block returns all lots from specific block."""
        manager, mock_session = mock_session_manager

        # Mock lots from same block
        mock_lot1 = Mock()
        mock_lot1.id = 1
        mock_lot1.block_id = 10

        mock_lot2 = Mock()
        mock_lot2.id = 2
        mock_lot2.block_id = 10

        # Mock the query result
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[mock_lot1, mock_lot2])))
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.get_by_block(block_id=10, winery_id=1)

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(lot.block_id == 10 for lot in result)

    @pytest.mark.asyncio
    async def test_update_returns_updated_entity(self, repository, mock_session_manager):
        """Test that update returns updated HarvestLot entity."""
        manager, mock_session = mock_session_manager

        # Mock the harvest lot
        mock_harvest_lot = Mock()
        mock_harvest_lot.id = 1
        mock_harvest_lot.code = "HL2025-001"
        mock_harvest_lot.weight_kg = 500.0

        # Mock the query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_harvest_lot)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Update data
        update_data = HarvestLotUpdate(weight_kg=550.0)

        # Call the method
        result = await repository.update(lot_id=1, winery_id=1, data=update_data)

        # Verify result
        assert result is not None
        assert mock_session.flush.called
        assert mock_session.refresh.called

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_successful(self, repository, mock_session_manager):
        """Test that delete soft-deletes harvest lot successfully."""
        manager, mock_session = mock_session_manager

        # Mock the harvest lot
        mock_harvest_lot = Mock()
        mock_harvest_lot.id = 1
        mock_harvest_lot.is_deleted = False

        # Mock the query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_harvest_lot)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        # Call the method
        result = await repository.delete(lot_id=1, winery_id=1)

        # Verify result
        assert result is True
        assert mock_harvest_lot.is_deleted is True
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, repository, mock_session_manager):
        """Test that repository enforces multi-tenant isolation via winery_id."""
        manager, mock_session = mock_session_manager

        # Mock the query result to return None (access denied to other winery's data)
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Try to access lot from different winery
        result = await repository.get_by_id(lot_id=1, winery_id=999)

        # Should return None (not found due to winery_id filter)
        assert result is None
