"""
Integration tests for HarvestLotRepository.

These tests validate repository operations against real SQLite database,
ensuring that:
- Create operations persist correctly with HarvestLotCreate DTO
- Get operations return correct data with multi-tenant winery_id scoping
- Update operations persist correctly
- Delete operations soft-delete correctly
- Multi-tenant isolation works correctly
- Complex queries (get_by_harvest_date_range, get_available_for_blend) work correctly
- Block validation and multi-tenant security work correctly

Database: SQLite in-memory (shared cache)
Following ADR-002: Integration tests verify actual database operations.
Following ADR-009: Phase 2 repository implementation tests.
"""

import pytest
from datetime import date, datetime
from sqlalchemy import select

from src.modules.fruit_origin.src.domain.dtos.harvest_lot_dtos import (
    HarvestLotCreate,
    HarvestLotUpdate,
)
# Import RepositoryError from fermentation since that's what map_database_error returns
from src.modules.fermentation.src.repository_component.errors import RepositoryError

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestHarvestLotRepositoryCRUD:
    """Integration tests for basic CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_harvest_lot_persists_to_database(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard,
        test_vineyard_block,
        db_session,
    ):
        """Test that create() persists HarvestLot to database."""
        # Arrange
        HarvestLot = test_models['HarvestLot']
        harvest_lot_data = HarvestLotCreate(
            block_id=test_vineyard_block.id,
            code="HL-2024-001",
            harvest_date=date(2024, 3, 15),
            weight_kg=1500.5,
            brix_at_harvest=24.5,
            brix_method="refractometer",
            brix_measured_at=datetime(2024, 3, 15, 10, 30),
            grape_variety="Cabernet Sauvignon",
            clone="337",
            rootstock="101-14",
            pick_method="hand",
            pick_start_time="08:00:00",
            pick_end_time="12:30:00",
            bins_count=15,
            field_temp_c=22.5,
            notes="Excellent quality harvest"
        )
        
        # Act
        created = await harvest_lot_repository.create(
            winery_id=test_winery.id,
            data=harvest_lot_data
        )
        await db_session.flush()
        
        # Assert
        assert created.id is not None
        assert created.winery_id == test_winery.id
        assert created.block_id == test_vineyard_block.id
        assert created.code == "HL-2024-001"
        assert created.harvest_date == date(2024, 3, 15)
        assert created.weight_kg == 1500.5
        assert created.brix_at_harvest == 24.5
        assert created.grape_variety == "Cabernet Sauvignon"
        assert created.is_deleted == False
        
        # Verify persistence
        result = await db_session.execute(
            select(HarvestLot).where(HarvestLot.id == created.id)
        )
        persisted = result.scalar_one()
        assert persisted.code == "HL-2024-001"
        assert persisted.weight_kg == 1500.5
        assert persisted.is_deleted == False

    @pytest.mark.asyncio
    async def test_create_with_minimal_required_fields(
        self,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
    ):
        """Test that create() works with only required fields."""
        # Arrange
        harvest_lot_data = HarvestLotCreate(
            block_id=test_vineyard_block.id,
            code="HL-MINIMAL",
            harvest_date=date(2024, 3, 16),
            weight_kg=1000.0,
            grape_variety="Merlot"
        )
        
        # Act
        created = await harvest_lot_repository.create(
            winery_id=test_winery.id,
            data=harvest_lot_data
        )
        
        # Assert
        assert created.code == "HL-MINIMAL"
        assert created.weight_kg == 1000.0
        assert created.brix_at_harvest is None
        assert created.notes is None

    @pytest.mark.asyncio
    async def test_create_with_nonexistent_block_raises_error(
        self,
        harvest_lot_repository,
        test_winery,
    ):
        """Test that create() raises NotFoundError for invalid block_id."""
        # Arrange
        harvest_lot_data = HarvestLotCreate(
            block_id=99999,  # Non-existent block
            code="HL-ERROR",
            harvest_date=date(2024, 3, 17),
            weight_kg=1000.0,
            grape_variety="Merlot"
        )
        
        # Act & Assert
        with pytest.raises(RepositoryError, match="VineyardBlock 99999 not found or access denied"):
            await harvest_lot_repository.create(
                winery_id=test_winery.id,
                data=harvest_lot_data
            )

    @pytest.mark.asyncio
    async def test_get_by_id_returns_correct_harvest_lot(
        self,
        harvest_lot_repository,
        test_winery,
        test_harvest_lot,
    ):
        """Test that get_by_id() returns correct HarvestLot."""
        # Act
        result = await harvest_lot_repository.get_by_id(
            lot_id=test_harvest_lot.id,
            winery_id=test_winery.id
        )
        
        # Assert
        assert result is not None
        assert result.id == test_harvest_lot.id
        assert result.code == test_harvest_lot.code
        assert result.winery_id == test_winery.id

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_soft_deleted(
        self,
        harvest_lot_repository,
        test_winery,
        test_harvest_lot,
        db_session,
    ):
        """Test that get_by_id() returns None for soft-deleted harvest lots."""
        # Arrange: Soft delete the harvest lot
        test_harvest_lot.is_deleted = True
        await db_session.flush()
        
        # Act
        result = await harvest_lot_repository.get_by_id(
            lot_id=test_harvest_lot.id,
            winery_id=test_winery.id
        )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_winery_returns_all_winery_lots(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
        db_session,
    ):
        """Test that get_by_winery() returns all HarvestLots for winery."""
        # Arrange: Create multiple harvest lots
        HarvestLot = test_models['HarvestLot']
        lots = [
            HarvestLot(
                winery_id=test_winery.id,
                block_id=test_vineyard_block.id,
                code=f"HL-WINERY-{i}",
                harvest_date=date(2024, 3, i+1),
                weight_kg=1000.0 * i,
                grape_variety="Cabernet Sauvignon",
                is_deleted=False
            )
            for i in range(1, 4)
        ]
        db_session.add_all(lots)
        await db_session.flush()
        
        # Act
        results = await harvest_lot_repository.get_by_winery(test_winery.id)
        
        # Assert
        assert len(results) >= 3
        codes = [lot.code for lot in results]
        assert "HL-WINERY-1" in codes
        assert "HL-WINERY-2" in codes
        assert "HL-WINERY-3" in codes
        # Should be ordered by harvest_date DESC
        assert results[0].harvest_date >= results[1].harvest_date

    @pytest.mark.asyncio
    async def test_get_by_code_returns_unique_lot(
        self,
        harvest_lot_repository,
        test_winery,
        test_harvest_lot,
    ):
        """Test that get_by_code() returns correct HarvestLot by code."""
        # Act
        result = await harvest_lot_repository.get_by_code(
            code=test_harvest_lot.code,
            winery_id=test_winery.id
        )
        
        # Assert
        assert result is not None
        assert result.id == test_harvest_lot.id
        assert result.code == test_harvest_lot.code

    @pytest.mark.asyncio
    async def test_get_by_code_returns_none_when_not_found(
        self,
        harvest_lot_repository,
        test_winery,
    ):
        """Test that get_by_code() returns None for non-existent code."""
        # Act
        result = await harvest_lot_repository.get_by_code(
            code="NON-EXISTENT",
            winery_id=test_winery.id
        )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_block_returns_lots_from_specific_block(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard,
        test_vineyard_block,
        db_session,
    ):
        """Test that get_by_block() returns all HarvestLots from a specific block."""
        # Arrange: Create another block and lots
        VineyardBlock = test_models['VineyardBlock']
        HarvestLot = test_models['HarvestLot']
        
        another_block = VineyardBlock(
            vineyard_id=test_vineyard.id,
            code="BLK-002"
        )
        db_session.add(another_block)
        await db_session.flush()
        
        # Create lots in different blocks
        lot1 = HarvestLot(
            winery_id=test_winery.id,
            block_id=test_vineyard_block.id,
            code="HL-BLK1-001",
            harvest_date=date(2024, 3, 20),
            weight_kg=1500.0,
            grape_variety="Cabernet Sauvignon"
        )
        lot2 = HarvestLot(
            winery_id=test_winery.id,
            block_id=another_block.id,
            code="HL-BLK2-001",
            harvest_date=date(2024, 3, 21),
            weight_kg=1200.0,
            grape_variety="Merlot"
        )
        db_session.add_all([lot1, lot2])
        await db_session.flush()
        
        # Act
        results = await harvest_lot_repository.get_by_block(
            block_id=test_vineyard_block.id,
            winery_id=test_winery.id
        )
        
        # Assert
        assert len(results) >= 1
        codes = [lot.code for lot in results]
        assert "HL-BLK1-001" in codes
        assert "HL-BLK2-001" not in codes
        # All should be from the correct block
        for lot in results:
            assert lot.block_id == test_vineyard_block.id

    @pytest.mark.asyncio
    async def test_get_by_harvest_date_range_returns_lots_in_range(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
        db_session,
    ):
        """Test that get_by_harvest_date_range() returns lots within date range."""
        # Arrange: Create lots with different dates
        HarvestLot = test_models['HarvestLot']
        lots = [
            HarvestLot(
                winery_id=test_winery.id,
                block_id=test_vineyard_block.id,
                code=f"HL-DATE-{i}",
                harvest_date=date(2024, 3, i),
                weight_kg=1000.0,
                grape_variety="Cabernet Sauvignon"
            )
            for i in range(10, 21)  # March 10-20
        ]
        db_session.add_all(lots)
        await db_session.flush()
        
        # Act: Query March 12-15
        results = await harvest_lot_repository.get_by_harvest_date_range(
            winery_id=test_winery.id,
            start_date=date(2024, 3, 12),
            end_date=date(2024, 3, 15)
        )
        
        # Assert
        assert len(results) == 4  # March 12, 13, 14, 15
        for lot in results:
            assert date(2024, 3, 12) <= lot.harvest_date <= date(2024, 3, 15)
        # Should be ordered by harvest_date ASC
        assert results[0].harvest_date <= results[-1].harvest_date

    @pytest.mark.asyncio
    async def test_get_by_harvest_date_range_raises_error_for_invalid_range(
        self,
        harvest_lot_repository,
        test_winery,
    ):
        """Test that get_by_harvest_date_range() raises ValueError for invalid range."""
        # Act & Assert
        with pytest.raises(ValueError, match="start_date .* must be <= end_date"):
            await harvest_lot_repository.get_by_harvest_date_range(
                winery_id=test_winery.id,
                start_date=date(2024, 3, 20),
                end_date=date(2024, 3, 10)
            )

    @pytest.mark.asyncio
    async def test_get_available_for_blend_returns_lots(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
        db_session,
    ):
        """Test that get_available_for_blend() returns harvest lots."""
        # Arrange: Create lots with different weights
        HarvestLot = test_models['HarvestLot']
        lots = [
            HarvestLot(
                winery_id=test_winery.id,
                block_id=test_vineyard_block.id,
                code=f"HL-BLEND-{i}",
                harvest_date=date(2024, 3, i),
                weight_kg=1000.0 * i,
                grape_variety="Cabernet Sauvignon"
            )
            for i in range(1, 5)
        ]
        db_session.add_all(lots)
        await db_session.flush()
        
        # Act
        results = await harvest_lot_repository.get_available_for_blend(
            winery_id=test_winery.id
        )
        
        # Assert
        assert len(results) >= 4
        # Should be ordered by harvest_date ASC (oldest first)
        assert results[0].harvest_date <= results[-1].harvest_date

    @pytest.mark.asyncio
    async def test_get_available_for_blend_with_min_weight_filter(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
        db_session,
    ):
        """Test that get_available_for_blend() filters by minimum weight."""
        # Arrange: Create lots with different weights
        HarvestLot = test_models['HarvestLot']
        lots = [
            HarvestLot(
                winery_id=test_winery.id,
                block_id=test_vineyard_block.id,
                code=f"HL-WEIGHT-{i}",
                harvest_date=date(2024, 3, i),
                weight_kg=500.0 * i,  # 500, 1000, 1500, 2000
                grape_variety="Cabernet Sauvignon"
            )
            for i in range(1, 5)
        ]
        db_session.add_all(lots)
        await db_session.flush()
        
        # Act: Filter for lots with at least 1200kg
        results = await harvest_lot_repository.get_available_for_blend(
            winery_id=test_winery.id,
            min_weight_kg=1200.0
        )
        
        # Assert
        assert len(results) >= 2  # Only lots with 1500kg and 2000kg
        for lot in results:
            assert lot.weight_kg >= 1200.0

    @pytest.mark.asyncio
    async def test_update_modifies_harvest_lot(
        self,
        harvest_lot_repository,
        test_winery,
        test_harvest_lot,
        db_session,
    ):
        """Test that update() modifies HarvestLot fields."""
        # Arrange
        update_data = HarvestLotUpdate(
            code="HL-UPDATED",
            weight_kg=2000.0,
            notes="Updated notes"
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
        assert updated.code == "HL-UPDATED"
        assert updated.weight_kg == 2000.0
        assert updated.notes == "Updated notes"
        # Original fields should remain unchanged
        assert updated.harvest_date == test_harvest_lot.harvest_date

    @pytest.mark.asyncio
    async def test_update_returns_none_for_nonexistent_lot(
        self,
        harvest_lot_repository,
        test_winery,
    ):
        """Test that update() returns None for non-existent harvest lot."""
        # Arrange
        update_data = HarvestLotUpdate(code="HL-NONE")
        
        # Act
        result = await harvest_lot_repository.update(
            lot_id=99999,
            winery_id=test_winery.id,
            data=update_data
        )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_soft_deletes_harvest_lot(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_harvest_lot,
        db_session,
    ):
        """Test that delete() soft-deletes HarvestLot."""
        # Act
        success = await harvest_lot_repository.delete(
            lot_id=test_harvest_lot.id,
            winery_id=test_winery.id
        )
        await db_session.flush()
        
        # Assert
        assert success is True
        
        # Verify soft delete in database
        HarvestLot = test_models['HarvestLot']
        result = await db_session.execute(
            select(HarvestLot).where(HarvestLot.id == test_harvest_lot.id)
        )
        deleted_lot = result.scalar_one()
        assert deleted_lot.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_nonexistent_lot(
        self,
        harvest_lot_repository,
        test_winery,
    ):
        """Test that delete() returns False for non-existent harvest lot."""
        # Act
        success = await harvest_lot_repository.delete(
            lot_id=99999,
            winery_id=test_winery.id
        )
        
        # Assert
        assert success is False


class TestHarvestLotRepositoryMultiTenant:
    """Integration tests for multi-tenant isolation."""

    @pytest.mark.asyncio
    async def test_get_by_id_respects_winery_isolation(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
        db_session,
    ):
        """Test that get_by_id() respects winery_id isolation."""
        # Arrange: Create harvest lot for test_winery
        HarvestLot = test_models['HarvestLot']
        lot = HarvestLot(
            winery_id=test_winery.id,
            block_id=test_vineyard_block.id,
            code="HL-ISOLATED",
            harvest_date=date(2024, 3, 25),
            weight_kg=1500.0,
            grape_variety="Cabernet Sauvignon"
        )
        db_session.add(lot)
        await db_session.flush()
        
        # Act: Try to access with different winery_id
        result = await harvest_lot_repository.get_by_id(
            lot_id=lot.id,
            winery_id=test_winery.id + 1
        )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_create_validates_block_belongs_to_winery(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        db_session,
    ):
        """Test that create() validates block belongs to winery."""
        # Arrange: Create another winery and block
        Winery = test_models['Winery']
        Vineyard = test_models['Vineyard']
        VineyardBlock = test_models['VineyardBlock']
        
        other_winery = Winery(name="Other Winery")
        db_session.add(other_winery)
        await db_session.flush()
        
        other_vineyard = Vineyard(
            winery_id=other_winery.id,
            code="OTHER-VYD",
            name="Other Vineyard"
        )
        db_session.add(other_vineyard)
        await db_session.flush()
        
        other_block = VineyardBlock(
            vineyard_id=other_vineyard.id,
            code="OTHER-BLK"
        )
        db_session.add(other_block)
        await db_session.flush()
        
        # Act & Assert: Try to create harvest lot with another winery's block
        harvest_lot_data = HarvestLotCreate(
            block_id=other_block.id,
            code="HL-VIOLATION",
            harvest_date=date(2024, 3, 26),
            weight_kg=1000.0,
            grape_variety="Merlot"
        )
        
        with pytest.raises(RepositoryError, match="VineyardBlock .* not found or access denied"):
            await harvest_lot_repository.create(
                winery_id=test_winery.id,
                data=harvest_lot_data
            )

    @pytest.mark.asyncio
    async def test_get_by_winery_only_returns_winery_lots(
        self,
        test_models,
        harvest_lot_repository,
        test_winery,
        test_vineyard_block,
        db_session,
    ):
        """Test that get_by_winery() only returns lots for specified winery."""
        # Arrange: Create another winery with its own structure
        Winery = test_models['Winery']
        Vineyard = test_models['Vineyard']
        VineyardBlock = test_models['VineyardBlock']
        HarvestLot = test_models['HarvestLot']
        
        other_winery = Winery(name="Other Winery 2")
        db_session.add(other_winery)
        await db_session.flush()
        
        other_vineyard = Vineyard(
            winery_id=other_winery.id,
            code="OTHER2-VYD",
            name="Other Vineyard 2"
        )
        db_session.add(other_vineyard)
        await db_session.flush()
        
        other_block = VineyardBlock(
            vineyard_id=other_vineyard.id,
            code="OTHER2-BLK"
        )
        db_session.add(other_block)
        await db_session.flush()
        
        # Create lots for both wineries
        test_lot = HarvestLot(
            winery_id=test_winery.id,
            block_id=test_vineyard_block.id,
            code="HL-TEST-WINERY",
            harvest_date=date(2024, 3, 27),
            weight_kg=1500.0,
            grape_variety="Cabernet Sauvignon"
        )
        other_lot = HarvestLot(
            winery_id=other_winery.id,
            block_id=other_block.id,
            code="HL-OTHER-WINERY",
            harvest_date=date(2024, 3, 28),
            weight_kg=1200.0,
            grape_variety="Merlot"
        )
        db_session.add_all([test_lot, other_lot])
        await db_session.flush()
        
        # Act
        results = await harvest_lot_repository.get_by_winery(test_winery.id)
        
        # Assert
        codes = [lot.code for lot in results]
        assert "HL-TEST-WINERY" in codes
        assert "HL-OTHER-WINERY" not in codes
        # All should belong to test_winery
        for lot in results:
            assert lot.winery_id == test_winery.id
