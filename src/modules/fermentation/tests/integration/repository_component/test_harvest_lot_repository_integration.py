"""
Integration tests for HarvestLotRepository.

These tests validate repository operations against real SQLite database,
ensuring that:
- Create operations persist correctly with HarvestLotCreate DTO
- Get operations return correct data with multi-tenant winery_id scoping
- Query methods filter correctly (by winery, by code, by block, by date range)
- get_available_for_blend() filters correctly by availability and weight
- Update operations persist correctly
- Delete operations soft-delete correctly
- SQLAlchemy mappings work with JOINs across VineyardBlock and Vineyard
- Transactions and rollbacks work properly
- Multi-tenant isolation works correctly

Database: SQLite in-memory (shared cache)

NOTE: This tests ONLY HarvestLotRepository operations from fruit_origin module.
"""

import pytest
from datetime import date, timedelta
from sqlalchemy import select

from src.modules.fruit_origin.src.domain.dtos import HarvestLotCreate, HarvestLotUpdate

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestHarvestLotRepositoryCRUD:
    """Integration tests for basic create and get operations."""

    @pytest.mark.asyncio
    async def test_create_harvest_lot_persists_to_database(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
        db_session,
    ):
        """
        Test that create() persists HarvestLot to database.
        
        GIVEN a valid HarvestLotCreate DTO
        WHEN create() is called
        THEN the harvest lot should be persisted with ID assigned
        AND should be retrievable from the database
        """
        # Arrange
        HarvestLot = test_models['HarvestLot']
        
        harvest_data = HarvestLotCreate(
            block_id=test_vineyard_block.id,
            code="HL2024TEST",
            harvest_date=date(2024, 9, 20),
            weight_kg=2000.0,
            brix_at_harvest=25.0,
            grape_variety="Merlot",
            notes="Test harvest lot"
        )
        
        # Act
        created = await harvest_lot_repository.create(
            winery_id=test_winery.id,
            data=harvest_data
        )
        await db_session.flush()
        
        # Assert
        assert created.id is not None, "ID should be assigned after create"
        assert created.winery_id == test_winery.id
        assert created.code == "HL2024TEST"
        assert created.weight_kg == 2000.0
        assert created.grape_variety == "Merlot"
        
        # Verify persistence
        result = await db_session.execute(
            select(HarvestLot).where(HarvestLot.id == created.id)
        )
        persisted = result.scalar_one()
        assert persisted.code == "HL2024TEST"
        assert persisted.is_deleted == False

    @pytest.mark.asyncio
    async def test_get_by_id_returns_harvest_lot_with_winery_scoping(
        self,
        harvest_lot_repository,
        test_harvest_lot,
        test_winery,
    ):
        """
        Test that get_by_id() requires winery_id for multi-tenant security.
        
        GIVEN a harvest lot exists
        WHEN get_by_id() is called with correct winery_id
        THEN harvest lot should be returned
        """
        # Act
        retrieved = await harvest_lot_repository.get_by_id(
            lot_id=test_harvest_lot.id,
            winery_id=test_winery.id
        )
        
        # Assert
        assert retrieved is not None
        assert retrieved.id == test_harvest_lot.id
        assert retrieved.code == test_harvest_lot.code
        assert retrieved.winery_id == test_winery.id

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self,
        harvest_lot_repository,
        test_winery,
    ):
        """
        Test that get_by_id() returns None for non-existent ID.
        
        GIVEN a non-existent harvest lot ID
        WHEN get_by_id() is called
        THEN None should be returned
        """
        # Act
        result = await harvest_lot_repository.get_by_id(
            lot_id=99999,
            winery_id=test_winery.id
        )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_enforces_winery_isolation(
        self,
        test_models,
        harvest_lot_repository,
        test_harvest_lot,
        db_session,
    ):
        """
        Test that get_by_id() enforces multi-tenant isolation.
        
        GIVEN a harvest lot exists for winery 1
        WHEN get_by_id() is called with different winery_id
        THEN None should be returned (tenant isolation)
        """
        # Act - Try to access with wrong winery ID
        result = await harvest_lot_repository.get_by_id(
            lot_id=test_harvest_lot.id,
            winery_id=99999  # Different winery
        )
        
        # Assert
        assert result is None, "Should not return lot from different winery"


class TestHarvestLotRepositoryQueries:
    """Integration tests for query methods."""

    @pytest.mark.asyncio
    async def test_get_by_winery_returns_all_lots_for_winery(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
        db_session,
    ):
        """
        Test that get_by_winery() returns all lots for a winery.
        
        GIVEN multiple harvest lots exist for a winery
        WHEN get_by_winery() is called
        THEN all lots should be returned
        """
        # Arrange - Create additional lots
        HarvestLot = test_models['HarvestLot']
        
        lot1 = HarvestLot(
            winery_id=test_winery.id,
            block_id=test_vineyard_block.id,
            code="HL2024A",
            harvest_date=date(2024, 9, 1),
            weight_kg=1000.0,
            brix_at_harvest=23.0,
            grape_variety="Chardonnay",
            is_deleted=False
        )
        lot2 = HarvestLot(
            winery_id=test_winery.id,
            block_id=test_vineyard_block.id,
            code="HL2024B",
            harvest_date=date(2024, 9, 10),
            weight_kg=1500.0,
            brix_at_harvest=24.0,
            grape_variety="Pinot Noir",
            is_deleted=False
        )
        db_session.add_all([lot1, lot2])
        await db_session.flush()
        
        # Act
        lots = await harvest_lot_repository.get_by_winery(winery_id=test_winery.id)
        
        # Assert - Should include test_harvest_lot from fixture + 2 new ones
        assert len(lots) >= 2
        codes = [lot.code for lot in lots]
        assert "HL2024A" in codes
        assert "HL2024B" in codes

    @pytest.mark.asyncio
    async def test_get_by_code_returns_unique_lot(
        self,
        harvest_lot_repository,
        test_harvest_lot,
        test_winery,
    ):
        """
        Test that get_by_code() returns lot by unique code.
        
        GIVEN a harvest lot exists with code "HL2024001"
        WHEN get_by_code() is called
        THEN the correct lot should be returned
        """
        # Act
        lot = await harvest_lot_repository.get_by_code(
            code="HL2024001",
            winery_id=test_winery.id
        )
        
        # Assert
        assert lot is not None
        assert lot.id == test_harvest_lot.id
        assert lot.code == "HL2024001"

    @pytest.mark.asyncio
    async def test_get_by_code_enforces_winery_scoping(
        self,
        harvest_lot_repository,
        test_harvest_lot,
    ):
        """
        Test that get_by_code() enforces multi-tenant isolation.
        
        GIVEN a harvest lot exists for winery 1
        WHEN get_by_code() is called with different winery_id
        THEN None should be returned
        """
        # Act
        lot = await harvest_lot_repository.get_by_code(
            code="HL2024001",
            winery_id=99999  # Different winery
        )
        
        # Assert
        assert lot is None

    @pytest.mark.asyncio
    async def test_get_by_block_returns_lots_from_specific_block(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
        test_harvest_lot,  # Add this fixture to ensure a lot exists
        db_session,
    ):
        """
        Test that get_by_block() returns lots from specific vineyard block.
        
        GIVEN multiple harvest lots exist in different blocks
        WHEN get_by_block() is called
        THEN only lots from specified block should be returned
        """
        # Arrange - Create another block and lot
        Vineyard = test_models['Vineyard']
        VineyardBlock = test_models['VineyardBlock']
        HarvestLot = test_models['HarvestLot']
        
        # Get existing vineyard
        vineyard_result = await db_session.execute(
            select(Vineyard).where(Vineyard.winery_id == test_winery.id)
        )
        vineyard = vineyard_result.scalar_one()
        
        # Create second block
        block2 = VineyardBlock(
            vineyard_id=vineyard.id,
            code="BLK002",
            soil_type="Sandy",
            area_ha=3.0,
            is_deleted=False
        )
        db_session.add(block2)
        await db_session.flush()
        
        # Create lot in second block
        lot_block2 = HarvestLot(
            winery_id=test_winery.id,
            block_id=block2.id,
            code="HL2024BLOCK2",
            harvest_date=date(2024, 9, 15),
            weight_kg=1200.0,
            brix_at_harvest=23.5,
            grape_variety="Syrah",
            is_deleted=False
        )
        db_session.add(lot_block2)
        await db_session.flush()
        
        # Act - Query for first block
        lots = await harvest_lot_repository.get_by_block(
            block_id=test_vineyard_block.id,
            winery_id=test_winery.id
        )
        
        # Assert
        assert len(lots) >= 1
        for lot in lots:
            assert lot.block_id == test_vineyard_block.id
        
        # Verify lot from block2 is not included
        codes = [lot.code for lot in lots]
        assert "HL2024BLOCK2" not in codes

    @pytest.mark.asyncio
    async def test_get_by_harvest_date_range_filters_correctly(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
        test_harvest_lot,  # Add this fixture to ensure the lot from fixture exists
        db_session,
    ):
        """
        Test that get_by_harvest_date_range() filters by date range.
        
        GIVEN harvest lots with different harvest dates
        WHEN get_by_harvest_date_range() is called with date range
        THEN only lots within range should be returned
        """
        # Arrange - Create lots with different dates
        HarvestLot = test_models['HarvestLot']
        
        lot_early = HarvestLot(
            winery_id=test_winery.id,
            block_id=test_vineyard_block.id,
            code="HL2024EARLY",
            harvest_date=date(2024, 8, 15),
            weight_kg=1000.0,
            brix_at_harvest=22.0,
            grape_variety="Early Variety",
            is_deleted=False
        )
        lot_late = HarvestLot(
            winery_id=test_winery.id,
            block_id=test_vineyard_block.id,
            code="HL2024LATE",
            harvest_date=date(2024, 10, 15),
            weight_kg=1000.0,
            brix_at_harvest=25.0,
            grape_variety="Late Variety",
            is_deleted=False
        )
        db_session.add_all([lot_early, lot_late])
        await db_session.flush()
        
        # Act - Query for September only
        lots = await harvest_lot_repository.get_by_harvest_date_range(
            winery_id=test_winery.id,
            start_date=date(2024, 9, 1),
            end_date=date(2024, 9, 30)
        )
        
        # Assert - Should include test_harvest_lot (9/15) but not early or late
        codes = [lot.code for lot in lots]
        assert "HL2024001" in codes  # From fixture (9/15)
        assert "HL2024EARLY" not in codes  # 8/15 - before range
        assert "HL2024LATE" not in codes  # 10/15 - after range

    @pytest.mark.asyncio
    async def test_get_available_for_blend_filters_by_weight(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
        db_session,
    ):
        """
        Test that get_available_for_blend() filters by minimum weight.
        
        GIVEN harvest lots with different weights
        WHEN get_available_for_blend() is called with min_weight_kg
        THEN only lots with sufficient weight should be returned
        """
        # Arrange - Create lots with different weights
        HarvestLot = test_models['HarvestLot']
        
        lot_small = HarvestLot(
            winery_id=test_winery.id,
            block_id=test_vineyard_block.id,
            code="HL2024SMALL",
            harvest_date=date(2024, 9, 15),
            weight_kg=50.0,  # Below minimum
            brix_at_harvest=23.0,
            grape_variety="Small Lot",
            is_deleted=False
        )
        lot_large = HarvestLot(
            winery_id=test_winery.id,
            block_id=test_vineyard_block.id,
            code="HL2024LARGE",
            harvest_date=date(2024, 9, 15),
            weight_kg=2000.0,  # Above minimum
            brix_at_harvest=24.0,
            grape_variety="Large Lot",
            is_deleted=False
        )
        db_session.add_all([lot_small, lot_large])
        await db_session.flush()
        
        # Act - Query for lots with at least 100kg
        lots = await harvest_lot_repository.get_available_for_blend(
            winery_id=test_winery.id,
            min_weight_kg=100.0
        )
        
        # Assert
        codes = [lot.code for lot in lots]
        assert "HL2024LARGE" in codes  # 2000kg > 100kg
        assert "HL2024SMALL" not in codes  # 50kg < 100kg
        
        # Verify all returned lots meet minimum
        for lot in lots:
            assert lot.weight_kg >= 100.0


class TestHarvestLotRepositoryUpdateDelete:
    """Integration tests for update and delete operations."""

    @pytest.mark.asyncio
    async def test_update_modifies_harvest_lot_fields(
        self,
        test_models,
        harvest_lot_repository,
        test_harvest_lot,
        test_winery,
        db_session,
    ):
        """
        Test that update() modifies harvest lot fields.
        
        GIVEN a harvest lot exists
        WHEN update() is called with HarvestLotUpdate DTO
        THEN the lot should be updated in the database
        """
        # Arrange
        HarvestLot = test_models['HarvestLot']
        update_data = HarvestLotUpdate(
            weight_kg=1800.0,
            brix_at_harvest=25.5,
            notes="Updated notes for lot"
        )
        
        # Act
        updated = await harvest_lot_repository.update(
            lot_id=test_harvest_lot.id,
            winery_id=test_winery.id,
            data=update_data
        )
        await db_session.flush()
        
        # Assert
        assert updated is not None
        assert updated.weight_kg == 1800.0
        assert updated.brix_at_harvest == 25.5
        assert updated.notes == "Updated notes for lot"
        
        # Verify persistence
        result = await db_session.execute(
            select(HarvestLot).where(HarvestLot.id == test_harvest_lot.id)
        )
        persisted = result.scalar_one()
        assert persisted.weight_kg == 1800.0

    @pytest.mark.asyncio
    async def test_update_enforces_winery_isolation(
        self,
        harvest_lot_repository,
        test_harvest_lot,
    ):
        """
        Test that update() enforces multi-tenant isolation.
        
        GIVEN a harvest lot exists for winery 1
        WHEN update() is called with different winery_id
        THEN None should be returned (no update)
        """
        # Arrange
        update_data = HarvestLotUpdate(weight_kg=2000.0)
        
        # Act
        result = await harvest_lot_repository.update(
            lot_id=test_harvest_lot.id,
            winery_id=99999,  # Different winery
            data=update_data
        )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_soft_deletes_harvest_lot(
        self,
        test_models,
        harvest_lot_repository,
        test_harvest_lot,
        test_winery,
        db_session,
    ):
        """
        Test that delete() soft-deletes harvest lot (sets is_deleted=True).
        
        GIVEN a harvest lot exists
        WHEN delete() is called
        THEN the lot should be soft-deleted (not physically removed)
        """
        # Arrange
        HarvestLot = test_models['HarvestLot']
        
        # Act
        success = await harvest_lot_repository.delete(
            lot_id=test_harvest_lot.id,
            winery_id=test_winery.id
        )
        await db_session.flush()
        
        # Assert
        assert success is True
        
        # Verify soft delete (record still exists but is_deleted=True)
        result = await db_session.execute(
            select(HarvestLot).where(HarvestLot.id == test_harvest_lot.id)
        )
        persisted = result.scalar_one()
        assert persisted.is_deleted == True
        
        # Verify get_by_id no longer returns it (filtered out)
        retrieved = await harvest_lot_repository.get_by_id(
            lot_id=test_harvest_lot.id,
            winery_id=test_winery.id
        )
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_enforces_winery_isolation(
        self,
        harvest_lot_repository,
        test_harvest_lot,
    ):
        """
        Test that delete() enforces multi-tenant isolation.
        
        GIVEN a harvest lot exists for winery 1
        WHEN delete() is called with different winery_id
        THEN False should be returned (no deletion)
        """
        # Act
        success = await harvest_lot_repository.delete(
            lot_id=test_harvest_lot.id,
            winery_id=99999  # Different winery
        )
        
        # Assert
        assert success is False
