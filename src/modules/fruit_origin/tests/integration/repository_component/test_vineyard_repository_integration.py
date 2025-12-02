"""
Integration tests for VineyardRepository.

These tests validate repository operations against real SQLite database,
ensuring that:
- Create operations persist correctly with VineyardCreate DTO
- Get operations return correct data with multi-tenant winery_id scoping
- Update operations persist correctly
- Delete operations soft-delete correctly
- Multi-tenant isolation works correctly
- Duplicate code constraints are enforced

Database: SQLite in-memory (shared cache)
Following ADR-002: Integration tests verify actual database operations.
Following ADR-009: Phase 2 repository implementation tests.
"""

import pytest
from sqlalchemy import select

from src.modules.fruit_origin.src.domain.dtos.vineyard_dtos import (
    VineyardCreate,
    VineyardUpdate,
)
from src.modules.fruit_origin.src.repository_component.errors import (
    DuplicateCodeError,
)

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestVineyardRepositoryCRUD:
    """Integration tests for basic CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_vineyard_persists_to_database(
        self,
        test_models,
        vineyard_repository,
        test_winery,
        db_session,
    ):
        """Test that create() persists Vineyard to database."""
        # Arrange
        Vineyard = test_models['Vineyard']
        vineyard_data = VineyardCreate(
            code="VYD-TEST-001",
            name="North Vineyard",
            notes="Premium location"
        )
        
        # Act
        created = await vineyard_repository.create(
            winery_id=test_winery.id,
            data=vineyard_data
        )
        await db_session.flush()
        
        # Assert
        assert created.id is not None
        assert created.winery_id == test_winery.id
        assert created.code == "VYD-TEST-001"
        assert created.name == "North Vineyard"
        assert created.notes == "Premium location"
        assert created.is_deleted == False
        
        # Verify persistence
        result = await db_session.execute(
            select(Vineyard).where(Vineyard.id == created.id)
        )
        persisted = result.scalar_one()
        assert persisted.code == "VYD-TEST-001"
        assert persisted.is_deleted == False

    @pytest.mark.asyncio
    async def test_create_vineyard_without_notes(
        self,
        vineyard_repository,
        test_winery,
    ):
        """Test that create() works without optional notes field."""
        # Arrange
        vineyard_data = VineyardCreate(
            code="VYD-MINIMAL",
            name="Minimal Vineyard"
        )
        
        # Act
        created = await vineyard_repository.create(
            winery_id=test_winery.id,
            data=vineyard_data
        )
        
        # Assert
        assert created.code == "VYD-MINIMAL"
        assert created.notes is None

    @pytest.mark.asyncio
    async def test_create_duplicate_code_raises_error(
        self,
        vineyard_repository,
        test_winery,
        test_vineyard,
    ):
        """Test that creating vineyard with duplicate code raises error."""
        # Arrange - test_vineyard has code "VYD001"
        duplicate_data = VineyardCreate(
            code="VYD001",  # Same code as test_vineyard
            name="Duplicate Vineyard"
        )
        
        # Act & Assert
        with pytest.raises(DuplicateCodeError) as exc_info:
            await vineyard_repository.create(
                winery_id=test_winery.id,
                data=duplicate_data
            )
        assert "VYD001" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_by_id_returns_vineyard(
        self,
        vineyard_repository,
        test_vineyard,
        test_winery,
    ):
        """Test that get_by_id() returns correct vineyard."""
        # Act
        retrieved = await vineyard_repository.get_by_id(
            vineyard_id=test_vineyard.id,
            winery_id=test_winery.id
        )
        
        # Assert
        assert retrieved is not None
        assert retrieved.id == test_vineyard.id
        assert retrieved.code == test_vineyard.code
        assert retrieved.name == test_vineyard.name

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self,
        vineyard_repository,
        test_winery,
    ):
        """Test that get_by_id() returns None for non-existent ID."""
        # Act
        result = await vineyard_repository.get_by_id(
            vineyard_id=99999,
            winery_id=test_winery.id
        )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_enforces_winery_isolation(
        self,
        test_models,
        vineyard_repository,
        test_vineyard,
        db_session,
    ):
        """Test that get_by_id() enforces multi-tenant isolation."""
        # Arrange - Create another winery
        Winery = test_models['Winery']
        other_winery = Winery(name="Other Winery", region="Sonoma")
        db_session.add(other_winery)
        await db_session.flush()
        
        # Act - Try to access test_vineyard with wrong winery ID
        result = await vineyard_repository.get_by_id(
            vineyard_id=test_vineyard.id,
            winery_id=other_winery.id
        )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_winery_returns_all_vineyards(
        self,
        test_models,
        vineyard_repository,
        test_winery,
        test_vineyard,
        db_session,
    ):
        """Test that get_by_winery() returns all vineyards for a winery."""
        # Arrange - Create additional vineyards
        Vineyard = test_models['Vineyard']
        vineyard2 = Vineyard(
            winery_id=test_winery.id,
            code="VYD002",
            name="South Vineyard",
            is_deleted=False
        )
        vineyard3 = Vineyard(
            winery_id=test_winery.id,
            code="VYD003",
            name="East Vineyard",
            is_deleted=False
        )
        db_session.add_all([vineyard2, vineyard3])
        await db_session.flush()
        
        # Act
        vineyards = await vineyard_repository.get_by_winery(
            winery_id=test_winery.id
        )
        
        # Assert
        assert len(vineyards) == 3
        codes = [v.code for v in vineyards]
        assert "VYD001" in codes
        assert "VYD002" in codes
        assert "VYD003" in codes

    @pytest.mark.asyncio
    async def test_get_by_winery_excludes_soft_deleted(
        self,
        test_models,
        vineyard_repository,
        test_winery,
        test_vineyard,
        db_session,
    ):
        """Test that get_by_winery() excludes soft-deleted vineyards."""
        # Arrange - Create soft-deleted vineyard
        Vineyard = test_models['Vineyard']
        deleted_vineyard = Vineyard(
            winery_id=test_winery.id,
            code="VYD-DELETED",
            name="Deleted Vineyard",
            is_deleted=True
        )
        db_session.add(deleted_vineyard)
        await db_session.flush()
        
        # Act
        vineyards = await vineyard_repository.get_by_winery(
            winery_id=test_winery.id
        )
        
        # Assert
        codes = [v.code for v in vineyards]
        assert "VYD001" in codes
        assert "VYD-DELETED" not in codes

    @pytest.mark.asyncio
    async def test_get_by_code_returns_vineyard(
        self,
        vineyard_repository,
        test_vineyard,
        test_winery,
    ):
        """Test that get_by_code() returns correct vineyard."""
        # Act
        retrieved = await vineyard_repository.get_by_code(
            code="VYD001",
            winery_id=test_winery.id
        )
        
        # Assert
        assert retrieved is not None
        assert retrieved.id == test_vineyard.id
        assert retrieved.code == "VYD001"

    @pytest.mark.asyncio
    async def test_update_vineyard_persists_changes(
        self,
        test_models,
        vineyard_repository,
        test_vineyard,
        test_winery,
        db_session,
    ):
        """Test that update() persists changes to database."""
        # Arrange
        Vineyard = test_models['Vineyard']
        update_data = VineyardUpdate(
            code="VYD001-UPDATED",
            name="Updated Vineyard",
            notes="Updated notes"
        )
        
        # Act
        updated = await vineyard_repository.update(
            vineyard_id=test_vineyard.id,
            winery_id=test_winery.id,
            data=update_data
        )
        await db_session.flush()
        
        # Assert
        assert updated is not None
        assert updated.code == "VYD001-UPDATED"
        assert updated.name == "Updated Vineyard"
        assert updated.notes == "Updated notes"
        
        # Verify persistence
        result = await db_session.execute(
            select(Vineyard).where(Vineyard.id == test_vineyard.id)
        )
        persisted = result.scalar_one()
        assert persisted.code == "VYD001-UPDATED"
        assert persisted.name == "Updated Vineyard"

    @pytest.mark.asyncio
    async def test_delete_vineyard_soft_deletes(
        self,
        test_models,
        vineyard_repository,
        test_vineyard,
        test_winery,
        db_session,
    ):
        """Test that delete() performs soft delete."""
        # Arrange
        Vineyard = test_models['Vineyard']
        
        # Act
        result = await vineyard_repository.delete(
            vineyard_id=test_vineyard.id,
            winery_id=test_winery.id
        )
        await db_session.flush()
        
        # Assert
        assert result is True
        
        # Verify soft delete in database
        db_result = await db_session.execute(
            select(Vineyard).where(Vineyard.id == test_vineyard.id)
        )
        persisted = db_result.scalar_one()
        assert persisted.is_deleted == True
        
        # Verify not returned by get_by_id
        retrieved = await vineyard_repository.get_by_id(
            vineyard_id=test_vineyard.id,
            winery_id=test_winery.id
        )
        assert retrieved is None
