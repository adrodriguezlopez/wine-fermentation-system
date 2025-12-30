"""
Integration tests for FermentationRepository.

These tests validate repository operations against real PostgreSQL database,
ensuring that:
- Create operations persist correctly with FermentationCreate DTO
- Get operations         
        completed_data = FermentationCreate(
            fermented_by_user_id=test_user.id,
            vintage_year=2024,
            yeast_strain="D47",
            vessel_code="TANK-COMPLETED",
            input_mass_kg=600.0,
            initial_sugar_brix=24.0,
            initial_density=1.098,
            start_date=datetime.now(),
        )
        
        active_ferm = await fermentation_repository.create(
            winery_id=test_user.winery_id, multi-tenant winery_id scoping
- Update status operations work correctly
- Query methods filter correctly (by status, by winery)
- SQLAlchemy mappings work
- Transactions and rollbacks work properly
- Multi-tenant isolation works correctly

Database: localhost:5433/wine_fermentation_test

NOTE: This tests ONLY FermentationRepository operations.
Sample queries are the responsibility of SampleRepository (test_sample_repository_integration.py)
"""

import pytest
from datetime import datetime
from sqlalchemy import select

from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.domain.dtos import FermentationCreate

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestFermentationRepositoryCRUD:
    """Integration tests for basic create and get operations."""

    @pytest.mark.asyncio
    async def test_create_fermentation_persists_to_database(
        self,
        test_models,
        fermentation_repository,
        test_user,
        db_session,
    ):
        """
        Test that create() persists Fermentation to PostgreSQL.
        
        GIVEN a valid FermentationCreate DTO
        WHEN create() is called
        THEN the fermentation should be persisted with ID assigned
        AND should be retrievable from the database
        """
        # Arrange
        Fermentation = test_models['Fermentation']
        
        fermentation_data = FermentationCreate(
            fermented_by_user_id=test_user.id,
            vintage_year=2024,
            yeast_strain="EC-1118",
            vessel_code="TANK-01",
            input_mass_kg=500.0,
            initial_sugar_brix=23.5,
            initial_density=1.098,
            start_date=datetime(2024, 10, 1, 10, 0, 0),
        )
        
        # Act
        created = await fermentation_repository.create(
            winery_id=test_user.winery_id,
            data=fermentation_data
        )
        await db_session.flush()
        
        # Assert
        assert created.id is not None, "ID should be assigned after create"
        assert created.winery_id == test_user.winery_id
        assert created.vessel_code == "TANK-01"
        assert created.status == FermentationStatus.ACTIVE
        
        # Verify persistence
        result = await db_session.execute(
            select(Fermentation).where(Fermentation.id == created.id)
        )
        persisted = result.scalar_one()
        assert persisted.vessel_code == "TANK-01"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_fermentation_with_winery_scoping(
        self,
        fermentation_repository,
        test_fermentation,
        test_user,
    ):
        """
        Test that get_by_id() requires winery_id for multi-tenant security.
        
        GIVEN a fermentation exists
        WHEN get_by_id() is called with correct winery_id
        THEN fermentation should be returned
        """
        # Act
        retrieved = await fermentation_repository.get_by_id(
            fermentation_id=test_fermentation.id,
            winery_id=test_user.winery_id
        )
        
        # Assert
        assert retrieved is not None
        assert retrieved.id == test_fermentation.id
        assert retrieved.vessel_code == test_fermentation.vessel_code
        assert retrieved.winery_id == test_user.winery_id

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self,
        fermentation_repository,
        test_user,
    ):
        """
        Test that get_by_id() returns None for non-existent ID.
        
        GIVEN a non-existent fermentation ID
        WHEN get_by_id() is called
        THEN None should be returned
        """
        # Act
        result = await fermentation_repository.get_by_id(
            fermentation_id=99999,
            winery_id=test_user.winery_id
        )
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_enforces_winery_isolation(
        self,
        test_models,
        fermentation_repository,
        test_fermentation,
        test_user,
        db_session,
    ):
        """
        Test that get_by_id() enforces multi-tenant isolation.
        
        GIVEN a fermentation for winery 1
        WHEN get_by_id() is called with winery 2's ID
        THEN None should be returned (security isolation)
        """
        # Arrange: Create another winery
        from uuid import uuid4
        Winery = test_models['Winery']
        other_winery = Winery(
            id=999,
            code=f"OTHER-{uuid4().hex[:8].upper()}",
            name="Other Winery",
            location="Other Region"
        )
        db_session.add(other_winery)
        await db_session.flush()
        
        # Act - Try to access test_fermentation with wrong winery_id
        result = await fermentation_repository.get_by_id(
            fermentation_id=test_fermentation.id,
            winery_id=other_winery.id  # WRONG winery
        )
        
        # Assert
        assert result is None, "Should not return fermentation from different winery"


