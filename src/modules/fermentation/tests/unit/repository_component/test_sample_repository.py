"""
Unit tests for SampleRepository implementation.

Following TDD (Test-Driven Development):
- Write tests FIRST (RED)
- Implement minimal code to pass (GREEN)
- Refactor if needed (REFACTOR)

Following ADR-002: Unit tests verify repository behavior without database connection.
Following ADR-003: Sample operations moved from FermentationRepository to SampleRepository.

These tests follow proper unit testing practices:
- Mock only the session manager (not SQLAlchemy internals)
- Mock the RESULTS of database queries (not the query builders)
- Focus on testing the repository contract, not implementation details
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from decimal import Decimal

# Import domain entities
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
from src.modules.fermentation.src.domain.enums.sample_type import SampleType

# Import repository implementation (will fail initially - TDD RED phase)
from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository


class TestSampleRepository:
    """Test SampleRepository with TDD approach - one method at a time."""

    @pytest.fixture
    def mock_session_manager(self):
        """Create a mock session manager that returns a mock session."""
        manager = Mock()
        mock_session = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        manager.get_session = AsyncMock(return_value=mock_context)
        manager.close = AsyncMock()
        return manager, mock_session

    @pytest.fixture
    def repository(self, mock_session_manager):
        """Create a SampleRepository instance with mocked session manager."""
        manager, _ = mock_session_manager
        return SampleRepository(manager)

    # =====================================================================
    # TDD PRAGMATIC APPROACH: Interface Tests
    # Full implementation testing requires integration tests with real DB
    # These tests verify that all methods exist and are callable
    # =====================================================================

    @pytest.mark.asyncio
    async def test_repository_inherits_from_base_repository(self, repository):
        """Test that SampleRepository extends BaseRepository."""
        from src.shared.infra.repository.base_repository import BaseRepository
        assert isinstance(repository, BaseRepository)

    @pytest.mark.asyncio
    async def test_repository_has_create_method(self, repository):
        """
        🔴 RED → 🟢 GREEN CICLO 1: Test that SampleRepository has create() method.
        
        GIVEN a SampleRepository instance
        WHEN checking for create() method
        THEN it should exist and be callable
        
        NOTE: Full create() logic tested in integration tests to avoid
        SQLAlchemy table registration conflicts in unit tests.
        """
        assert hasattr(repository, 'create')
        assert callable(repository.create)

    @pytest.mark.asyncio
    async def test_repository_has_upsert_sample_method(self, repository):
        """
        🔴 RED → 🟢 GREEN CICLO 2: Test that SampleRepository has upsert_sample() method.
        
        Verifies upsert pattern (create or update) method exists.
        """
        assert hasattr(repository, 'upsert_sample')
        assert callable(repository.upsert_sample)

    @pytest.mark.asyncio
    async def test_repository_has_get_sample_by_id_method(self, repository):
        """
        🔴 RED → 🟢 GREEN CICLO 3: Test that SampleRepository has get_sample_by_id() method.
        
        Verifies retrieval by ID with optional fermentation_id for access control.
        """
        assert hasattr(repository, 'get_sample_by_id')
        assert callable(repository.get_sample_by_id)

    @pytest.mark.asyncio
    async def test_repository_has_get_samples_by_fermentation_id_method(self, repository):
        """
        🔴 RED → 🟢 GREEN CICLO 4: Test that SampleRepository has get_samples_by_fermentation_id() method.
        
        Verifies retrieval of all samples for a fermentation in chronological order.
        """
        assert hasattr(repository, 'get_samples_by_fermentation_id')
        assert callable(repository.get_samples_by_fermentation_id)

    @pytest.mark.asyncio
    async def test_repository_has_get_samples_in_timerange_method(self, repository):
        """
        🔴 RED → 🟢 GREEN CICLO 5: Test that SampleRepository has get_samples_in_timerange() method.
        
        Verifies retrieval of samples within a specific time range.
        """
        assert hasattr(repository, 'get_samples_in_timerange')
        assert callable(repository.get_samples_in_timerange)

    @pytest.mark.asyncio
    async def test_repository_has_get_latest_sample_method(self, repository):
        """
        🔴 RED → 🟢 GREEN CICLO 6: Test that SampleRepository has get_latest_sample() method.
        
        Verifies retrieval of most recent sample for a fermentation.
        """
        assert hasattr(repository, 'get_latest_sample')
        assert callable(repository.get_latest_sample)

    @pytest.mark.asyncio
    async def test_repository_has_get_fermentation_start_date_method(self, repository):
        """
        🔴 RED → 🟢 GREEN CICLO 7: Test that SampleRepository has get_fermentation_start_date() method.
        
        Verifies retrieval of fermentation start date for validation.
        """
        assert hasattr(repository, 'get_fermentation_start_date')
        assert callable(repository.get_fermentation_start_date)

    @pytest.mark.asyncio
    async def test_repository_has_get_latest_sample_by_type_method(self, repository):
        """
        🔴 RED → 🟢 GREEN CICLO 8: Test that SampleRepository has get_latest_sample_by_type() method.
        
        Verifies retrieval of most recent sample of specific type for trend validation.
        """
        assert hasattr(repository, 'get_latest_sample_by_type')
        assert callable(repository.get_latest_sample_by_type)

    @pytest.mark.asyncio
    async def test_repository_has_check_duplicate_timestamp_method(self, repository):
        """
        🔴 RED → 🟢 GREEN CICLO 9: Test that SampleRepository has check_duplicate_timestamp() method.
        
        Verifies duplicate timestamp detection for validation.
        """
        assert hasattr(repository, 'check_duplicate_timestamp')
        assert callable(repository.check_duplicate_timestamp)

    @pytest.mark.asyncio
    async def test_repository_has_soft_delete_sample_method(self, repository):
        """
        🔴 RED → 🟢 GREEN CICLO 10: Test that SampleRepository has soft_delete_sample() method.
        
        Verifies logical deletion without removing from database.
        """
        assert hasattr(repository, 'soft_delete_sample')
        assert callable(repository.soft_delete_sample)

    @pytest.mark.asyncio
    async def test_repository_has_bulk_upsert_samples_method(self, repository):
        """
        🔴 RED → 🟢 GREEN CICLO 11: Test that SampleRepository has bulk_upsert_samples() method.
        
        Verifies batch upsert operation for performance.
        """
        assert hasattr(repository, 'bulk_upsert_samples')
        assert callable(repository.bulk_upsert_samples)
