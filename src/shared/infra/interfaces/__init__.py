"""
Interfaces package for shared infrastructure components.
"""

from .database_config import IDatabaseConfig
from .session_manager import ISessionManager

__all__ = [
    "IDatabaseConfig",
    "ISessionManager",
]