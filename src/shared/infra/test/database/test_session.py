"""
Unit tests for DatabaseSession - TDD approach

Testing session management and async context handling for repository infrastructure.
Following TDD religioso - tests first, implementation after approval.
Now refactored to use interface-based architecture.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

# Add path to import shared modules (same pattern as other working tests)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.infra.database import DatabaseConfig, DatabaseSession
from shared.infra.interfaces import IDatabaseConfig


class TestDatabaseSessionCreation:
    """Test basic DatabaseSession creation and initialization."""
    
    def test_database_session_requires_config(self):
        """Test that DatabaseSession requires an IDatabaseConfig for initialization."""
        mock_config = Mock(spec=IDatabaseConfig)
        mock_engine = Mock(spec=AsyncEngine)
        mock_config.async_engine = mock_engine
        
        session = DatabaseSession(mock_config)
        
        assert session._config is mock_config
        assert hasattr(session, 'session_factory')

    def test_database_session_creates_session_factory(self):
        """Test that DatabaseSession creates a sessionmaker factory."""
        mock_config = Mock(spec=IDatabaseConfig)
        mock_engine = Mock(spec=AsyncEngine)
        mock_config.async_engine = mock_engine
        
        session = DatabaseSession(mock_config)
        
        # Should create an async sessionmaker
        assert session.session_factory is not None
        assert callable(session.session_factory)

    def test_database_session_integration_with_config(self):
        """Test that DatabaseSession integrates with existing DatabaseConfig."""
        # Use real DatabaseConfig
        config = DatabaseConfig()
        
        session = DatabaseSession(config)
        assert session._config is config


class TestAsyncSessionManagement:
    """Test async session context management."""
    
    @pytest.mark.asyncio
    async def test_get_session_returns_async_session(self):
        """Test that get_session returns an AsyncSession."""
        mock_config = Mock(spec=IDatabaseConfig)
        mock_engine = Mock(spec=AsyncEngine)
        mock_config.async_engine = mock_engine
        
        db_session = DatabaseSession(mock_config)
        
        async with db_session.get_session() as session:
            assert isinstance(session, AsyncSession)

    @pytest.mark.asyncio 
    async def test_get_session_context_manager(self):
        """Test that get_session works as async context manager."""
        mock_config = Mock(spec=IDatabaseConfig)
        mock_engine = Mock(spec=AsyncEngine)
        mock_config.async_engine = mock_engine
        
        # Create a proper mock that acts like async_sessionmaker result
        mock_session_instance = AsyncMock(spec=AsyncSession)
        mock_session_factory = Mock()
        mock_session_factory.return_value = mock_session_instance
        
        with patch('shared.infra.database.session.async_sessionmaker', return_value=mock_session_factory):
            db_session = DatabaseSession(mock_config)
            
            # Test that async context manager works (not checking exact instance)
            async with db_session.get_session() as session:
                assert session is not None
                assert hasattr(session, 'execute')  # Should be session-like object

    @pytest.mark.asyncio
    async def test_session_cleanup_on_context_exit(self):
        """Test that session is properly cleaned up when context exits."""
        mock_config = Mock(spec=IDatabaseConfig)
        mock_engine = Mock(spec=AsyncEngine)
        mock_config.async_engine = mock_engine
        
        # Create mocks that properly simulate SQLAlchemy behavior
        mock_session_instance = AsyncMock(spec=AsyncSession)
        mock_session_factory = Mock()
        mock_session_factory.return_value = mock_session_instance
        
        with patch('shared.infra.database.session.async_sessionmaker', return_value=mock_session_factory):
            db_session = DatabaseSession(mock_config)
            
            async with db_session.get_session() as session:
                pass  # Session used in context
            
            # Verify that __aexit__ was called on the session (cleanup)
            mock_session_instance.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_manager_close(self):
        """Test that close method properly disposes of the engine."""
        mock_config = Mock(spec=IDatabaseConfig)
        mock_engine = AsyncMock(spec=AsyncEngine)
        mock_config.async_engine = mock_engine
        
        db_session = DatabaseSession(mock_config)
        
        # Call close method
        await db_session.close()
        
        # Verify that engine dispose was called
        mock_engine.dispose.assert_called_once()


class TestDatabaseSessionErrorHandling:
    """Test error handling in session management."""
    
    @pytest.mark.asyncio
    async def test_session_error_propagation(self):
        """Test that session errors are properly propagated."""
        mock_config = Mock(spec=IDatabaseConfig)
        mock_engine = Mock(spec=AsyncEngine)
        mock_config.async_engine = mock_engine
        
        # Mock the sessionmaker to raise an exception when called
        with patch('shared.infra.database.session.async_sessionmaker') as mock_sessionmaker:
            mock_sessionmaker.side_effect = Exception("Database connection failed")
            
            # Exception should be raised during DatabaseSession creation, not during get_session()
            with pytest.raises(Exception, match="Database connection failed"):
                DatabaseSession(mock_config)

    def test_database_session_invalid_config(self):
        """Test that DatabaseSession validates config type."""
        # Should raise error for invalid config
        with pytest.raises(TypeError, match="DatabaseSession requires a config implementing IDatabaseConfig"):
            DatabaseSession("not_a_config")


class TestDatabaseSessionIntegration:
    """Integration tests with real database config."""
    
    def test_database_session_with_real_config(self):
        """Test DatabaseSession with real DatabaseConfig (no actual DB connection)."""
        # Use actual config but don't connect
        config = DatabaseConfig()
        
        # Should not raise errors during initialization
        session = DatabaseSession(config)
        assert session._config is config
        assert session.session_factory is not None

    @pytest.mark.asyncio
    async def test_session_factory_configuration(self):
        """Test that session factory is properly configured."""
        mock_config = Mock(spec=IDatabaseConfig)
        mock_engine = Mock(spec=AsyncEngine)
        mock_config.async_engine = mock_engine
        
        db_session = DatabaseSession(mock_config)
        
        # Verify sessionmaker was configured with correct parameters
        with patch('shared.infra.database.session.async_sessionmaker') as mock_sessionmaker:
            db_session = DatabaseSession(mock_config)
            
            # Verify sessionmaker was called with engine and async=True
            mock_sessionmaker.assert_called_once_with(
                bind=mock_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )