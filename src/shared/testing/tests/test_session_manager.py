"""
Tests for TestSessionManager.

Verifies the session manager wrapper behaves correctly as a
repository-compatible session manager.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from shared.testing.integration.session_manager import TestSessionManager


class TestTestSessionManager:
    """Test suite for TestSessionManager."""
    
    def test_initialization(self):
        """Test that TestSessionManager stores the session correctly."""
        mock_session = MagicMock()
        manager = TestSessionManager(mock_session)
        
        assert manager._session is mock_session
    
    @pytest.mark.asyncio
    async def test_get_session_yields_correct_session(self):
        """Test that get_session yields the wrapped session."""
        mock_session = MagicMock()
        manager = TestSessionManager(mock_session)
        
        async with manager.get_session() as session:
            assert session is mock_session
    
    @pytest.mark.asyncio
    async def test_get_session_context_manager(self):
        """Test that get_session works as a context manager."""
        mock_session = MagicMock()
        manager = TestSessionManager(mock_session)
        
        # Should not raise any exceptions
        async with manager.get_session() as session:
            assert session is not None
    
    @pytest.mark.asyncio
    async def test_close_is_noop(self):
        """Test that close does nothing (fixture manages lifecycle)."""
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        
        manager = TestSessionManager(mock_session)
        await manager.close()
        
        # Verify the underlying session's close was NOT called
        mock_session.close.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_multiple_get_session_calls(self):
        """Test that get_session can be called multiple times."""
        mock_session = MagicMock()
        manager = TestSessionManager(mock_session)
        
        # First call
        async with manager.get_session() as session1:
            assert session1 is mock_session
        
        # Second call should work the same
        async with manager.get_session() as session2:
            assert session2 is mock_session
        
        # Both should return the same session
        assert session1 is session2
    
    @pytest.mark.asyncio
    async def test_session_operations_pass_through(self):
        """Test that operations on the session are passed through correctly."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value="result")
        
        manager = TestSessionManager(mock_session)
        
        async with manager.get_session() as session:
            result = await session.execute("SELECT 1")
        
        assert result == "result"
        mock_session.execute.assert_called_once_with("SELECT 1")
