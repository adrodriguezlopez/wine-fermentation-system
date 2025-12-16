"""
MockSessionManager Builder

Provides a fluent API for creating mock SessionManager objects with configurable behavior.

Usage:
    # Simple mock
    mock_session_manager = create_mock_session_manager()
    
    # With custom session behavior
    mock_session_manager = (
        create_mock_session_manager()
        .with_execute_result(mock_result)
        .with_commit_side_effect(Exception("Commit failed"))
        .build()
    )
"""

from typing import Any, Optional, Callable, Union
from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager

from src.shared.infra.interfaces.session_manager import ISessionManager


class MockSessionManagerBuilder:
    """
    Builder for creating mock SessionManager instances with configurable behavior.
    
    Provides a fluent interface for setting up mock sessions, execute results,
    and side effects for testing repository and service layers.
    """
    
    def __init__(self):
        """Initialize the builder with default mock objects."""
        self._session = AsyncMock()
        self._execute_result = None
        self._execute_side_effect = None
        self._commit_side_effect = None
        self._rollback_side_effect = None
        self._flush_side_effect = None
        self._close_side_effect = None
        self._session_context_manager = None
        
        # Configure default session behavior
        self._session.execute = AsyncMock()
        self._session.commit = AsyncMock()
        self._session.rollback = AsyncMock()
        self._session.close = AsyncMock()
        self._session.refresh = AsyncMock()
        self._session.flush = AsyncMock()
        self._session.scalar = AsyncMock()
        self._session.scalars = AsyncMock()
    
    def with_execute_result(self, result: Any) -> "MockSessionManagerBuilder":
        """
        Configure the result returned by session.execute().
        
        Args:
            result: The result to return when execute() is called
            
        Returns:
            Self for method chaining
        """
        self._execute_result = result
        return self
    
    def with_execute_side_effect(
        self, side_effect: Union[Callable, Exception]
    ) -> "MockSessionManagerBuilder":
        """
        Configure a side effect for session.execute().
        
        Args:
            side_effect: Exception to raise or callable to invoke
            
        Returns:
            Self for method chaining
        """
        self._execute_side_effect = side_effect
        return self
    
    def with_commit_side_effect(
        self, side_effect: Union[Callable, Exception]
    ) -> "MockSessionManagerBuilder":
        """
        Configure a side effect for session.commit().
        
        Args:
            side_effect: Exception to raise or callable to invoke
            
        Returns:
            Self for method chaining
        """
        self._commit_side_effect = side_effect
        return self
    
    def with_rollback_side_effect(
        self, side_effect: Union[Callable, Exception]
    ) -> "MockSessionManagerBuilder":
        """
        Configure a side effect for session.rollback().
        
        Args:
            side_effect: Exception to raise or callable to invoke
            
        Returns:
            Self for method chaining
        """
        self._rollback_side_effect = side_effect
        return self
    
    def with_flush_side_effect(
        self, side_effect: Union[Callable, Exception]
    ) -> "MockSessionManagerBuilder":
        """
        Configure a side effect for session.flush().
        
        Args:
            side_effect: Exception to raise or callable to invoke
            
        Returns:
            Self for method chaining
        """
        self._flush_side_effect = side_effect
        return self
    
    def with_close_side_effect(
        self, side_effect: Union[Callable, Exception]
    ) -> "MockSessionManagerBuilder":
        """
        Configure a side effect for session_manager.close().
        
        Args:
            side_effect: Exception to raise or callable to invoke
            
        Returns:
            Self for method chaining
        """
        self._close_side_effect = side_effect
        return self
    
    def with_session(self, session: AsyncMock) -> "MockSessionManagerBuilder":
        """
        Use a custom mock session instead of the default.
        
        Args:
            session: Custom AsyncMock session object
            
        Returns:
            Self for method chaining
        """
        self._session = session
        return self
    
    def build(self) -> ISessionManager:
        """
        Build and return the configured mock SessionManager.
        
        Returns:
            Mock SessionManager instance conforming to ISessionManager protocol
        """
        # Apply side effects and results
        if self._execute_result is not None:
            self._session.execute.return_value = self._execute_result
        
        if self._execute_side_effect is not None:
            self._session.execute.side_effect = self._execute_side_effect
        
        if self._commit_side_effect is not None:
            self._session.commit.side_effect = self._commit_side_effect
        
        if self._rollback_side_effect is not None:
            self._session.rollback.side_effect = self._rollback_side_effect
        
        if self._flush_side_effect is not None:
            self._session.flush.side_effect = self._flush_side_effect
        
        # Create the session manager mock
        session_manager = AsyncMock(spec=ISessionManager)
        
        # Configure get_session to return async context manager
        @asynccontextmanager
        async def mock_get_session():
            yield self._session
        
        session_manager.get_session = mock_get_session
        
        # Configure close with optional side effect
        if self._close_side_effect is not None:
            session_manager.close.side_effect = self._close_side_effect
        else:
            session_manager.close = AsyncMock()
        
        return session_manager


def create_mock_session_manager(
    execute_result: Optional[Any] = None,
    execute_side_effect: Optional[Union[Callable, Exception]] = None,
    commit_side_effect: Optional[Union[Callable, Exception]] = None,
) -> ISessionManager:
    """
    Factory function for creating a mock SessionManager with common defaults.
    
    Provides a convenient one-line way to create simple mocks while still
    supporting the builder pattern for complex scenarios.
    
    Args:
        execute_result: Optional result to return from session.execute()
        execute_side_effect: Optional side effect for session.execute()
        commit_side_effect: Optional side effect for session.commit()
        
    Returns:
        Mock SessionManager instance
        
    Examples:
        # Simple mock
        mock_sm = create_mock_session_manager()
        
        # With execute result
        mock_sm = create_mock_session_manager(execute_result=mock_result)
        
        # With commit failure
        mock_sm = create_mock_session_manager(
            commit_side_effect=Exception("Commit failed")
        )
        
        # For complex scenarios, use the builder
        mock_sm = (
            MockSessionManagerBuilder()
            .with_execute_result(mock_result)
            .with_commit_side_effect(Exception("Failed"))
            .with_rollback_side_effect(Exception("Rollback failed"))
            .build()
        )
    """
    builder = MockSessionManagerBuilder()
    
    if execute_result is not None:
        builder.with_execute_result(execute_result)
    
    if execute_side_effect is not None:
        builder.with_execute_side_effect(execute_side_effect)
    
    if commit_side_effect is not None:
        builder.with_commit_side_effect(commit_side_effect)
    
    return builder.build()
