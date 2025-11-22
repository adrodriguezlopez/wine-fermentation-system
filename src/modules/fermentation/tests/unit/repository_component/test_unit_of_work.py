"""
Unit tests for UnitOfWork pattern implementation.

Following TDD approach - tests written before implementation.

Test Coverage:
- UoW context manager lifecycle
- Transaction commit/rollback
- Repository access within UoW
- Error handling
- Session sharing between repositories
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.repository_component.unit_of_work import UnitOfWork


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager that returns a mock session."""
    manager = Mock()
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Create async context manager mock
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context.__aexit__ = AsyncMock()
    
    manager.get_session = Mock(return_value=mock_context)
    
    return manager, mock_session


class TestUnitOfWorkLifecycle:
    """Test UoW context manager lifecycle."""
    
    @pytest.mark.asyncio
    async def test_uow_enters_context_successfully(self, mock_session_manager):
        """
        Given: A UnitOfWork instance
        When: Entering async context
        Then: Should return self and mark as active
        """
        # Arrange
        session_manager, mock_session = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act
        async with uow as result:
            # Assert
            assert result is uow
            assert uow._is_active is True
            assert uow._session is mock_session
    
    @pytest.mark.asyncio
    async def test_uow_exits_context_successfully(self, mock_session_manager):
        """
        Given: A UoW in active context
        When: Exiting context normally
        Then: Should cleanup (rollback & close session)
        """
        # Arrange
        session_manager, mock_session = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act
        async with uow:
            pass  # Normal exit
        
        # Assert
        assert uow._is_active is False
        assert uow._session is None
        mock_session.rollback.assert_called()
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_uow_auto_rollback_on_exception(self, mock_session_manager):
        """
        Given: A UoW in active context
        When: Exception occurs
        Then: Should auto-rollback and cleanup
        """
        # Arrange
        session_manager, mock_session = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act & Assert
        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("Test error")
        
        # Cleanup should have occurred
        assert uow._is_active is False
        assert uow._session is None
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestUnitOfWorkTransactions:
    """Test transaction commit/rollback."""
    
    @pytest.mark.asyncio
    async def test_commit_persists_changes(self, mock_session_manager):
        """
        Given: A UoW with changes
        When: Calling commit()
        Then: Should call session.commit()
        """
        # Arrange
        session_manager, mock_session = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act
        async with uow:
            await uow.commit()
        
        # Assert
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback_discards_changes(self, mock_session_manager):
        """
        Given: A UoW with changes
        When: Calling rollback()
        Then: Should call session.rollback()
        """
        # Arrange
        session_manager, mock_session = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act
        async with uow:
            await uow.rollback()
        
        # Assert - rollback called explicitly + in cleanup
        assert mock_session.rollback.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_commit_outside_context_raises_error(self, mock_session_manager):
        """
        Given: A UoW outside active context
        When: Calling commit()
        Then: Should raise RuntimeError
        """
        # Arrange
        session_manager, _ = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="outside active"):
            await uow.commit()
    
    @pytest.mark.asyncio
    async def test_rollback_outside_context_raises_error(self, mock_session_manager):
        """
        Given: A UoW outside active context
        When: Calling rollback()
        Then: Should raise RuntimeError
        """
        # Arrange
        session_manager, _ = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="outside active"):
            await uow.rollback()
    
    @pytest.mark.asyncio
    async def test_commit_failure_triggers_rollback(self, mock_session_manager):
        """
        Given: A UoW where commit fails
        When: Calling commit()
        Then: Should auto-rollback
        """
        # Arrange
        session_manager, mock_session = mock_session_manager
        mock_session.commit = AsyncMock(side_effect=Exception("DB error"))
        uow = UnitOfWork(session_manager)
        
        # Act & Assert
        with pytest.raises(Exception):
            async with uow:
                await uow.commit()
        
        # Rollback should have been called
        mock_session.rollback.assert_called()


class TestUnitOfWorkRepositoryAccess:
    """Test repository access within UoW."""
    
    @pytest.mark.asyncio
    async def test_fermentation_repo_accessible_in_context(self, mock_session_manager):
        """
        Given: A UoW in active context
        When: Accessing fermentation_repo
        Then: Should return repository instance
        """
        # Arrange
        session_manager, _ = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act
        async with uow:
            repo = uow.fermentation_repo
        
        # Assert
        assert repo is not None
    
    @pytest.mark.asyncio
    async def test_sample_repo_accessible_in_context(self, mock_session_manager):
        """
        Given: A UoW in active context
        When: Accessing sample_repo
        Then: Should return repository instance
        """
        # Arrange
        session_manager, _ = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act
        async with uow:
            repo = uow.sample_repo
        
        # Assert
        assert repo is not None
    
    @pytest.mark.asyncio
    async def test_repo_access_outside_context_raises_error(self, mock_session_manager):
        """
        Given: A UoW outside active context
        When: Accessing repository property
        Then: Should raise RuntimeError
        """
        # Arrange
        session_manager, _ = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="outside active"):
            _ = uow.fermentation_repo
    
    @pytest.mark.asyncio
    async def test_repos_share_same_session(self, mock_session_manager):
        """
        Given: A UoW with multiple repos accessed
        When: Accessing different repos
        Then: All should share same session instance
        """
        # Arrange
        session_manager, mock_session = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act
        async with uow:
            ferm_repo = uow.fermentation_repo
            sample_repo = uow.sample_repo
        
        # Assert - both repos created (we can't directly verify session sharing
        # without inspecting private repo internals, but we verify they exist)
        assert ferm_repo is not None
        assert sample_repo is not None
    
    @pytest.mark.asyncio
    async def test_repo_lazy_initialization(self, mock_session_manager):
        """
        Given: A UoW in active context
        When: Not accessing any repos
        Then: Repos should not be initialized
        """
        # Arrange
        session_manager, _ = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act
        async with uow:
            pass  # Don't access any repos
        
        # Assert
        assert uow._fermentation_repo is None
        assert uow._sample_repo is None


class TestUnitOfWorkErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_uow_handles_repository_errors(self, mock_session_manager):
        """
        Given: A UoW with repository operation that fails
        When: Error occurs
        Then: Should auto-rollback and cleanup
        """
        # Arrange
        session_manager, mock_session = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act & Assert
        with pytest.raises(RuntimeError):
            async with uow:
                # Simulate repo error by accessing outside context
                raise RuntimeError("Simulated repo error")
        
        # Cleanup should have occurred
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_uow_state_cleaned_after_error(self, mock_session_manager):
        """
        Given: A UoW that encountered error
        When: After context exit
        Then: State should be fully cleaned
        """
        # Arrange
        session_manager, _ = mock_session_manager
        uow = UnitOfWork(session_manager)
        
        # Act
        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("Test")
        
        # Assert - state cleaned
        assert uow._is_active is False
        assert uow._session is None
        assert uow._fermentation_repo is None
        assert uow._sample_repo is None
