"""
TestSessionManager - Repository-compatible session wrapper for integration tests.

Eliminates 80+ lines of duplication across module conftest.py files.
"""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession


class TestSessionManager:
    """
    Test double for ISessionManager that wraps an existing test session.
    
    Allows repository integration tests to use real database sessions
    without transaction management overhead.
    
    Usage:
        async with db_session.begin():
            session_manager = TestSessionManager(db_session)
            repository = MyRepository(session_manager)
            
            result = await repository.create(data)
            # No need to commit - handled by test transaction
    
    This class eliminates the need to duplicate session manager code
    in every module's conftest.py file.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize with test session.
        
        Args:
            session: Active AsyncSession from test fixture
        """
        self._session = session
    
    @asynccontextmanager
    async def get_session(self):
        """
        Yield the test session.
        
        Does not create new session or manage transactions -
        test fixture handles transaction lifecycle.
        
        Yields:
            AsyncSession: The wrapped test session
        """
        yield self._session
    
    async def close(self):
        """
        No-op close method for compatibility.
        
        Test fixture manages session lifecycle, so this method
        does nothing to avoid interfering with test cleanup.
        """
        pass
