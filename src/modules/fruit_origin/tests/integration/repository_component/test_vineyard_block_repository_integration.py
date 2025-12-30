"""
Integration tests for VineyardBlockRepository.

These tests validate repository operations against real SQLite database,
ensuring that:
- Create operations persist correctly with VineyardBlockCreate DTO
- Get operations return correct data with multi-tenant winery_id scoping
- Vineyard verification works correctly (multi-tenant security)
- Update operations persist correctly
- Delete operations soft-delete correctly
- Multi-tenant isolation works correctly via vineyard JOIN
- Duplicate code constraints are enforced per vineyard

Database: SQLite in-memory (shared cache)
Following ADR-002: Integration tests verify actual database operations.
Following ADR-009: Phase 2 repository implementation tests.
"""

import pytest
from sqlalchemy import select

from src.modules.fruit_origin.src.domain.dtos.vineyard_block_dtos import (
    VineyardBlockCreate,
    VineyardBlockUpdate,
)
from src.modules.fruit_origin.src.repository_component.errors import (
    DuplicateCodeError,
    NotFoundError,
)

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestVineyardBlockRepositoryCRUD:
    """Integration tests for basic CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_block_persists_to_database(
        self,
        test_models,
        vineyard_block_repository,
        test_winery,
        test_vineyard,
        db_session,
    ):
        """Test that create() persists VineyardBlock to database."""
        # Arrange
        VineyardBlock = test_models['VineyardBlock']
        block_data = VineyardBlockCreate(
            code="BLK-TEST-001",
            soil_type="Clay loam",
            slope_pct=5.0,
            area_ha=2.5,
            notes="Test block"
        )
        
        # Act
        created = await vineyard_block_repository.create(
            vineyard_id=test_vineyard.id,
            winery_id=test_winery.id,
            data=block_data
        )
        await db_session.flush()
        
        # Assert
        assert created.id is not None
        assert created.vineyard_id == test_vineyard.id
        assert created.code == "BLK-TEST-001"
        assert created.soil_type == "Clay loam"
        assert created.slope_pct == 5.0
        assert created.area_ha == 2.5
        assert created.is_deleted == False
        
        # Verify persistence
        result = await db_session.execute(
            select(VineyardBlock).where(VineyardBlock.id == created.id)
        )
        persisted = result.scalar_one()
        assert persisted.code == "BLK-TEST-001"

    @pytest.mark.asyncio
    async def test_create_block_with_minimal_data(
        self,
        vineyard_block_repository,
        test_winery,
        test_vineyard,
    ):
        """Test that create() works with only required code field."""
        # Arrange
        block_data = VineyardBlockCreate(code="BLK-MINIMAL")
        
        # Act
        created = await vineyard_block_repository.create(
            vineyard_id=test_vineyard.id,
            winery_id=test_winery.id,
            data=block_data
        )
        
        # Assert
        assert created.code == "BLK-MINIMAL"
        assert created.soil_type is None
        assert created.area_ha is None

    @pytest.mark.asyncio
    async def test_create_block_validates_vineyard_exists(
        self,
        vineyard_block_repository,
        test_winery,
    ):
        """Test that create() validates vineyard exists."""
        # Arrange
        block_data = VineyardBlockCreate(code="BLK-NO-VINEYARD")
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await vineyard_block_repository.create(
                vineyard_id=99999,  # Non-existent vineyard
                winery_id=test_winery.id,
                data=block_data
            )
        assert "Vineyard 99999 not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_block_enforces_winery_isolation(
        self,
        test_models,
        vineyard_block_repository,
        test_vineyard,
        db_session,
    ):
        """Test that create() enforces vineyard belongs to winery."""
        # Arrange - Create another winery and try to create block in test_vineyard
        from uuid import uuid4
        Winery = test_models['Winery']
        other_winery = Winery(
            code=f"OTHER-{uuid4().hex[:8].upper()}",
            name="Other Winery",
            location="Sonoma"
        )
        db_session.add(other_winery)
        await db_session.flush()
        
        block_data = VineyardBlockCreate(code="BLK-WRONG-WINERY")
        
        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await vineyard_block_repository.create(
                vineyard_id=test_vineyard.id,
                winery_id=other_winery.id,  # Wrong winery
                data=block_data
            )
        assert f"Vineyard {test_vineyard.id} not found for winery {other_winery.id}" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_duplicate_code_raises_error(
        self,
        vineyard_block_repository,
        test_winery,
        test_vineyard,
        test_vineyard_block,
    ):
        """Test that creating block with duplicate code in same vineyard raises error."""
        # Arrange - test_vineyard_block has code "BLK001"
        duplicate_data = VineyardBlockCreate(code="BLK001")
        
        # Act & Assert
        with pytest.raises(DuplicateCodeError) as exc_info:
            await vineyard_block_repository.create(
                vineyard_id=test_vineyard.id,
                winery_id=test_winery.id,
                data=duplicate_data
            )
        assert "BLK001" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_by_id_returns_block(
        self,
        vineyard_block_repository,
        test_vineyard_block,
        test_winery,
    ):
        """Test that get_by_id() returns correct block."""
        # Act
        retrieved = await vineyard_block_repository.get_by_id(
            block_id=test_vineyard_block.id,
            winery_id=test_winery.id
        )
        
        # Assert
        assert retrieved is not None
        assert retrieved.id == test_vineyard_block.id
        assert retrieved.code == test_vineyard_block.code

    @pytest.mark.asyncio
    async def test_get_by_id_enforces_winery_isolation(
        self,
        test_models,
        vineyard_block_repository,
        test_vineyard_block,
        db_session,
    ):
        """Test that get_by_id() enforces multi-tenant isolation via vineyard JOIN."""
        # Arrange - Create another winery
        from uuid import uuid4
        Winery = test_models['Winery']
        other_winery = Winery(
            code=f"OTHER2-{uuid4().hex[:8].upper()}",
            name="Other Winery",
            location="Sonoma"
        )
        db_session.add(other_winery)
        await db_session.flush()
        
        # Act - Try to access test_vineyard_block with wrong winery ID
        result = await vineyard_block_repository.get_by_id(
            block_id=test_vineyard_block.id,
            winery_id=other_winery.id
        )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_vineyard_returns_all_blocks(
        self,
        test_models,
        vineyard_block_repository,
        test_winery,
        test_vineyard,
        test_vineyard_block,
        db_session,
    ):
        """Test that get_by_vineyard() returns all blocks for a vineyard."""
        # Arrange - Create additional blocks
        VineyardBlock = test_models['VineyardBlock']
        block2 = VineyardBlock(
            vineyard_id=test_vineyard.id,
            code="BLK002",
            is_deleted=False
        )
        block3 = VineyardBlock(
            vineyard_id=test_vineyard.id,
            code="BLK003",
            is_deleted=False
        )
        db_session.add_all([block2, block3])
        await db_session.flush()
        
        # Act
        blocks = await vineyard_block_repository.get_by_vineyard(
            vineyard_id=test_vineyard.id,
            winery_id=test_winery.id
        )
        
        # Assert
        assert len(blocks) == 3
        codes = [b.code for b in blocks]
        assert "BLK001" in codes
        assert "BLK002" in codes
        assert "BLK003" in codes

    @pytest.mark.asyncio
    async def test_get_by_vineyard_excludes_soft_deleted(
        self,
        test_models,
        vineyard_block_repository,
        test_winery,
        test_vineyard,
        test_vineyard_block,
        db_session,
    ):
        """Test that get_by_vineyard() excludes soft-deleted blocks."""
        # Arrange - Create soft-deleted block
        VineyardBlock = test_models['VineyardBlock']
        deleted_block = VineyardBlock(
            vineyard_id=test_vineyard.id,
            code="BLK-DELETED",
            is_deleted=True
        )
        db_session.add(deleted_block)
        await db_session.flush()
        
        # Act
        blocks = await vineyard_block_repository.get_by_vineyard(
            vineyard_id=test_vineyard.id,
            winery_id=test_winery.id
        )
        
        # Assert
        codes = [b.code for b in blocks]
        assert "BLK001" in codes
        assert "BLK-DELETED" not in codes

    @pytest.mark.asyncio
    async def test_get_by_code_returns_block(
        self,
        vineyard_block_repository,
        test_vineyard_block,
        test_winery,
        test_vineyard,
    ):
        """Test that get_by_code() returns correct block."""
        # Act
        retrieved = await vineyard_block_repository.get_by_code(
            code="BLK001",
            vineyard_id=test_vineyard.id,
            winery_id=test_winery.id
        )
        
        # Assert
        assert retrieved is not None
        assert retrieved.id == test_vineyard_block.id
        assert retrieved.code == "BLK001"

    @pytest.mark.asyncio
    async def test_update_block_persists_changes(
        self,
        test_models,
        vineyard_block_repository,
        test_vineyard_block,
        test_winery,
        db_session,
    ):
        """Test that update() persists changes to database."""
        # Arrange
        VineyardBlock = test_models['VineyardBlock']
        update_data = VineyardBlockUpdate(
            code="BLK001-UPDATED",
            soil_type="Updated soil",
            area_ha=3.5,
            notes="Updated notes"
        )
        
        # Act
        updated = await vineyard_block_repository.update(
            block_id=test_vineyard_block.id,
            winery_id=test_winery.id,
            data=update_data
        )
        await db_session.flush()
        
        # Assert
        assert updated is not None
        assert updated.code == "BLK001-UPDATED"
        assert updated.soil_type == "Updated soil"
        assert updated.area_ha == 3.5
        
        # Verify persistence
        result = await db_session.execute(
            select(VineyardBlock).where(VineyardBlock.id == test_vineyard_block.id)
        )
        persisted = result.scalar_one()
        assert persisted.code == "BLK001-UPDATED"
        assert persisted.soil_type == "Updated soil"

    @pytest.mark.asyncio
    async def test_delete_block_soft_deletes(
        self,
        test_models,
        vineyard_block_repository,
        test_vineyard_block,
        test_winery,
        db_session,
    ):
        """Test that delete() performs soft delete."""
        # Arrange
        VineyardBlock = test_models['VineyardBlock']
        
        # Act
        result = await vineyard_block_repository.delete(
            block_id=test_vineyard_block.id,
            winery_id=test_winery.id
        )
        await db_session.flush()
        
        # Assert
        assert result is True
        
        # Verify soft delete in database
        db_result = await db_session.execute(
            select(VineyardBlock).where(VineyardBlock.id == test_vineyard_block.id)
        )
        persisted = db_result.scalar_one()
        assert persisted.is_deleted == True
        
        # Verify not returned by get_by_id
        retrieved = await vineyard_block_repository.get_by_id(
            block_id=test_vineyard_block.id,
            winery_id=test_winery.id
        )
        assert retrieved is None
