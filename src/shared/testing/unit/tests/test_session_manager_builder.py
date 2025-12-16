"""
Tests for MockSessionManagerBuilder

Validates the behavior and API of the mock session manager builder.
Follows TDD principles from ADR-012.
"""

import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncResult

from src.shared.testing.unit.mocks.session_manager_builder import (
    create_mock_session_manager,
    MockSessionManagerBuilder,
)


class TestMockSessionManagerBuilder:
    """Test suite for MockSessionManagerBuilder"""
    
    @pytest.mark.asyncio
    async def test_create_simple_mock(self):
        """Should create a basic mock session manager"""
        # Act
        mock_sm = create_mock_session_manager()
        
        # Assert
        assert mock_sm is not None
        assert hasattr(mock_sm, "get_session")
        assert hasattr(mock_sm, "close")
        
        # Should be able to use get_session as async context manager
        async with mock_sm.get_session() as session:
            assert session is not None
            assert hasattr(session, "execute")
            assert hasattr(session, "commit")
            assert hasattr(session, "rollback")
    
    @pytest.mark.asyncio
    async def test_session_has_all_required_methods(self):
        """Should provide session with all SQLAlchemy async methods"""
        # Arrange
        mock_sm = create_mock_session_manager()
        
        # Act
        async with mock_sm.get_session() as session:
            # Assert - all methods should exist
            assert hasattr(session, "execute")
            assert hasattr(session, "commit")
            assert hasattr(session, "rollback")
            assert hasattr(session, "close")
            assert hasattr(session, "refresh")
            assert hasattr(session, "flush")
            assert hasattr(session, "scalar")
            assert hasattr(session, "scalars")
    
    @pytest.mark.asyncio
    async def test_with_execute_result(self):
        """Should return configured result from execute()"""
        # Arrange
        mock_result = AsyncMock(spec=AsyncResult)
        mock_sm = create_mock_session_manager(execute_result=mock_result)
        
        # Act
        async with mock_sm.get_session() as session:
            result = await session.execute("SELECT * FROM test")
        
        # Assert
        assert result == mock_result
    
    @pytest.mark.asyncio
    async def test_with_execute_side_effect_exception(self):
        """Should raise configured exception from execute()"""
        # Arrange
        test_exception = Exception("Database error")
        mock_sm = create_mock_session_manager(execute_side_effect=test_exception)
        
        # Act & Assert
        async with mock_sm.get_session() as session:
            with pytest.raises(Exception, match="Database error"):
                await session.execute("SELECT * FROM test")
    
    @pytest.mark.asyncio
    async def test_with_commit_side_effect_exception(self):
        """Should raise configured exception from commit()"""
        # Arrange
        test_exception = Exception("Commit failed")
        mock_sm = create_mock_session_manager(commit_side_effect=test_exception)
        
        # Act & Assert
        async with mock_sm.get_session() as session:
            with pytest.raises(Exception, match="Commit failed"):
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_builder_pattern_chaining(self):
        """Should support fluent builder pattern"""
        # Arrange
        mock_result = AsyncMock(spec=AsyncResult)
        commit_error = Exception("Commit failed")
        
        # Act
        mock_sm = (
            MockSessionManagerBuilder()
            .with_execute_result(mock_result)
            .with_commit_side_effect(commit_error)
            .build()
        )
        
        # Assert
        async with mock_sm.get_session() as session:
            result = await session.execute("SELECT * FROM test")
            assert result == mock_result
            
            with pytest.raises(Exception, match="Commit failed"):
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_builder_with_rollback_side_effect(self):
        """Should configure rollback side effect"""
        # Arrange
        rollback_error = Exception("Rollback failed")
        mock_sm = (
            MockSessionManagerBuilder()
            .with_rollback_side_effect(rollback_error)
            .build()
        )
        
        # Act & Assert
        async with mock_sm.get_session() as session:
            with pytest.raises(Exception, match="Rollback failed"):
                await session.rollback()
    
    @pytest.mark.asyncio
    async def test_builder_with_close_side_effect(self):
        """Should configure close side effect on session manager"""
        # Arrange
        close_error = Exception("Close failed")
        mock_sm = (
            MockSessionManagerBuilder()
            .with_close_side_effect(close_error)
            .build()
        )
        
        # Act & Assert
        with pytest.raises(Exception, match="Close failed"):
            await mock_sm.close()
    
    @pytest.mark.asyncio
    async def test_builder_with_custom_session(self):
        """Should allow using a custom session mock"""
        # Arrange
        custom_session = AsyncMock()
        custom_session.custom_method = AsyncMock(return_value="custom_result")
        
        mock_sm = (
            MockSessionManagerBuilder()
            .with_session(custom_session)
            .build()
        )
        
        # Act
        async with mock_sm.get_session() as session:
            result = await session.custom_method()
        
        # Assert
        assert result == "custom_result"
    
    @pytest.mark.asyncio
    async def test_execute_side_effect_callable(self):
        """Should support callable side effects for execute()"""
        # Arrange
        call_count = []
        
        def side_effect(*args, **kwargs):
            call_count.append(1)
            return AsyncMock()
        
        mock_sm = (
            MockSessionManagerBuilder()
            .with_execute_side_effect(side_effect)
            .build()
        )
        
        # Act
        async with mock_sm.get_session() as session:
            await session.execute("SELECT 1")
            await session.execute("SELECT 2")
        
        # Assert
        assert len(call_count) == 2
    
    @pytest.mark.asyncio
    async def test_multiple_session_contexts(self):
        """Should support multiple get_session calls"""
        # Arrange
        mock_result = AsyncMock(spec=AsyncResult)
        mock_sm = create_mock_session_manager(execute_result=mock_result)
        
        # Act & Assert - First context
        async with mock_sm.get_session() as session1:
            result1 = await session1.execute("SELECT 1")
            assert result1 == mock_result
        
        # Act & Assert - Second context
        async with mock_sm.get_session() as session2:
            result2 = await session2.execute("SELECT 2")
            assert result2 == mock_result
    
    @pytest.mark.asyncio
    async def test_session_manager_close(self):
        """Should support closing the session manager"""
        # Arrange
        mock_sm = create_mock_session_manager()
        
        # Act
        await mock_sm.close()
        
        # Assert
        mock_sm.close.assert_called_once()


class TestFactoryFunctionConvenience:
    """Test convenience factory function vs builder pattern"""
    
    @pytest.mark.asyncio
    async def test_factory_is_simpler_for_basic_cases(self):
        """Factory function should be more concise than builder for simple cases"""
        # Simple mock with factory
        mock_sm = create_mock_session_manager()
        
        # Should work the same as builder
        async with mock_sm.get_session() as session:
            assert session is not None
    
    @pytest.mark.asyncio
    async def test_builder_required_for_complex_cases(self):
        """Builder should be used for complex multi-configuration scenarios"""
        # Complex scenario requiring builder
        mock_sm = (
            MockSessionManagerBuilder()
            .with_execute_result(AsyncMock())
            .with_commit_side_effect(Exception("Commit failed"))
            .with_rollback_side_effect(Exception("Rollback failed"))
            .with_close_side_effect(Exception("Close failed"))
            .build()
        )
        
        # Should have all configurations applied
        async with mock_sm.get_session() as session:
            with pytest.raises(Exception, match="Commit failed"):
                await session.commit()
            
            with pytest.raises(Exception, match="Rollback failed"):
                await session.rollback()
        
        with pytest.raises(Exception, match="Close failed"):
            await mock_sm.close()
