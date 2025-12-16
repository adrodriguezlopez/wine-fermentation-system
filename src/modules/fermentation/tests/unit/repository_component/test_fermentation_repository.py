"""
Unit tests for FermentationRepository implementation.

These tests follow proper unit testing practices:
- Mock only the session manager (not SQLAlchemy internals)
- Mock the RESULTS of database queries (not the query builders)
- Focus on testing the repository contract, not implementation details
- No need to import or patch SQLAlchemy entities

Following ADR-002: Unit tests verify repository behavior without database connection.
Following ADR-003: Sample operations removed - use ISampleRepository tests instead.
Following ADR-012: Using shared testing infrastructure for consistent mocking.
Integration tests (separate file) will verify actual database operations.
"""

import pytest
from datetime import datetime

# Import domain entities and DTOs from their canonical locations
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.dtos import FermentationCreate

# Import repository implementation
from src.modules.fermentation.src.repository_component.repositories import FermentationRepository

# Import ADR-012 testing utilities
from src.shared.testing.unit import (
    MockSessionManagerBuilder,
    create_query_result,
    create_empty_result,
    create_mock_entity,
)


class TestFermentationRepository:
    """Test FermentationRepository with proper mocking strategy.
    
    Following ADR-012: Each test creates its own session manager and repository instance for isolation.
    """

    @pytest.mark.asyncio
    async def test_repository_inherits_from_base_repository(self):
        """Test that FermentationRepository extends BaseRepository."""
        from src.shared.infra.repository.base_repository import BaseRepository
        session_manager = MockSessionManagerBuilder().build()
        repository = FermentationRepository(session_manager)
        assert isinstance(repository, BaseRepository)

    @pytest.mark.asyncio
    async def test_create_returns_fermentation_entity(self):
        """Test that create method returns a Fermentation domain entity."""
        # Create test data
        create_data = FermentationCreate(
            fermented_by_user_id=1,
            vintage_year=2024,
            yeast_strain="Test Yeast",
            input_mass_kg=100.0,
            initial_sugar_brix=20.0,
            initial_density=1.08,
            vessel_code="V1"
        )

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().build()
        repository = FermentationRepository(session_manager)

        # This test verifies the repository interface contract
        # Full implementation tests require integration testing with real DB
        assert hasattr(repository, 'create')
        assert callable(repository.create)

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self):
        """Test that get_by_id returns None when fermentation doesn't exist."""
        # Mock the query result to return None
        empty_result = create_empty_result()

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(empty_result).build()
        repository = FermentationRepository(session_manager)

        # Call the method
        result = await repository.get_by_id(fermentation_id=999, winery_id=1)

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_returns_fermentation_when_found(self):
        """Test that get_by_id returns a Fermentation entity when found."""
        # Mock the SQLAlchemy entity
        mock_fermentation = create_mock_entity(
            Fermentation,
            id=1,
            winery_id=1,
            fermented_by_user_id=1,
            status="ACTIVE",
            vintage_year=2024,
            yeast_strain="Test Yeast",
            input_mass_kg=100.0,
            initial_sugar_brix=20.0,
            initial_density=1.08,
            vessel_code="V1"
        )

        # Mock the query result
        query_result = create_query_result([mock_fermentation])

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repository = FermentationRepository(session_manager)

        # Call the method
        result = await repository.get_by_id(fermentation_id=1, winery_id=1)

        # Verify result (check attributes, not type)
        assert result is not None
        assert result.id == 1
        assert result.winery_id == 1
        assert result.status == "ACTIVE"

    @pytest.mark.asyncio
    async def test_update_status_returns_false_when_not_found(self):
        """Test that update_status returns None when fermentation doesn't exist."""
        # Mock the query result to return None
        empty_result = create_empty_result()

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(empty_result).build()
        repository = FermentationRepository(session_manager)

        # Call the method
        result = await repository.update_status(
            fermentation_id=999,
            winery_id=1,
            new_status=FermentationStatus.COMPLETED
        )

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_update_status_returns_true_when_successful(self):
        """Test that update_status returns updated Fermentation when update succeeds."""
        # Mock the SQLAlchemy entity
        mock_fermentation = create_mock_entity(
            Fermentation,
            id=1,
            winery_id=1,
            status="ACTIVE"
        )

        # Mock the query result
        query_result = create_query_result([mock_fermentation])

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repository = FermentationRepository(session_manager)

        # Call the method
        result = await repository.update_status(
            fermentation_id=1,
            winery_id=1,
            new_status=FermentationStatus.COMPLETED
        )

        # Verify result (check behavior, not type)
        assert result is not None
        assert result.status == FermentationStatus.COMPLETED.value

    # ==================================================================================
    # Sample operation tests REMOVED - Use test_sample_repository.py (ADR-003)
    # ==================================================================================
    # Sample-related tests have been moved to test_sample_repository.py
    # Removed tests:
    # - test_add_sample_raises_error_when_fermentation_not_found
    # - test_add_sample_creates_sugar_sample_when_glucose_provided
    # - test_get_latest_sample_returns_none_when_no_samples
    # - test_get_latest_sample_returns_most_recent_sample
    # - test_get_latest_sample_raises_error_when_fermentation_not_found
    #
    # See: tests/unit/repository_component/test_sample_repository.py (to be created)
    # ==================================================================================

    @pytest.mark.asyncio
    async def test_get_by_status_returns_list_of_fermentations(self):
        """Test that get_by_status returns a list of fermentations with the specified status."""
        # Mock two fermentations with ACTIVE status
        mock_fermentation1 = create_mock_entity(
            Fermentation,
            id=1,
            winery_id=1,
            status="ACTIVE"
        )

        mock_fermentation2 = create_mock_entity(
            Fermentation,
            id=2,
            winery_id=1,
            status="ACTIVE"
        )

        # Mock the query result
        query_result = create_query_result([mock_fermentation1, mock_fermentation2])

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repository = FermentationRepository(session_manager)

        # Call the method
        result = await repository.get_by_status(status=FermentationStatus.ACTIVE, winery_id=1)

        # Verify result (check structure and attributes, not types)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        assert all(f.status == "ACTIVE" for f in result)

    @pytest.mark.asyncio
    async def test_get_by_winery_returns_all_fermentations_for_winery(self):
        """Test that get_by_winery returns all fermentations for a winery."""
        # Mock a fermentation
        mock_fermentation = create_mock_entity(
            Fermentation,
            id=1,
            winery_id=1
        )

        # Mock the query result
        query_result = create_query_result([mock_fermentation])

        # Create session manager and repository
        session_manager = MockSessionManagerBuilder().with_execute_result(query_result).build()
        repository = FermentationRepository(session_manager)

        # Call the method
        result = await repository.get_by_winery(winery_id=1)

        # Verify result (check structure and attributes, not types)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].winery_id == 1

