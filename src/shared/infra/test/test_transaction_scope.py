"""
Tests for TransactionScope - Cross-module transaction coordination.

Tests the TransactionScope context manager that coordinates transactions
across multiple services, ensuring atomic operations with automatic
commit on success and rollback on exception.

Architecture: Infrastructure Layer Tests
Pattern: Unit Testing with Mocks
ADR: ADR-031 Cross-Module Transaction Coordination
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.shared.infra.session.transaction_scope import TransactionScope
from src.shared.infra.interfaces.session_manager import ISessionManager


class TestTransactionScope:
    """Test suite for TransactionScope context manager."""
    
    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager for testing."""
        mock = AsyncMock(spec=ISessionManager)
        mock.begin = AsyncMock()
        mock.commit = AsyncMock()
        mock.rollback = AsyncMock()
        return mock
    
    @pytest.mark.asyncio
    async def test_transaction_scope_commits_on_success(
        self, mock_session_manager
    ):
        """
        Test that TransactionScope commits transaction when no exception occurs.
        
        Scenario: Normal execution path
        Expected: begin() called on enter, commit() called on exit
        """
        # Act
        async with TransactionScope(mock_session_manager) as scope:
            # Simulate some work
            pass
        
        # Assert
        assert mock_session_manager.begin.called
        assert mock_session_manager.commit.called
        assert not mock_session_manager.rollback.called
        assert scope.committed
        assert not scope.rolled_back
    
    @pytest.mark.asyncio
    async def test_transaction_scope_rollback_on_exception(
        self, mock_session_manager
    ):
        """
        Test that TransactionScope rolls back transaction when exception occurs.
        
        Scenario: Exception raised within scope
        Expected: begin() called on enter, rollback() called on exit,
                 exception propagates
        """
        # Arrange
        class TestException(Exception):
            pass
        
        # Act & Assert
        with pytest.raises(TestException):
            async with TransactionScope(mock_session_manager) as scope:
                raise TestException("Test error")
        
        # Assert rollback happened
        assert mock_session_manager.begin.called
        assert not mock_session_manager.commit.called
        assert mock_session_manager.rollback.called
        assert not scope.committed
        assert scope.rolled_back
    
    @pytest.mark.asyncio
    async def test_transaction_scope_returns_self(
        self, mock_session_manager
    ):
        """
        Test that __aenter__ returns the TransactionScope instance.
        
        Scenario: Enter context manager
        Expected: Returns self for 'as' clause
        """
        # Act
        async with TransactionScope(mock_session_manager) as scope:
            # Assert
            assert isinstance(scope, TransactionScope)
    
    @pytest.mark.asyncio
    async def test_transaction_scope_begin_called_on_enter(
        self, mock_session_manager
    ):
        """
        Test that begin() is called when entering transaction scope.
        
        Scenario: Context manager entry
        Expected: Session manager's begin() method called
        """
        # Arrange
        scope = TransactionScope(mock_session_manager)
        
        # Act
        await scope.__aenter__()
        
        # Assert
        mock_session_manager.begin.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transaction_scope_commit_called_on_normal_exit(
        self, mock_session_manager
    ):
        """
        Test that commit() is called when exiting scope without exception.
        
        Scenario: Normal context manager exit (no exception)
        Expected: Session manager's commit() method called
        """
        # Arrange
        scope = TransactionScope(mock_session_manager)
        await scope.__aenter__()
        
        # Act
        await scope.__aexit__(None, None, None)
        
        # Assert
        mock_session_manager.commit.assert_called_once()
        assert not mock_session_manager.rollback.called
    
    @pytest.mark.asyncio
    async def test_transaction_scope_rollback_called_on_exception_exit(
        self, mock_session_manager
    ):
        """
        Test that rollback() is called when exiting scope with exception.
        
        Scenario: Context manager exit with exception
        Expected: Session manager's rollback() method called
        """
        # Arrange
        scope = TransactionScope(mock_session_manager)
        await scope.__aenter__()
        
        # Simulate exception
        exception = ValueError("Test error")
        
        # Act
        result = await scope.__aexit__(
            type(exception), exception, None
        )
        
        # Assert
        mock_session_manager.rollback.assert_called_once()
        assert not mock_session_manager.commit.called
        assert result is False  # Exception not suppressed
    
    @pytest.mark.asyncio
    async def test_transaction_scope_exception_propagates(
        self, mock_session_manager
    ):
        """
        Test that exceptions are not suppressed by TransactionScope.
        
        Scenario: Exception raised within scope
        Expected: Exception propagates to caller after rollback
        """
        # Arrange
        class CustomError(Exception):
            pass
        
        # Act & Assert
        with pytest.raises(CustomError, match="Custom error message"):
            async with TransactionScope(mock_session_manager):
                raise CustomError("Custom error message")
    
    @pytest.mark.asyncio
    async def test_transaction_scope_multiple_operations(
        self, mock_session_manager
    ):
        """
        Test TransactionScope with multiple operations in sequence.
        
        Scenario: Multiple service calls within same transaction scope
        Expected: All operations complete, single commit at end
        """
        # Arrange
        operations_completed = []
        
        # Act
        async with TransactionScope(mock_session_manager):
            operations_completed.append("operation_1")
            operations_completed.append("operation_2")
            operations_completed.append("operation_3")
        
        # Assert
        assert len(operations_completed) == 3
        assert mock_session_manager.begin.call_count == 1
        assert mock_session_manager.commit.call_count == 1
    
    @pytest.mark.asyncio
    async def test_transaction_scope_with_async_operations(
        self, mock_session_manager
    ):
        """
        Test TransactionScope with async operations.
        
        Scenario: Async service calls within transaction scope
        Expected: All async operations complete before commit
        """
        # Arrange
        async def async_operation(value):
            return value * 2
        
        results = []
        
        # Act
        async with TransactionScope(mock_session_manager):
            results.append(await async_operation(1))
            results.append(await async_operation(2))
            results.append(await async_operation(3))
        
        # Assert
        assert results == [2, 4, 6]
        assert mock_session_manager.commit.called
    
    @pytest.mark.asyncio
    async def test_transaction_scope_committed_property_false_before_commit(
        self, mock_session_manager
    ):
        """
        Test that committed property is False before commit.
        
        Scenario: Check property during scope execution
        Expected: committed=False until scope exits successfully
        """
        # Act
        async with TransactionScope(mock_session_manager) as scope:
            # Assert - inside scope, not yet committed
            assert not scope.committed
        
        # Assert - after scope, committed
        assert scope.committed
    
    @pytest.mark.asyncio
    async def test_transaction_scope_rolled_back_property_false_on_success(
        self, mock_session_manager
    ):
        """
        Test that rolled_back property is False on successful commit.
        
        Scenario: Successful execution path
        Expected: rolled_back=False throughout
        """
        # Act
        async with TransactionScope(mock_session_manager) as scope:
            assert not scope.rolled_back
        
        # Assert
        assert not scope.rolled_back
        assert scope.committed
    
    @pytest.mark.asyncio
    async def test_transaction_scope_state_properties_accurate(
        self, mock_session_manager
    ):
        """
        Test that committed and rolled_back properties accurately reflect state.
        
        Scenario: Check state after both success and failure
        Expected: Properties match actual execution path
        """
        # Success case
        async with TransactionScope(mock_session_manager) as scope1:
            pass
        assert scope1.committed
        assert not scope1.rolled_back
        
        # Failure case
        with pytest.raises(RuntimeError):
            async with TransactionScope(mock_session_manager) as scope2:
                raise RuntimeError("Test")
        
        assert not scope2.committed
        assert scope2.rolled_back


class TestTransactionScopeIntegration:
    """Integration-style tests for TransactionScope with real-ish scenarios."""
    
    @pytest.mark.asyncio
    async def test_transaction_scope_coordinates_multiple_services(self):
        """
        Test TransactionScope coordinating multiple services.
        
        Scenario: Cross-module operation (simulated)
        Expected: All services participate in same transaction
        """
        # Arrange
        mock_session_manager = AsyncMock(spec=ISessionManager)
        mock_session_manager.begin = AsyncMock()
        mock_session_manager.commit = AsyncMock()
        mock_session_manager.rollback = AsyncMock()
        
        # Simulate services
        service1_called = False
        service2_called = False
        
        async def service1_operation():
            nonlocal service1_called
            service1_called = True
            return "service1_result"
        
        async def service2_operation():
            nonlocal service2_called
            service2_called = True
            return "service2_result"
        
        # Act
        async with TransactionScope(mock_session_manager):
            result1 = await service1_operation()
            result2 = await service2_operation()
        
        # Assert
        assert service1_called
        assert service2_called
        assert mock_session_manager.begin.called
        assert mock_session_manager.commit.called
    
    @pytest.mark.asyncio
    async def test_transaction_scope_partial_rollback(self):
        """
        Test that TransactionScope rolls back even if first operation succeeded.
        
        Scenario: First operation succeeds, second fails
        Expected: Both rolled back (atomicity)
        """
        # Arrange
        mock_session_manager = AsyncMock(spec=ISessionManager)
        mock_session_manager.begin = AsyncMock()
        mock_session_manager.commit = AsyncMock()
        mock_session_manager.rollback = AsyncMock()
        
        operation1_completed = False
        operation2_attempted = False
        
        async def operation1():
            nonlocal operation1_completed
            operation1_completed = True
        
        async def operation2():
            nonlocal operation2_attempted
            operation2_attempted = True
            raise ValueError("Operation 2 failed")
        
        # Act & Assert
        with pytest.raises(ValueError):
            async with TransactionScope(mock_session_manager):
                await operation1()
                await operation2()
        
        # Assert
        assert operation1_completed  # First op ran
        assert operation2_attempted  # Second op attempted
        assert mock_session_manager.rollback.called  # But rolled back
        assert not mock_session_manager.commit.called
