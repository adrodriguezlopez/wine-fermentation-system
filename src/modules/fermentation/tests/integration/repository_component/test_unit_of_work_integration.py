"""
Integration tests for UnitOfWork pattern.

These tests use a REAL database to validate:
- Actual transaction commit/rollback
- Real session sharing between repositories
- Database-level atomicity
- Concurrent modification handling

Unlike unit tests (which mock the session), integration tests verify
that UnitOfWork works correctly with actual PostgreSQL database.

Test Strategy:
- Use test database (not production)
- Each test runs in isolated transaction
- Cleanup after each test
- Validate actual DB state changes

Related: ADR-002 (UnitOfWork pattern), test_unit_of_work.py (unit tests)
"""

import pytest
from datetime import datetime
from decimal import Decimal
from contextlib import asynccontextmanager

from src.modules.fermentation.src.repository_component.unit_of_work import UnitOfWork
from src.modules.fermentation.src.domain.dtos import FermentationCreate
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.domain.enums.sample_type import SampleType


@pytest.fixture
def session_manager_factory(db_session):
    """
    Create a session manager factory for UnitOfWork.
    
    The db_session fixture provides a session that's already in a transaction
    context. To allow multiple UoW contexts to reuse this session, we need to:
    1. Intercept commit/rollback to use savepoints instead of committing the parent transaction
    2. Intercept close() to prevent closing the shared test session
    
    Args:
        db_session: Test database session from conftest (already in transaction)
    
    Returns:
        Callable that returns async context manager for session
    """
    @asynccontextmanager
    async def get_session():
        """
        Async context manager that yields a wrapped session.
        
        The wrapper intercepts commit/rollback/close to allow multiple UoW contexts
        on the same test session.
        """
        # Wrap the session to intercept transactional operations
        class SessionWrapper:
            def __init__(self, real_session):
                self._real_session = real_session
                self._savepoint = None
            
            async def commit(self):
                """Commit the savepoint instead of the parent transaction."""
                if self._savepoint and self._savepoint.is_active:
                    await self._savepoint.commit()
            
            async def rollback(self):
                """Rollback the savepoint instead of the parent transaction."""
                if self._savepoint and self._savepoint.is_active:
                    await self._savepoint.rollback()
            
            async def close(self):
                """No-op - don't close the shared test session."""
                # Close the savepoint if still active
                if self._savepoint and self._savepoint.is_active:
                    await self._savepoint.close()
            
            async def flush(self, *args, **kwargs):
                """Delegate flush to real session."""
                return await self._real_session.flush(*args, **kwargs)
            
            async def execute(self, *args, **kwargs):
                """Delegate execute to real session."""
                return await self._real_session.execute(*args, **kwargs)
            
            async def begin_nested(self):
                """Create a savepoint for this UoW context."""
                self._savepoint = await self._real_session.begin_nested()
                return self._savepoint
            
            def __getattr__(self, name):
                """Delegate all other attributes to the real session."""
                return getattr(self._real_session, name)
        
        # Create wrapper and start a savepoint
        wrapper = SessionWrapper(db_session)
        await wrapper.begin_nested()
        
        try:
            yield wrapper
        finally:
            # Cleanup: close savepoint if still active
            if wrapper._savepoint and wrapper._savepoint.is_active:
                await wrapper._savepoint.close()
    
    return get_session



@pytest.fixture
def uow(session_manager_factory):
    """
    Create a UnitOfWork instance with test session factory.
    
    Args:
        session_manager_factory: Callable that returns session context manager
    
    Returns:
        UnitOfWork: UnitOfWork instance for integration testing
    """
    # Wrap session_manager_factory to match ISessionManager interface
    # UnitOfWork expects an object with get_session() method that returns an async context manager
    # For testing, we need to ensure the session can be reused across multiple UoW contexts
    class SessionManagerWrapper:
        def __init__(self, session_func):
            self._session_func = session_func
        
        def get_session(self):
            """Return an async context manager for the session."""
            # Return the context manager directly - it will handle session lifecycle
            return self._session_func()
        
        async def close(self):
            """No-op for test fixture - db_session fixture handles cleanup."""
            pass
    
    wrapped_manager = SessionManagerWrapper(session_manager_factory)
    return UnitOfWork(wrapped_manager)


