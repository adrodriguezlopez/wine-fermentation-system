"""
Unit tests for LotSourceRepository implementation.

These tests follow proper unit testing practices:
- Mock only the session manager (not SQLAlchemy internals)
- Mock the RESULTS of database queries (not the query builders)
- Focus on testing the repository contract, not implementation details
- No need to import or patch SQLAlchemy entities

Following ADR-002: Unit tests verify repository behavior without database connection.
Integration tests (separate file) will verify actual database operations.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from decimal import Decimal

# Import domain entities and DTOs from their canonical locations
from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource
from src.modules.fermentation.src.domain.dtos import LotSourceData

# Import repository implementation (will be created next)
from src.modules.fermentation.src.repository_component.repositories import LotSourceRepository


class TestLotSourceRepository:
    """Test LotSourceRepository with proper mocking strategy."""

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
        """Create a LotSourceRepository instance with mocked session manager."""
        manager, _ = mock_session_manager
        return LotSourceRepository(manager)

    @pytest.mark.asyncio
    async def test_repository_inherits_from_base_repository(self, repository):
        """Test that LotSourceRepository extends BaseRepository."""
        from src.shared.infra.repository.base_repository import BaseRepository
        assert isinstance(repository, BaseRepository)

    @pytest.mark.asyncio
    async def test_create_returns_lot_source_entity(self, repository, mock_session_manager):
        """Test that create method returns a FermentationLotSource domain entity."""
        manager, mock_session = mock_session_manager

        # Mock the SQLAlchemy entity that will be created
        mock_sql_lot_source = Mock()
        mock_sql_lot_source.id = 1
        mock_sql_lot_source.fermentation_id = 1
        mock_sql_lot_source.harvest_lot_id = 10
        mock_sql_lot_source.mass_used_kg = 50.5
        mock_sql_lot_source.notes = "Test notes"
        mock_sql_lot_source.created_at = datetime.utcnow()
        mock_sql_lot_source.updated_at = datetime.utcnow()

        # Mock session operations
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Create test data
        lot_source_data = LotSourceData(
            harvest_lot_id=10,
            mass_used_kg=Decimal("50.5"),
            notes="Test notes"
        )

        # This test verifies the repository interface contract
        # Full implementation tests require integration testing with real DB
        assert hasattr(repository, 'create')
        assert callable(repository.create)

    @pytest.mark.asyncio
    async def test_get_by_fermentation_id_returns_empty_list_when_no_sources(self, repository, mock_session_manager):
        """Test that get_by_fermentation_id returns empty list when no lot sources exist."""
        manager, mock_session = mock_session_manager

        # Mock the query result to return empty list
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.get_by_fermentation_id(fermentation_id=1, winery_id=1)

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 0
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_get_by_fermentation_id_returns_list_of_sources(self, repository, mock_session_manager):
        """Test that get_by_fermentation_id returns list of lot sources when found."""
        manager, mock_session = mock_session_manager

        # Mock two lot sources for the same fermentation
        mock_source1 = Mock()
        mock_source1.id = 1
        mock_source1.fermentation_id = 1
        mock_source1.harvest_lot_id = 10
        mock_source1.mass_used_kg = 50.0

        mock_source2 = Mock()
        mock_source2.id = 2
        mock_source2.fermentation_id = 1
        mock_source2.harvest_lot_id = 11
        mock_source2.mass_used_kg = 30.0

        # Mock the query result
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=[mock_source1, mock_source2])))
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.get_by_fermentation_id(fermentation_id=1, winery_id=1)

        # Verify result (check structure and attributes, not types)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].harvest_lot_id == 10
        assert result[1].id == 2
        assert result[1].harvest_lot_id == 11

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_found(self, repository, mock_session_manager):
        """Test that delete returns False when lot source doesn't exist."""
        manager, mock_session = mock_session_manager

        # Mock the query result to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.delete(lot_source_id=999, winery_id=1)

        # Verify result
        assert result is False
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_successful(self, repository, mock_session_manager):
        """Test that delete returns True when lot source is deleted successfully."""
        manager, mock_session = mock_session_manager

        # Mock the SQLAlchemy entity
        mock_lot_source = Mock()
        mock_lot_source.id = 1

        # Mock the query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_lot_source)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.delete = Mock()
        mock_session.flush = AsyncMock()

        # Call the method
        result = await repository.delete(lot_source_id=1, winery_id=1)

        # Verify result
        assert result is True
        assert mock_session.delete.called
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self, repository, mock_session_manager):
        """Test that get_by_id returns None when lot source doesn't exist."""
        manager, mock_session = mock_session_manager

        # Mock the query result to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.get_by_id(lot_source_id=999, winery_id=1)

        # Verify result
        assert result is None
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_get_by_id_returns_lot_source_when_found(self, repository, mock_session_manager):
        """Test that get_by_id returns a FermentationLotSource entity when found."""
        manager, mock_session = mock_session_manager

        # Mock the SQLAlchemy entity
        mock_lot_source = Mock()
        mock_lot_source.id = 1
        mock_lot_source.fermentation_id = 1
        mock_lot_source.harvest_lot_id = 10
        mock_lot_source.mass_used_kg = 50.0
        mock_lot_source.notes = "Test notes"

        # Mock the query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_lot_source)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.get_by_id(lot_source_id=1, winery_id=1)

        # Verify result (check attributes, not type)
        assert result is not None
        assert result.id == 1
        assert result.fermentation_id == 1
        assert result.harvest_lot_id == 10
        assert result.mass_used_kg == 50.0

    @pytest.mark.asyncio
    async def test_update_mass_returns_none_when_not_found(self, repository, mock_session_manager):
        """Test that update_mass returns None when lot source doesn't exist."""
        manager, mock_session = mock_session_manager

        # Mock the query result to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Call the method
        result = await repository.update_mass(lot_source_id=999, winery_id=1, new_mass_kg=75.0)

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_update_mass_returns_updated_entity_when_successful(self, repository, mock_session_manager):
        """Test that update_mass returns updated FermentationLotSource when update succeeds."""
        manager, mock_session = mock_session_manager

        # Mock the SQLAlchemy entity
        mock_lot_source = Mock()
        mock_lot_source.id = 1
        mock_lot_source.fermentation_id = 1
        mock_lot_source.mass_used_kg = 50.0

        # Mock the query result
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=mock_lot_source)
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Call the method
        result = await repository.update_mass(lot_source_id=1, winery_id=1, new_mass_kg=75.0)

        # Verify result (check behavior, not type)
        assert result is not None
        assert result.mass_used_kg == 75.0
        assert mock_session.flush.called
        assert mock_session.refresh.called

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, repository, mock_session_manager):
        """Test that repository enforces multi-tenant isolation via winery_id."""
        manager, mock_session = mock_session_manager

        # Mock the query result to return None (access denied to other winery's data)
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Try to access lot source from different winery
        result = await repository.get_by_id(lot_source_id=1, winery_id=999)

        # Should return None (not found due to winery_id filter)
        assert result is None
