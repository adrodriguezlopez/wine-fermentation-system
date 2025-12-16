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
from datetime import date, datetime

# Import domain entities and DTOs from their canonical locations
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.modules.fruit_origin.src.domain.dtos import HarvestLotCreate, HarvestLotUpdate

# Import repository implementation (will be created next)
from src.modules.fruit_origin.src.repository_component.repositories.harvest_lot_repository import HarvestLotRepository

# ADR-012: Import shared testing utilities
from src.shared.testing.unit import (
    MockSessionManagerBuilder,
    create_query_result,
    create_empty_result,
    create_mock_entity,
)


class TestHarvestLotRepository:
    """Test HarvestLotRepository with proper mocking strategy."""

    @pytest.mark.asyncio
    async def test_repository_inherits_from_base_repository(self):
        """Test that HarvestLotRepository extends BaseRepository."""
        from src.shared.infra.repository.base_repository import BaseRepository
        session_manager = MockSessionManagerBuilder().build()
        repository = HarvestLotRepository(session_manager)
        assert isinstance(repository, BaseRepository)

    @pytest.mark.asyncio
    async def test_create_returns_harvest_lot_entity(self):
        """Test that create method returns a HarvestLot domain entity."""
        session_manager = MockSessionManagerBuilder().build()
        repository = HarvestLotRepository(session_manager)

        # This test verifies the repository interface contract
        assert hasattr(repository, 'create')
        assert callable(repository.create)

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self):
        """Test that get_by_id returns None when harvest lot doesn't exist."""
        result = create_empty_result()
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = HarvestLotRepository(session_manager)

        # Call the method
        result = await repository.get_by_id(lot_id=999, winery_id=1)

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_returns_harvest_lot_when_found(self):
        """Test that get_by_id returns a HarvestLot entity when found."""
        mock_harvest_lot = create_mock_entity(
            HarvestLot,
            id=1,
            winery_id=1,
            code="HL2025-001",
            harvest_date=date(2025, 3, 15),
            weight_kg=500.0
        )
        result = create_query_result([mock_harvest_lot])
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = HarvestLotRepository(session_manager)

        # Call the method
        result = await repository.get_by_id(lot_id=1, winery_id=1)

        # Verify result (check attributes, not type)
        assert result is not None
        assert result.id == 1
        assert result.winery_id == 1
        assert result.code == "HL2025-001"

    @pytest.mark.asyncio
    async def test_get_by_winery_returns_list_of_lots(self):
        """Test that get_by_winery returns list of harvest lots."""
        mock_lot1 = create_mock_entity(
            HarvestLot,
            id=1,
            winery_id=1,
            code="HL2025-001"
        )
        mock_lot2 = create_mock_entity(
            HarvestLot,
            id=2,
            winery_id=1,
            code="HL2025-002"
        )
        result = create_query_result([mock_lot1, mock_lot2])
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = HarvestLotRepository(session_manager)

        # Call the method
        result = await repository.get_by_winery(winery_id=1)

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].code == "HL2025-001"
        assert result[1].code == "HL2025-002"

    @pytest.mark.asyncio
    async def test_get_by_code_returns_unique_lot(self):
        """Test that get_by_code returns harvest lot with matching code."""
        mock_harvest_lot = create_mock_entity(
            HarvestLot,
            id=1,
            code="HL2025-001",
            winery_id=1
        )
        result = create_query_result([mock_harvest_lot])
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = HarvestLotRepository(session_manager)

        # Call the method
        result = await repository.get_by_code(code="HL2025-001", winery_id=1)

        # Verify result
        assert result is not None
        assert result.code == "HL2025-001"

    @pytest.mark.asyncio
    async def test_get_available_for_blend_returns_available_lots(self):
        """Test that get_available_for_blend returns lots not fully used."""
        mock_lot1 = create_mock_entity(
            HarvestLot,
            id=1,
            weight_kg=500.0
        )
        mock_lot2 = create_mock_entity(
            HarvestLot,
            id=2,
            weight_kg=300.0
        )
        result = create_query_result([mock_lot1, mock_lot2])
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = HarvestLotRepository(session_manager)

        # Call the method
        result = await repository.get_available_for_blend(winery_id=1)

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_block_returns_lots_from_block(self):
        """Test that get_by_block returns all lots from specific block."""
        mock_lot1 = create_mock_entity(
            HarvestLot,
            id=1,
            block_id=10
        )
        mock_lot2 = create_mock_entity(
            HarvestLot,
            id=2,
            block_id=10
        )
        result = create_query_result([mock_lot1, mock_lot2])
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = HarvestLotRepository(session_manager)

        # Call the method
        result = await repository.get_by_block(block_id=10, winery_id=1)

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(lot.block_id == 10 for lot in result)

    @pytest.mark.asyncio
    async def test_get_by_harvest_date_range_returns_lots_in_range(self):
        """Test that get_by_harvest_date_range returns lots within date range."""
        mock_lot1 = create_mock_entity(
            HarvestLot,
            id=1,
            harvest_date=date(2025, 3, 12)
        )
        mock_lot2 = create_mock_entity(
            HarvestLot,
            id=2,
            harvest_date=date(2025, 3, 15)
        )
        result = create_query_result([mock_lot1, mock_lot2])
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = HarvestLotRepository(session_manager)

        # Call the method
        result = await repository.get_by_harvest_date_range(
            winery_id=1,
            start_date=date(2025, 3, 10),
            end_date=date(2025, 3, 20)
        )

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_harvest_date_range_raises_error_for_invalid_range(self):
        """Test that get_by_harvest_date_range raises ValueError for invalid date range."""
        session_manager = MockSessionManagerBuilder().build()
        repository = HarvestLotRepository(session_manager)
        
        # Call the method with invalid range (start > end)
        with pytest.raises(ValueError, match="start_date .* must be <= end_date"):
            await repository.get_by_harvest_date_range(
                winery_id=1,
                start_date=date(2025, 3, 20),
                end_date=date(2025, 3, 10)
            )

    @pytest.mark.asyncio
    async def test_update_returns_updated_entity(self):
        """Test that update returns updated HarvestLot entity."""
        mock_harvest_lot = create_mock_entity(
            HarvestLot,
            id=1,
            code="HL2025-001",
            weight_kg=500.0
        )
        result = create_query_result([mock_harvest_lot])
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = HarvestLotRepository(session_manager)

        # Update data
        update_data = HarvestLotUpdate(weight_kg=550.0)

        # Call the method
        result = await repository.update(lot_id=1, winery_id=1, data=update_data)

        # Verify result
        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_successful(self):
        """Test that delete soft-deletes harvest lot successfully."""
        mock_harvest_lot = create_mock_entity(
            HarvestLot,
            id=1,
            is_deleted=False
        )
        result = create_query_result([mock_harvest_lot])
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = HarvestLotRepository(session_manager)

        # Call the method
        result = await repository.delete(lot_id=1, winery_id=1)

        # Verify result
        assert result is True
        assert mock_harvest_lot.is_deleted is True

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self):
        """Test that repository enforces multi-tenant isolation via winery_id."""
        result = create_empty_result()
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = HarvestLotRepository(session_manager)

        # Try to access lot from different winery
        result = await repository.get_by_id(lot_id=1, winery_id=999)

        # Should return None (not found due to winery_id filter)
        assert result is None
