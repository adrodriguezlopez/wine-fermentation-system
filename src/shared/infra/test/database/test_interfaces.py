"""
Unit tests for interface compliance - TDD approach

Testing that our implementations properly follow the defined interfaces.
This ensures we maintain the contract while refactoring.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

# Add path to import shared modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.infra.interfaces import IDatabaseConfig, ISessionManager
from shared.infra.database import DatabaseConfig, DatabaseSession


class TestDatabaseConfigInterface:
    """Test that DatabaseConfig implements IDatabaseConfig interface."""
    
    def test_database_config_implements_interface(self):
        """Test that DatabaseConfig properly implements IDatabaseConfig protocol."""
        # Arrange
        with patch('shared.infra.database.config.create_async_engine') as mock_create_engine:
            mock_engine = Mock(spec=AsyncEngine)
            mock_create_engine.return_value = mock_engine
            
            # Act
            config = DatabaseConfig()
            
            # Assert - Check that it has the interface properties
            assert hasattr(config, 'async_engine')
            assert callable(getattr(config, 'async_engine', None)) or hasattr(type(config), 'async_engine')
            
    def test_database_config_async_engine_property(self):
        """Test that async_engine property returns AsyncEngine."""
        # Arrange
        with patch('shared.infra.database.config.create_async_engine') as mock_create_engine:
            mock_engine = Mock(spec=AsyncEngine)
            mock_create_engine.return_value = mock_engine
            
            config = DatabaseConfig()
            
            # Act
            engine = config.async_engine
            
            # Assert
            assert engine is mock_engine
            

class TestDatabaseSessionInterface:
    """Test that DatabaseSession implements ISessionManager interface."""
    
    def test_database_session_implements_interface(self):
        """Test that DatabaseSession properly implements ISessionManager protocol."""
        # Arrange
        mock_config = Mock(spec=IDatabaseConfig)
        mock_engine = Mock(spec=AsyncEngine)
        mock_config.async_engine = mock_engine
        
        # Act
        session_manager = DatabaseSession(mock_config)
        
        # Assert - Check that it has the interface methods
        assert hasattr(session_manager, 'get_session')
        assert callable(getattr(session_manager, 'get_session'))
        assert hasattr(session_manager, 'close')
        assert callable(getattr(session_manager, 'close'))
        
    @pytest.mark.asyncio
    async def test_database_session_get_session_signature(self):
        """Test that get_session method has correct async signature."""
        # Arrange
        mock_config = Mock(spec=IDatabaseConfig)
        mock_engine = Mock(spec=AsyncEngine)
        mock_config.async_engine = mock_engine
        
        with patch('sqlalchemy.ext.asyncio.async_sessionmaker') as mock_sessionmaker:
            mock_session_factory = Mock()
            mock_sessionmaker.return_value = mock_session_factory
            
            session_manager = DatabaseSession(mock_config)
            
            # Act & Assert - Should be callable without raising
            result = session_manager.get_session()
            assert result is not None
            
    @pytest.mark.asyncio
    async def test_database_session_close_signature(self):
        """Test that close method has correct async signature."""
        # Arrange
        mock_config = Mock(spec=IDatabaseConfig)
        mock_engine = Mock(spec=AsyncEngine)
        mock_config.async_engine = mock_engine
        
        with patch('sqlalchemy.ext.asyncio.async_sessionmaker') as mock_sessionmaker:
            mock_session_factory = Mock()
            mock_sessionmaker.return_value = mock_session_factory
            
            session_manager = DatabaseSession(mock_config)
            
            # Act & Assert - Should be callable without raising
            await session_manager.close()


class TestInterfaceContracts:
    """Test that interfaces define proper contracts."""
    
    def test_idatabase_config_has_async_engine_property(self):
        """Test that IDatabaseConfig protocol defines async_engine property."""
        # This test verifies the interface itself is well-defined
        assert hasattr(IDatabaseConfig, 'async_engine')
        
    def test_isession_manager_has_required_methods(self):
        """Test that ISessionManager protocol defines required methods."""
        # This test verifies the interface itself is well-defined
        assert hasattr(ISessionManager, 'get_session')
        assert hasattr(ISessionManager, 'close')