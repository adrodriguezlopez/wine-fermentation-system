"""
Unit tests for FermentationRepository.list_by_data_source() method (ADR-029)

Following ADR-012 testing patterns for proper mocking.
"""
import pytest
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.enums import DataSource

# Import ADR-012 testing utilities
from src.shared.testing.unit import (
    MockSessionManagerBuilder,
    create_query_result,
    create_empty_result,
    create_mock_entity,
)


class TestFermentationRepositoryListByDataSource:
    """Test suite for list_by_data_source() method"""

    def test_list_by_data_source_method_exists(self):
        """
        TDD RED: Repository should have list_by_data_source method.
        
        Given: FermentationRepository class
        When: Checking for list_by_data_source method
        Then: Method should exist
        """
        assert hasattr(FermentationRepository, 'list_by_data_source')
        assert callable(getattr(FermentationRepository, 'list_by_data_source'))

    @pytest.mark.asyncio
    async def test_list_by_data_source_filters_by_system(self):
        """
        Should return only fermentations with data_source='system'.
        
        Given: Repository with system fermentation
        When: Calling list_by_data_source(winery_id=1, data_source='system')
        Then: Returns only system fermentations
        """
        # Mock fermentation entity
        system_ferm = create_mock_entity(
            Fermentation,
            id=1,
            winery_id=1,
            data_source=DataSource.SYSTEM.value,
            is_deleted=False,
            fermented_by_user_id=1,
            status="ACTIVE",
            vintage_year=2024,
            yeast_strain="Test",
            input_mass_kg=100.0,
            initial_sugar_brix=20.0,
            initial_density=1.08
        )
        
        # Mock query result
        query_result = create_query_result([system_ferm])
        
        # Build session manager
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repo = FermentationRepository(session_manager)
        
        # Execute
        result = await repo.list_by_data_source(winery_id=1, data_source=DataSource.SYSTEM.value)
        
        # Verify
        assert len(result) == 1
        assert result[0].data_source == DataSource.SYSTEM.value

    @pytest.mark.asyncio
    async def test_list_by_data_source_filters_by_imported(self):
        """
        Should return only fermentations with data_source='imported'.
        """
        imported_ferm = create_mock_entity(
            Fermentation,
            id=2,
            winery_id=1,
            data_source=DataSource.IMPORTED.value,
            is_deleted=False,
            fermented_by_user_id=1,
            status="ACTIVE",
            vintage_year=2024,
            yeast_strain="Test",
            input_mass_kg=100.0,
            initial_sugar_brix=20.0,
            initial_density=1.08
        )
        
        query_result = create_query_result([imported_ferm])
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repo = FermentationRepository(session_manager)
        
        result = await repo.list_by_data_source(winery_id=1, data_source=DataSource.IMPORTED.value)
        
        assert len(result) == 1
        assert result[0].data_source == DataSource.IMPORTED.value

    @pytest.mark.asyncio
    async def test_list_by_data_source_filters_by_migrated(self):
        """
        Should return only fermentations with data_source='migrated'.
        """
        migrated_ferm = create_mock_entity(
            Fermentation,
            id=3,
            winery_id=1,
            data_source=DataSource.MIGRATED.value,
            is_deleted=False,
            fermented_by_user_id=1,
            status="ACTIVE",
            vintage_year=2024,
            yeast_strain="Test",
            input_mass_kg=100.0,
            initial_sugar_brix=20.0,
            initial_density=1.08
        )
        
        query_result = create_query_result([migrated_ferm])
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repo = FermentationRepository(session_manager)
        
        result = await repo.list_by_data_source(winery_id=1, data_source=DataSource.MIGRATED.value)
        
        assert len(result) == 1
        assert result[0].data_source == DataSource.MIGRATED.value

    @pytest.mark.asyncio
    async def test_list_by_data_source_enforces_winery_isolation(self):
        """
        Should only return fermentations for specified winery.
        """
        winery1_ferm = create_mock_entity(
            Fermentation,
            id=1,
            winery_id=1,
            data_source=DataSource.SYSTEM.value,
            fermented_by_user_id=1,
            status="ACTIVE",
            vintage_year=2024,
            yeast_strain="Test",
            input_mass_kg=100.0,
            initial_sugar_brix=20.0,
            initial_density=1.08
        )
        
        query_result = create_query_result([winery1_ferm])
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repo = FermentationRepository(session_manager)
        
        result = await repo.list_by_data_source(winery_id=1, data_source=DataSource.SYSTEM.value)
        
        assert all(f.winery_id == 1 for f in result)

    @pytest.mark.asyncio
    async def test_list_by_data_source_excludes_deleted_by_default(self):
        """
        Should exclude soft-deleted fermentations by default.
        """
        active_ferm = create_mock_entity(
            Fermentation,
            id=1,
            winery_id=1,
            data_source=DataSource.SYSTEM.value,
            is_deleted=False,
            fermented_by_user_id=1,
            status="ACTIVE",
            vintage_year=2024,
            yeast_strain="Test",
            input_mass_kg=100.0,
            initial_sugar_brix=20.0,
            initial_density=1.08
        )
        
        query_result = create_query_result([active_ferm])
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repo = FermentationRepository(session_manager)
        
        result = await repo.list_by_data_source(winery_id=1, data_source=DataSource.SYSTEM.value)
        
        assert all(not f.is_deleted for f in result)

    @pytest.mark.asyncio
    async def test_list_by_data_source_includes_deleted_when_requested(self):
        """
        Should include soft-deleted fermentations when requested.
        """
        active_ferm = create_mock_entity(
            Fermentation,
            id=1,
            winery_id=1,
            data_source=DataSource.SYSTEM.value,
            is_deleted=False,
            fermented_by_user_id=1,
            status="ACTIVE",
            vintage_year=2024,
            yeast_strain="Test",
            input_mass_kg=100.0,
            initial_sugar_brix=20.0,
            initial_density=1.08
        )
        deleted_ferm = create_mock_entity(
            Fermentation,
            id=2,
            winery_id=1,
            data_source=DataSource.SYSTEM.value,
            is_deleted=True,
            fermented_by_user_id=1,
            status="ACTIVE",
            vintage_year=2024,
            yeast_strain="Test",
            input_mass_kg=100.0,
            initial_sugar_brix=20.0,
            initial_density=1.08
        )
        
        query_result = create_query_result([active_ferm, deleted_ferm])
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repo = FermentationRepository(session_manager)
        
        result = await repo.list_by_data_source(
            winery_id=1,
            data_source=DataSource.SYSTEM.value,
            include_deleted=True
        )
        
        assert len(result) == 2
        assert any(f.is_deleted for f in result)

    @pytest.mark.asyncio
    async def test_list_by_data_source_returns_empty_list_when_no_matches(self):
        """
        Should return empty list when no fermentations match.
        """
        empty_result = create_empty_result()
        session_manager = MockSessionManagerBuilder().with_execute_result(empty_result).build()
        repo = FermentationRepository(session_manager)
        
        result = await repo.list_by_data_source(winery_id=1, data_source=DataSource.IMPORTED.value)
        
        assert result == []
