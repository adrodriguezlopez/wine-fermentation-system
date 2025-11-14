"""
FastAPI Database Session Management

Provides async session lifecycle management for FastAPI applications.
Implements dependency injection pattern for database sessions.
"""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.shared.infra.database.config import DatabaseConfig


# Global database configuration
_db_config: Optional[DatabaseConfig] = None
_async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


def initialize_database(config: Optional[DatabaseConfig] = None) -> None:
    """
    Initialize database configuration and session maker.
    
    Should be called once during application startup.
    
    Args:
        config: Optional DatabaseConfig instance. If None, creates default config.
    
    Example:
        ```python
        # In main.py or app startup
        from src.shared.infra.database.fastapi_session import initialize_database
        
        initialize_database()  # Uses default config from environment
        ```
    """
    global _db_config, _async_session_maker
    
    if config is None:
        config = DatabaseConfig()
    
    _db_config = config
    _async_session_maker = async_sessionmaker(
        bind=config.async_engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Keep objects accessible after commit
        autoflush=False,  # Explicit control over flushes
    )


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: Provides async database session with proper lifecycle.
    
    Yields:
        AsyncSession: Database session for the request
    
    Lifecycle:
        1. Creates session from session maker
        2. Yields session to endpoint
        3. Commits transaction on success
        4. Rolls back on exception
        5. Closes session
    
    Usage:
        ```python
        @router.get("/items")
        async def get_items(
            session: Annotated[AsyncSession, Depends(get_db_session)]
        ):
            result = await session.execute(select(Item))
            return result.scalars().all()
        ```
    
    Raises:
        RuntimeError: If database not initialized (call initialize_database first)
    """
    if _async_session_maker is None:
        raise RuntimeError(
            "Database not initialized. Call initialize_database() during app startup."
        )
    
    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_database() -> None:
    """
    Cleanup database resources.
    
    Should be called during application shutdown.
    
    Example:
        ```python
        # In main.py
        @app.on_event("shutdown")
        async def shutdown():
            await close_database()
        ```
    """
    global _db_config
    
    if _db_config and _db_config._engine:
        await _db_config._engine.dispose()