class TestUnitOfWorkTransactionCommit:
    """Test that UoW commits actually persist to database."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_commit_persists_fermentation_to_database(self, uow):
        """
        Given: A UoW with a new fermentation created
        When: Calling commit()
        Then: Fermentation should be persisted in database
        
        Validates:
        - Fermentation is written to DB
        - ID is generated by database
        - Data integrity is maintained
        """
        # Arrange
        fermentation_data = FermentationCreate(
            fermented_by_user_id=1,
            vintage_year=2024,
            yeast_strain="Test Yeast",
            vessel_code="V-TEST-001",
            input_mass_kg=Decimal("100.50"),
            initial_sugar_brix=Decimal("22.5"),
            initial_density=Decimal("1.095"),
            start_date=datetime(2024, 11, 15)
        )
        winery_id = 1
        fermentation_id = None
        
        # Act - Create fermentation and commit
        async with uow:
            fermentation = await uow.fermentation_repo.create(
                winery_id=winery_id,
                data=fermentation_data
            )
            fermentation_id = fermentation.id
            await uow.commit()
        
        # Assert - Verify fermentation exists in database
        async with uow:
            retrieved = await uow.fermentation_repo.get_by_id(
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
            assert retrieved is not None
            assert retrieved.id == fermentation_id
            assert retrieved.vessel_code == "V-TEST-001"
            assert retrieved.status == FermentationStatus.ACTIVE
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_commit_persists_multiple_operations(self, uow):
        """
        Given: A UoW with fermentation + sample created
        When: Calling commit()
        Then: Both operations should be persisted atomically
        
        Validates:
        - Multiple repo operations in one transaction
        - Atomicity (all or nothing)
        - Cross-repository transaction coordination
        """
        # Arrange
        fermentation_data = FermentationCreate(
            fermented_by_user_id=1,
            vintage_year=2024,
            yeast_strain="Multi-Op Test",
            vessel_code="V-MULTI-001",
            input_mass_kg=Decimal("200.0"),
            initial_sugar_brix=Decimal("24.0"),
            initial_density=Decimal("1.100"),
            start_date=datetime(2024, 11, 15)
        )
        winery_id = 1
        
        # Act - Create fermentation AND sample in same transaction
        async with uow:
            fermentation = await uow.fermentation_repo.create(
                winery_id=winery_id,
                data=fermentation_data
            )
            fermentation_id = fermentation.id
            
            # Create sample for this fermentation
            from src.modules.fermentation.src.domain.entities.samples.sugar_sample import SugarSample
            sample = SugarSample(
                fermentation_id=fermentation_id,
                recorded_at=datetime(2024, 11, 16),
                recorded_by_user_id=1,
                value=20.5,
                sample_type=SampleType.SUGAR.value
            )
            sample = await uow.sample_repo.create(sample)
            sample_id = sample.id
            
            await uow.commit()
        
        # Assert - Both should exist in database
        async with uow:
            retrieved_ferm = await uow.fermentation_repo.get_by_id(
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
            # Get sample with proper access control parameters
            retrieved_sample = await uow.sample_repo.get_sample_by_id(
                sample_id=sample_id,
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
            
            assert retrieved_ferm is not None
            assert retrieved_sample is not None
            assert retrieved_sample.fermentation_id == fermentation_id


class TestUnitOfWorkTransactionRollback:
    """Test that UoW rollback actually discards changes."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rollback_discards_fermentation_creation(self, uow):
        """
        Given: A UoW with a new fermentation created
        When: Calling rollback() instead of commit()
        Then: Fermentation should NOT be in database
        
        Validates:
        - Rollback actually discards changes
        - No partial data in database
        - Database remains consistent
        """
        # Arrange
        fermentation_data = FermentationCreate(
            fermented_by_user_id=1,
            vintage_year=2024,
            yeast_strain="Rollback Test",
            vessel_code="V-ROLLBACK-001",
            input_mass_kg=Decimal("100.0"),
            initial_sugar_brix=Decimal("22.0"),
            initial_density=Decimal("1.090"),
            start_date=datetime(2024, 11, 15)
        )
        winery_id = 1
        fermentation_id = None
        
        # Act - Create fermentation but rollback
        async with uow:
            fermentation = await uow.fermentation_repo.create(
                winery_id=winery_id,
                data=fermentation_data
            )
            fermentation_id = fermentation.id
            await uow.rollback()
        
        # Assert - Fermentation should NOT exist in database
        async with uow:
            retrieved = await uow.fermentation_repo.get_by_id(
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
            assert retrieved is None
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_auto_rollback_on_exception(self, uow):
        """
        Given: A UoW where exception occurs after creation
        When: Exception is raised before commit
        Then: All changes should be rolled back automatically
        
        Validates:
        - Automatic rollback on exception
        - Transaction safety
        - No orphaned data in database
        """
        # Arrange
        fermentation_data = FermentationCreate(
            fermented_by_user_id=1,
            vintage_year=2024,
            yeast_strain="Exception Test",
            vessel_code="V-EXCEPTION-001",
            input_mass_kg=Decimal("100.0"),
            initial_sugar_brix=Decimal("22.0"),
            initial_density=Decimal("1.090"),
            start_date=datetime(2024, 11, 15)
        )
        winery_id = 1
        fermentation_id = None
        
        # Act - Create fermentation but raise exception
        with pytest.raises(ValueError):
            async with uow:
                fermentation = await uow.fermentation_repo.create(
                    winery_id=winery_id,
                    data=fermentation_data
                )
                fermentation_id = fermentation.id
                raise ValueError("Simulated error")
        
        # Assert - Fermentation should NOT exist (auto-rollback)
        async with uow:
            retrieved = await uow.fermentation_repo.get_by_id(
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
            assert retrieved is None


class TestUnitOfWorkSessionSharing:
    """Test that repositories share the same session within UoW."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_repos_see_uncommitted_changes(self, uow):
        """
        Given: A UoW with fermentation created (not committed)
        When: Accessing fermentation through another repo query
        Then: Should see the uncommitted fermentation (same session)
        
        Validates:
        - Repositories share same database session
        - Uncommitted changes visible within transaction
        - Proper transaction isolation
        """
        # Arrange
        fermentation_data = FermentationCreate(
            fermented_by_user_id=1,
            vintage_year=2024,
            yeast_strain="Session Share Test",
            vessel_code="V-SESSION-001",
            input_mass_kg=Decimal("100.0"),
            initial_sugar_brix=Decimal("22.0"),
            initial_density=Decimal("1.090"),
            start_date=datetime(2024, 11, 15)
        )
        winery_id = 1
        
        # Act & Assert
        async with uow:
            # Create fermentation
            fermentation = await uow.fermentation_repo.create(
                winery_id=winery_id,
                data=fermentation_data
            )
            fermentation_id = fermentation.id
            
            # Query it back through same UoW (should see it)
            retrieved = await uow.fermentation_repo.get_by_id(
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
            
            # Within same UoW, should see uncommitted fermentation
            assert retrieved is not None
            assert retrieved.id == fermentation_id
            
            # Don't commit - let it rollback
            await uow.rollback()


class TestUnitOfWorkAtomicity:
    """Test that UoW provides true atomicity (all-or-nothing)."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_partial_failure_rolls_back_all(self, uow):
        """
        Given: A UoW with multiple operations where one fails
        When: Second operation raises error
        Then: First operation should also be rolled back
        
        Validates:
        - True atomicity (all or nothing)
        - No partial state in database
        - Transaction consistency
        """
        # Arrange
        fermentation_data = FermentationCreate(
            fermented_by_user_id=1,
            vintage_year=2024,
            yeast_strain="Atomicity Test",
            vessel_code="V-ATOMIC-001",
            input_mass_kg=Decimal("100.0"),
            initial_sugar_brix=Decimal("22.0"),
            initial_density=Decimal("1.090"),
            start_date=datetime(2024, 11, 15)
        )
        winery_id = 1
        fermentation_id = None
        
        # Act - Create fermentation, then fail on sample creation
        with pytest.raises(Exception):
            async with uow:
                fermentation = await uow.fermentation_repo.create(
                    winery_id=winery_id,
                    data=fermentation_data
                )
                fermentation_id = fermentation.id
                
                # Try to create invalid sample (should fail)
                await uow.sample_repo.create_sample(
                    winery_id=winery_id,
                    fermentation_id=9999999,  # Invalid FK - will fail
                    sample_type=SampleType.SUGAR,
                    sample_date=datetime(2024, 11, 16),
                    measured_by_user_id=1,
                    value=Decimal("20.0")
                )
        
        # Assert - Fermentation should NOT exist (atomicity)
        async with uow:
            retrieved = await uow.fermentation_repo.get_by_id(
                fermentation_id=fermentation_id,
                winery_id=winery_id
            )
            assert retrieved is None
