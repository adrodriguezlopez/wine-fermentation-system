"""
Integration tests for WineryRepository.

These tests validate repository operations against real SQLite database.
Following ADR-009: Phase 3 - Winery repository implementation tests.
"""

import pytest
from sqlalchemy import select

from src.modules.winery.src.domain.dtos.winery_dtos import (
    WineryCreate,
    WineryUpdate,
)
from src.modules.winery.src.repository_component.repositories.winery_repository import (
    DuplicateNameError,
)

pytestmark = pytest.mark.integration


class TestWineryRepositoryCRUD:
    """Integration tests for basic CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_winery_persists_to_database(
        self,
        test_models,
        winery_repository,
        db_session,
    ):
        """Test that create() persists Winery to database."""
        from uuid import uuid4
        Winery = test_models['Winery']
        winery_data = WineryCreate(
            code=f"SUNSET-{uuid4().hex[:8].upper()}",
            name="Sunset Vineyards",
            location="Napa Valley"
        )
        
        created = await winery_repository.create(data=winery_data)
        await db_session.flush()
        
        assert created.id is not None
        assert created.code is not None
        assert created.name == "Sunset Vineyards"
        assert created.location == "Napa Valley"
        assert created.is_deleted == False
        
        # Verify persistence
        result = await db_session.execute(
            select(Winery).where(Winery.id == created.id)
        )
        persisted = result.scalar_one()
        assert persisted.name == "Sunset Vineyards"
        assert persisted.is_deleted == False

    @pytest.mark.asyncio
    async def test_create_winery_without_region(
        self,
        winery_repository,
    ):
        """Test that create() works without optional location field."""
        from uuid import uuid4
        winery_data = WineryCreate(
            code=f"MTN-{uuid4().hex[:8].upper()}",
            name="Mountain Winery"
        )
        
        created = await winery_repository.create(data=winery_data)
        
        assert created.name == "Mountain Winery"
        assert created.location is None

    @pytest.mark.asyncio
    async def test_create_duplicate_name_raises_error(
        self,
        winery_repository,
        test_winery,
    ):
        """Test that creating winery with duplicate name raises error."""
        from uuid import uuid4
        duplicate_data = WineryCreate(
            code=f"DUP-{uuid4().hex[:8].upper()}",
            name=test_winery.name,  # Use the same name as test_winery
            location="Different Region"
        )
        
        with pytest.raises(DuplicateNameError) as exc_info:
            await winery_repository.create(data=duplicate_data)
        assert test_winery.name in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_by_id_returns_winery(
        self,
        winery_repository,
        test_winery,
    ):
        """Test that get_by_id() returns correct winery."""
        retrieved = await winery_repository.get_by_id(winery_id=test_winery.id)
        
        assert retrieved is not None
        assert retrieved.id == test_winery.id
        assert retrieved.name == test_winery.name

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self,
        winery_repository,
    ):
        """Test that get_by_id() returns None for non-existent ID."""
        result = await winery_repository.get_by_id(winery_id=99999)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_soft_deleted(
        self,
        winery_repository,
        test_models,
        db_session,
    ):
        """Test that get_by_id() excludes soft-deleted wineries."""
        from uuid import uuid4
        Winery = test_models['Winery']
        winery = Winery(
            code=f"DEL-{uuid4().hex[:8].upper()}",
            name="Deleted Winery",
            location="Old Region",
            is_deleted=True
        )
        db_session.add(winery)
        await db_session.flush()
        await db_session.refresh(winery)
        
        result = await winery_repository.get_by_id(winery_id=winery.id)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_returns_all_wineries(
        self,
        winery_repository,
        test_winery,
        test_winery_2,
    ):
        """Test that get_all() returns all active wineries."""
        wineries = await winery_repository.get_all()
        
        assert len(wineries) >= 2
        winery_ids = [w.id for w in wineries]
        assert test_winery.id in winery_ids
        assert test_winery_2.id in winery_ids

    @pytest.mark.asyncio
    async def test_get_all_orders_by_name(
        self,
        winery_repository,
        db_session,
        test_models,
    ):
        """Test that get_all() returns wineries ordered by name."""
        from uuid import uuid4
        Winery = test_models['Winery']
        winery_z = Winery(
            code=f"ZEBRA-{uuid4().hex[:8].upper()}",
            name="Zebra Winery",
            location="Region Z",
            is_deleted=False
        )
        winery_a = Winery(
            code=f"ALPHA-{uuid4().hex[:8].upper()}",
            name="Alpha Winery",
            location="Region A",
            is_deleted=False
        )
        db_session.add(winery_z)
        db_session.add(winery_a)
        await db_session.flush()
        
        wineries = await winery_repository.get_all()
        
        assert len(wineries) >= 2
        names = [w.name for w in wineries]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_get_all_excludes_soft_deleted(
        self,
        winery_repository,
        test_winery,
        test_models,
        db_session,
    ):
        """Test that get_all() excludes soft-deleted wineries."""
        from uuid import uuid4
        Winery = test_models['Winery']
        deleted = Winery(
            code=f"DELETED-{uuid4().hex[:8].upper()}",
            name=f"Deleted Winery {uuid4().hex[:8]}",
            location="Old",
            is_deleted=True
        )
        db_session.add(deleted)
        await db_session.flush()
        
        wineries = await winery_repository.get_all()
        
        winery_ids = [w.id for w in wineries]
        assert deleted.id not in winery_ids
        assert test_winery.id in winery_ids

    @pytest.mark.asyncio
    async def test_get_by_name_returns_winery(
        self,
        winery_repository,
        test_winery,
    ):
        """Test that get_by_name() returns correct winery."""
        retrieved = await winery_repository.get_by_name(name=test_winery.name)
        
        assert retrieved is not None
        assert retrieved.id == test_winery.id
        assert retrieved.name == test_winery.name

    @pytest.mark.asyncio
    async def test_get_by_name_returns_none_when_not_found(
        self,
        winery_repository,
    ):
        """Test that get_by_name() returns None for non-existent name."""
        result = await winery_repository.get_by_name(name="Nonexistent Winery")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_winery_persists_changes(
        self,
        winery_repository,
        test_winery,
        db_session,
        test_models,
    ):
        """Test that update() persists changes to database."""
        Winery = test_models['Winery']
        update_data = WineryUpdate(
            name="Updated Name",
            location="Updated Region"
        )
        
        updated = await winery_repository.update(
            winery_id=test_winery.id,
            data=update_data
        )
        await db_session.flush()
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.location == "Updated Region"
        
        result = await db_session.execute(
            select(Winery).where(Winery.id == test_winery.id)
        )
        persisted = result.scalar_one()
        assert persisted.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_partial_fields(
        self,
        winery_repository,
        test_winery,
    ):
        """Test that update() supports partial updates."""
        original_location = test_winery.location
        update_data = WineryUpdate(name="New Name Only")
        
        updated = await winery_repository.update(
            winery_id=test_winery.id,
            data=update_data
        )
        
        assert updated.name == "New Name Only"
        assert updated.location == original_location

    @pytest.mark.asyncio
    async def test_update_nonexistent_winery_returns_none(
        self,
        winery_repository,
    ):
        """Test that update() returns None for non-existent winery."""
        update_data = WineryUpdate(name="New Name")
        
        result = await winery_repository.update(winery_id=99999, data=update_data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_to_duplicate_name_raises_error(
        self,
        winery_repository,
        test_winery,
        test_winery_2,
    ):
        """Test that updating to duplicate name raises error."""
        update_data = WineryUpdate(name=test_winery_2.name)
        
        with pytest.raises(DuplicateNameError):
            await winery_repository.update(
                winery_id=test_winery.id,
                data=update_data
            )

    @pytest.mark.asyncio
    async def test_delete_winery_soft_deletes(
        self,
        winery_repository,
        test_winery,
        db_session,
        test_models,
    ):
        """Test that delete() performs soft delete."""
        Winery = test_models['Winery']
        
        result = await winery_repository.delete(winery_id=test_winery.id)
        await db_session.flush()
        
        assert result is True
        
        db_result = await db_session.execute(
            select(Winery).where(Winery.id == test_winery.id)
        )
        persisted = db_result.scalar_one()
        assert persisted.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_winery_returns_false(
        self,
        winery_repository,
    ):
        """Test that delete() returns False for non-existent winery."""
        result = await winery_repository.delete(winery_id=99999)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_already_deleted_winery_returns_false(
        self,
        winery_repository,
        test_models,
        db_session,
    ):
        """Test that delete() returns False for already deleted winery."""
        from uuid import uuid4
        Winery = test_models['Winery']
        winery = Winery(
            code=f"ALDEL-{uuid4().hex[:8].upper()}",
            name="Already Deleted",
            location="Old",
            is_deleted=True
        )
        db_session.add(winery)
        await db_session.flush()
        await db_session.refresh(winery)
        
        result = await winery_repository.delete(winery_id=winery.id)
        
        assert result is False