class TestFermentationRepositoryStatusUpdate:
    """Integration tests for status update operations."""

    @pytest.mark.asyncio
    async def test_update_status_persists_changes(
        self,
        test_models,
        fermentation_repository,
        test_fermentation,
        test_user,
        db_session,
    ):
        """
        Test that update_status() persists status changes to database.
        
        GIVEN an existing active fermentation
        WHEN update_status() is called with COMPLETED status
        THEN status should be updated and persisted
        """
        # Arrange
        Fermentation = test_models['Fermentation']
        
        # Act
        updated = await fermentation_repository.update_status(
            fermentation_id=test_fermentation.id,
            winery_id=test_user.winery_id,
            new_status=FermentationStatus.COMPLETED
        )
        await db_session.flush()
        
        # Assert
        assert updated.status == FermentationStatus.COMPLETED
        
        # Verify persistence
        result = await db_session.execute(
            select(Fermentation).where(Fermentation.id == test_fermentation.id)
        )
        persisted = result.scalar_one()
        assert persisted.status == FermentationStatus.COMPLETED.value


class TestFermentationRepositoryQueries:
    """Integration tests for query methods."""

    @pytest.mark.asyncio
    async def test_get_by_status_filters_correctly(
        self,
        fermentation_repository,
        test_user,
        db_session,
    ):
        """
        Test that get_by_status() returns only fermentations with matching status.
        
        GIVEN multiple fermentations with different statuses
        WHEN get_by_status() is called with ACTIVE status
        THEN only active fermentations should be returned
        """
        # Arrange: Create fermentations with different statuses
        active_data = FermentationCreate(
            fermented_by_user_id=test_user.id,
            vintage_year=2024,
            yeast_strain="EC-1118",
            vessel_code="TANK-ACTIVE",
            input_mass_kg=500.0,
            initial_sugar_brix=23.5,
            initial_density=1.095,
            start_date=datetime.now(),
        )
        
        completed_data = FermentationCreate(
            fermented_by_user_id=test_user.id,
            vintage_year=2024,
            yeast_strain="D47",
            vessel_code="TANK-COMPLETED",
            input_mass_kg=400.0,
            initial_sugar_brix=22.0,
            initial_density=1.090,
            start_date=datetime.now(),
        )
        
        active_ferm = await fermentation_repository.create(
            winery_id=test_user.winery_id,
            data=active_data
        )
        
        completed_ferm = await fermentation_repository.create(
            winery_id=test_user.winery_id,
            data=completed_data
        )
        
        # Update completed fermentation's status
        await fermentation_repository.update_status(
            fermentation_id=completed_ferm.id,
            winery_id=test_user.winery_id,
            new_status=FermentationStatus.COMPLETED
        )
        
        await db_session.flush()
        
        # Act - Get only ACTIVE fermentations
        active_results = await fermentation_repository.get_by_status(
            status=FermentationStatus.ACTIVE,
            winery_id=test_user.winery_id
        )
        
        # Assert
        assert len(active_results) >= 1, "Should return at least one active fermentation"
        for ferm in active_results:
            assert ferm.status == FermentationStatus.ACTIVE
            assert ferm.winery_id == test_user.winery_id

    @pytest.mark.asyncio
    async def test_get_active_by_winery_filters_correctly(
        self,
        test_models,
        fermentation_repository,
        test_user,
        db_session,
    ):
        """
        Test that get_active_by_winery() returns only active fermentations for winery.
        
        GIVEN active and completed fermentations for multiple wineries
        WHEN get_active_by_winery() is called
        THEN only active fermentations for specified winery should be returned
        """
        # Arrange: Create second winery
        from uuid import uuid4
        Winery = test_models['Winery']
        winery2 = Winery(
            id=999,
            code=f"OTHER-{uuid4().hex[:8].upper()}",
            name="Other Winery",
            location="Other Region"
        )
        db_session.add(winery2)
        await db_session.flush()
        
        # Active fermentation for test_user's winery
        active_data = FermentationCreate(
            fermented_by_user_id=test_user.id,
            vintage_year=2024,
            yeast_strain="EC-1118",
            vessel_code="TANK-ACTIVE-1",
            input_mass_kg=500.0,
            initial_sugar_brix=23.5,
            initial_density=1.095,
            start_date=datetime.now(),
        )
        
        active1 = await fermentation_repository.create(
            winery_id=test_user.winery_id,
            data=active_data
        )
        
        # Completed fermentation for test_user's winery
        completed_data = FermentationCreate(
            fermented_by_user_id=test_user.id,
            vintage_year=2024,
            yeast_strain="D47",
            vessel_code="TANK-COMPLETED-1",
            input_mass_kg=400.0,
            initial_sugar_brix=22.0,
            initial_density=1.090,
            start_date=datetime.now(),
        )
        
        completed1 = await fermentation_repository.create(
            winery_id=test_user.winery_id,
            data=completed_data
        )
        
        await fermentation_repository.update_status(
            fermentation_id=completed1.id,
            winery_id=test_user.winery_id,
            new_status=FermentationStatus.COMPLETED
        )
        
        # Active fermentation for OTHER winery
        active_other_data = FermentationCreate(
            fermented_by_user_id=test_user.id,
            vintage_year=2024,
            yeast_strain="D47",
            vessel_code="TANK-OTHER",
            input_mass_kg=300.0,
            initial_sugar_brix=21.0,
            initial_density=1.088,
            start_date=datetime.now(),
        )
        
        await fermentation_repository.create(
            winery_id=winery2.id,
            data=active_other_data
        )
        
        await db_session.flush()
        
        # Act
        results = await fermentation_repository.get_active_by_winery(test_user.winery_id)
        
        # Assert
        assert len(results) >= 1, "Should return at least one active fermentation for winery"
        for ferm in results:
            assert ferm.status == FermentationStatus.ACTIVE
            assert ferm.winery_id == test_user.winery_id
        
        # Verify completed is NOT included
        vessel_codes = {f.vessel_code for f in results}
        assert "TANK-COMPLETED-1" not in vessel_codes
        assert "TANK-OTHER" not in vessel_codes

    @pytest.mark.asyncio
    async def test_get_by_winery_with_include_completed(
        self,
        fermentation_repository,
        test_user,
        db_session,
    ):
        """
        Test that get_by_winery() can include or exclude completed fermentations.
        
        GIVEN active and completed fermentations
        WHEN get_by_winery() is called with include_completed=True/False
        THEN results should be filtered correctly
        """
        # Arrange
        active_data = FermentationCreate(
            fermented_by_user_id=test_user.id,
            vintage_year=2024,
            yeast_strain="EC-1118",
            vessel_code="TANK-ACTIVE",
            input_mass_kg=500.0,
            initial_sugar_brix=23.5,
            initial_density=1.095,
            start_date=datetime.now(),
        )
        
        completed_data = FermentationCreate(
            fermented_by_user_id=test_user.id,
            vintage_year=2024,
            yeast_strain="D47",
            vessel_code="TANK-COMPLETED",
            input_mass_kg=400.0,
            initial_sugar_brix=22.0,
            initial_density=1.090,
            start_date=datetime.now(),
        )
        
        await fermentation_repository.create(
            winery_id=test_user.winery_id,
            data=active_data
        )
        
        completed = await fermentation_repository.create(
            winery_id=test_user.winery_id,
            data=completed_data
        )
        
        await fermentation_repository.update_status(
            fermentation_id=completed.id,
            winery_id=test_user.winery_id,
            new_status=FermentationStatus.COMPLETED
        )
        
        await db_session.flush()
        
        # Act
        all_results = await fermentation_repository.get_by_winery(
            winery_id=test_user.winery_id,
            include_completed=True
        )
        
        active_only = await fermentation_repository.get_by_winery(
            winery_id=test_user.winery_id,
            include_completed=False
        )
        
        # Assert
        assert len(all_results) > len(active_only), "Including completed should return more results"
        
        statuses_all = {f.status for f in all_results}
        assert FermentationStatus.ACTIVE in statuses_all
        assert FermentationStatus.COMPLETED in statuses_all
        
        statuses_active = {f.status for f in active_only}
        assert FermentationStatus.COMPLETED not in statuses_active
