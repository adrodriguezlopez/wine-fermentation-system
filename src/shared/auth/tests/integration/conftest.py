"""
Integration tests configuration and fixtures.

Provides database setup, session management, and common fixtures
for integration testing with real database operations.

Uses environment variable to signal test mode and avoid FK constraint issues.
"""

import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool

# Set test mode BEFORE importing User entity
# This will be cleaned up in the session fixture below
os.environ['AUTH_TEST_MODE'] = '1'

from src.shared.infra.orm.base_entity import Base
from src.shared.auth.domain.entities.user import User
from src.shared.auth.infra.repositories import UserRepository
from src.shared.auth.infra.services import (
    PasswordService,
    JwtService,
    AuthService,
)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_mode():
    """Clean up AUTH_TEST_MODE after all auth tests complete."""
    yield
    os.environ.pop('AUTH_TEST_MODE', None)


@pytest.fixture(scope="session")
def database_url() -> str:
    """
    Provide in-memory SQLite database URL for testing.
    
    Using in-memory database ensures:
    - Fast test execution
    - Isolated test environment
    - No persistence between test runs
    """
    return "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def async_engine(database_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """
    Create async SQLAlchemy engine for testing.
    
    Configured with:
    - StaticPool: Maintains single connection for in-memory DB
    - echo=False: Disable SQL logging for cleaner test output
    
    Uses AUTH_TEST_MODE environment variable to avoid FK constraints.
    """
    engine = create_async_engine(
        database_url,
        echo=False,
        poolclass=StaticPool,  # Required for SQLite in-memory with async
        connect_args={"check_same_thread": False},  # Allow multi-threading
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create async database session for testing.
    
    Each test gets a fresh session that is automatically cleaned up.
    Transactions are rolled back to ensure test isolation.
    """
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def user_repository(async_session: AsyncSession) -> UserRepository:
    """Provide UserRepository instance with test database session."""
    return UserRepository(async_session)


@pytest.fixture
def password_service() -> PasswordService:
    """Provide PasswordService instance for testing."""
    return PasswordService()


@pytest.fixture
def jwt_service() -> JwtService:
    """
    Provide JwtService instance with test configuration.
    
    Uses test-specific secret key for token generation.
    """
    return JwtService(secret_key="test-secret-key-for-integration-tests")


@pytest_asyncio.fixture
async def auth_service(
    user_repository: UserRepository,
    password_service: PasswordService,
    jwt_service: JwtService,
) -> AuthService:
    """
    Provide fully configured AuthService for integration testing.
    
    This fixture wires together all dependencies with real implementations
    connected to the test database.
    """
    return AuthService(
        user_repository=user_repository,
        password_service=password_service,
        jwt_service=jwt_service,
    )


@pytest_asyncio.fixture
async def sample_winery_id() -> int:
    """Provide a sample winery ID for multi-tenancy testing."""
    return 1


@pytest_asyncio.fixture
async def another_winery_id() -> int:
    """Provide another winery ID for multi-tenancy isolation testing."""
    return 2
