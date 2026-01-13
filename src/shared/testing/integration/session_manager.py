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
    
    async def begin(self):
        """
        Begin transaction - no-op for test session.
        
        Test fixture already manages transaction lifecycle with:
            async with session.begin():
                yield session
                
        This method exists for ISessionManager protocol compliance (ADR-031).
        We don't create nested transactions because they can interfere with
        the test fixture's cleanup logic.
        """
        pass
    
    async def commit(self):
        """
        Commit transaction - no-op for test session.
        
        The test fixture manages commits/rollbacks. Committing here would
        interfere with test isolation (fixture always rolls back at end).
        
        For testing purposes, data written during the test is visible
        within the same transaction, so no actual commit is needed.
        """
        pass
    
    async def rollback(self):
        """
        Rollback transaction - no-op for test session.
        
        The test fixture handles final rollback after test completes.
        Individual rollbacks within a test are simulated by the fixture's
        transaction isolation.
        """
        pass
