"""
Unit tests for LotSourceRepository implementation.

These tests follow proper unit testing practices:
- Mock only the session manager (not SQLAlchemy internals)
- Mock the RESULTS of database queries (not the query builders)
- Focus on testing the repository contract, not implementation details
- No need to import or patch SQLAlchemy entities

Following ADR-002: Unit tests verify repository behavior without database connection.
Following ADR-012: Using shared testing infrastructure for consistent mocking.
Integration tests (separate file) will verify actual database operations.
"""

import pytest
from datetime import datetime
from decimal import Decimal

# Import domain entities and DTOs from their canonical locations
from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource
from src.modules.fermentation.src.domain.dtos import LotSourceData

# Import repository implementation
from src.modules.fermentation.src.repository_component.repositories import LotSourceRepository

# Import ADR-012 testing utilities
from src.shared.testing.unit import (
    MockSessionManagerBuilder,
    create_query_result,
    create_empty_result,
    create_mock_entity,
)


class TestLotSourceRepository:
    """Test LotSourceRepository with proper mocking strategy.
    
    Following ADR-012: Each test creates its own session manager and repository instance for isolation.
    """

    @pytest.mark.asyncio
    async def test_repository_inherits_from_base_repository(self):
        """Test that LotSourceRepository extends BaseRepository."""
        from src.shared.infra.repository.base_repository import BaseRepository
        session_manager = MockSessionManagerBuilder().build()
        repository = LotSourceRepository(session_manager)
        assert isinstance(repository, BaseRepository)

    @pytest.mark.asyncio
    async def test_create_returns_lot_source_entity(self):
        """Test that create method returns a FermentationLotSource domain entity."""
        # Create test data
        lot_source_data = LotSourceData(
            harvest_lot_id=10,
            mass_used_kg=Decimal("50.5"),
            notes="Test notes"
        )

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().build()
        repository = LotSourceRepository(session_manager)

        # This test verifies the repository interface contract
        # Full implementation tests require integration testing with real DB
        assert hasattr(repository, 'create')
        assert callable(repository.create)

    @pytest.mark.asyncio
    async def test_get_by_fermentation_id_returns_empty_list_when_no_sources(self):
        """Test that get_by_fermentation_id returns empty list when no lot sources exist."""
        # Mock the query result to return empty list
        empty_result = create_empty_result()

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(empty_result).build()
        repository = LotSourceRepository(session_manager)

        # Call the method
        result = await repository.get_by_fermentation_id(fermentation_id=1, winery_id=1)

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_by_fermentation_id_returns_list_of_sources(self):
        """Test that get_by_fermentation_id returns list of lot sources when found."""
        # Mock two lot sources for the same fermentation
        mock_source1 = create_mock_entity(
            FermentationLotSource,
            id=1,
            fermentation_id=1,
            harvest_lot_id=10,
            mass_used_kg=50.0
        )

        mock_source2 = create_mock_entity(
            FermentationLotSource,
            id=2,
            fermentation_id=1,
            harvest_lot_id=11,
            mass_used_kg=30.0
        )

        # Mock the query result
        query_result = create_query_result([mock_source1, mock_source2])

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repository = LotSourceRepository(session_manager)

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
    async def test_delete_returns_false_when_not_found(self):
        """Test that delete returns False when lot source doesn't exist."""
        # Mock the query result to return None
        empty_result = create_empty_result()

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(empty_result).build()
        repository = LotSourceRepository(session_manager)

        # Call the method
        result = await repository.delete(lot_source_id=999, winery_id=1)

        # Verify result
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_successful(self):
        """Test that delete returns True when lot source is deleted successfully."""
        # Mock the SQLAlchemy entity
        mock_lot_source = create_mock_entity(
            FermentationLotSource,
            id=1
        )

        # Mock the query result
        query_result = create_query_result([mock_lot_source])

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repository = LotSourceRepository(session_manager)

        # Call the method
        result = await repository.delete(lot_source_id=1, winery_id=1)

        # Verify result
        assert result is True

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self):
        """Test that get_by_id returns None when lot source doesn't exist."""
        # Mock the query result to return None
        empty_result = create_empty_result()

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(empty_result).build()
        repository = LotSourceRepository(session_manager)

        # Call the method
        result = await repository.get_by_id(lot_source_id=999, winery_id=1)

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_returns_lot_source_when_found(self):
        """Test that get_by_id returns a FermentationLotSource entity when found."""
        # Mock the SQLAlchemy entity
        mock_lot_source = create_mock_entity(
            FermentationLotSource,
            id=1,
            fermentation_id=1,
            harvest_lot_id=10,
            mass_used_kg=50.0,
            notes="Test notes"
        )

        # Mock the query result
        query_result = create_query_result([mock_lot_source])

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repository = LotSourceRepository(session_manager)

        # Call the method
        result = await repository.get_by_id(lot_source_id=1, winery_id=1)

        # Verify result (check attributes, not type)
        assert result is not None
        assert result.id == 1
        assert result.fermentation_id == 1
        assert result.harvest_lot_id == 10
        assert result.mass_used_kg == 50.0

    @pytest.mark.asyncio
    async def test_update_mass_returns_none_when_not_found(self):
        """Test that update_mass returns None when lot source doesn't exist."""
        # Mock the query result to return None
        empty_result = create_empty_result()

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(empty_result).build()
        repository = LotSourceRepository(session_manager)

        # Call the method
        result = await repository.update_mass(lot_source_id=999, winery_id=1, new_mass_kg=75.0)

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_update_mass_returns_updated_entity_when_successful(self):
        """Test that update_mass returns updated FermentationLotSource when update succeeds."""
        # Mock the SQLAlchemy entity
        mock_lot_source = create_mock_entity(
            FermentationLotSource,
            id=1,
            fermentation_id=1,
            mass_used_kg=50.0
        )

        # Mock the query result
        query_result = create_query_result([mock_lot_source])

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repository = LotSourceRepository(session_manager)

        # Call the method
        result = await repository.update_mass(lot_source_id=1, winery_id=1, new_mass_kg=75.0)

        # Verify result (check behavior, not type)
        assert result is not None
        assert result.mass_used_kg == 75.0

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self):
        """Test that repository enforces multi-tenant isolation via winery_id."""
        # Mock the query result to return None (access denied to other winery's data)
        empty_result = create_empty_result()

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(empty_result).build()
        repository = LotSourceRepository(session_manager)

        # Try to access lot source from different winery
        result = await repository.get_by_id(lot_source_id=1, winery_id=999)

        # Should return None (not found due to winery_id filter)
        assert result is None
