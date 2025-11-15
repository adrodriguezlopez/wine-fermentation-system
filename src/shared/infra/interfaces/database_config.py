"""
Database configuration interface.
"""

from typing import Protocol
from sqlalchemy.ext.asyncio import AsyncEngine


class IDatabaseConfig(Protocol):
    """
    Interface for database configuration management.
    
    This protocol defines the contract that any database configuration
    implementation must follow to be compatible with the repository infrastructure.
    """
    
    @property
    def async_engine(self) -> AsyncEngine:
        """
        Get the async SQLAlchemy engine.
        
        Returns:
            AsyncEngine: The configured async database engine
            
        Raises:
            DatabaseConfigError: If engine is not properly configured
        """
        ...