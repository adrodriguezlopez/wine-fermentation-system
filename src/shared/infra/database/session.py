"""
Database Session Management

Provides async session management for repository infrastructure.
Integrates with IDatabaseConfig interface to provide session factory and context management.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from ..interfaces import IDatabaseConfig


class DatabaseSession:
    """
    Manages async database sessions for repository operations.
    
    Provides session factory creation and async context management
    following the ISessionManager interface contract.
    """
    
    def __init__(self, config: IDatabaseConfig):
        """
        Initialize DatabaseSession with a database configuration.
        
        Args:
            config: Database configuration implementing IDatabaseConfig interface
            
        Raises:
            TypeError: If config doesn't implement IDatabaseConfig interface
        """
        # Validate that config implements the interface
        if not hasattr(config, 'async_engine'):
            raise TypeError("DatabaseSession requires a config implementing IDatabaseConfig")
            
        self._config = config
        self.session_factory = async_sessionmaker(
            bind=config.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    def get_session(self):
        """
        Get an async database session as context manager.
        
        Returns:
            AsyncSession context manager for repository operations
            
        Example:
            async with session_manager.get_session() as session:
                # Use session for database operations
                result = await session.execute(query)
        """
        return self.session_factory()
    
    async def close(self) -> None:
        """
        Close the session manager and cleanup resources.
        
        This properly disposes of the underlying engine and
        cleans up any pending connections.
        """
        if hasattr(self._config, 'async_engine') and self._config.async_engine:
            await self._config.async_engine.dispose()