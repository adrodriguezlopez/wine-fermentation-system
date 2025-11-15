"""
FastAPI SessionManager Wrapper

Wraps FastAPI's AsyncSession to implement ISessionManager protocol
for compatibility with BaseRepository.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from src.shared.infra.interfaces.session_manager import ISessionManager


class FastAPISessionManager(ISessionManager):
    """
    SessionManager implementation for FastAPI dependency injection.
    
    Wraps an AsyncSession provided by get_db_session() dependency
    to implement ISessionManager protocol for BaseRepository compatibility.
    
    Lifecycle:
        - FastAPI manages session creation/disposal via get_db_session()
        - This wrapper just provides ISessionManager interface
        - No need to commit/rollback here (handled by get_db_session)
    
    Example:
        ```python
        async def get_fermentation_repository(
            session: Annotated[AsyncSession, Depends(get_db_session)]
        ) -> IFermentationRepository:
            session_manager = FastAPISessionManager(session)
            return FermentationRepository(session_manager)
        ```
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize with FastAPI-managed AsyncSession.
        
        Args:
            session: AsyncSession from get_db_session() dependency
        """
        self._session = session
    
    @asynccontextmanager
    async def get_session(self):
        """
        Yield the wrapped session.
        
        No context management needed - FastAPI handles lifecycle.
        
        Yields:
            AsyncSession: The session provided by FastAPI
        """
        yield self._session
    
    async def close(self) -> None:
        """
        Close session (no-op for FastAPI).
        
        FastAPI's get_db_session() dependency handles session cleanup,
        so this is a no-op to satisfy ISessionManager protocol.
        """
        # FastAPI manages session lifecycle, nothing to do here
        pass
