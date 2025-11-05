"""Shared fixtures for auth unit tests."""

from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

import pytest

from src.shared.auth.domain.enums import UserRole


# Note: We use Mock objects for User fixtures in unit tests because the real User entity
# has relationships to Fermentation/BaseSample entities that can't be resolved without
# the fermentation module. For repository and integration tests, we'll use real User entities.


@pytest.fixture
def sample_user():
    """Create a sample User mock for testing."""
    user = Mock()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.password_hash = "$2b$12$hashedpassword"
    user.full_name = "Test User"
    user.winery_id = 1
    user.role = UserRole.WINEMAKER.value
    user.is_active = True
    user.is_verified = True
    user.last_login_at = None
    user.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.updated_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.deleted_at = None
    return user


@pytest.fixture
def sample_user_data():
    """Create sample User entity data for creation tests."""
    user = Mock()
    user.username = "newuser"
    user.email = "newuser@example.com"
    user.password_hash = "$2b$12$hashedpassword"
    user.full_name = "New User"
    user.winery_id = 1
    user.role = UserRole.VIEWER.value
    user.is_active = True
    user.is_verified = False
    user.last_login_at = None
    user.id = None
    user.created_at = None
    user.updated_at = None
    user.deleted_at = None
    return user


@pytest.fixture
def admin_user():
    """Create an admin User mock for testing."""
    user = Mock()
    user.id = 2
    user.username = "admin"
    user.email = "admin@example.com"
    user.password_hash = "$2b$12$hashedpassword"
    user.full_name = "Admin User"
    user.winery_id = 1
    user.role = UserRole.ADMIN.value
    user.is_active = True
    user.is_verified = True
    user.last_login_at = None
    user.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.updated_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.deleted_at = None
    return user


@pytest.fixture
def operator_user():
    """Create an operator User mock for testing."""
    user = Mock()
    user.id = 3
    user.username = "operator"
    user.email = "operator@example.com"
    user.password_hash = "$2b$12$hashedpassword"
    user.full_name = "Operator User"
    user.winery_id = 1
    user.role = UserRole.OPERATOR.value
    user.is_active = True
    user.is_verified = True
    user.last_login_at = None
    user.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.updated_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.deleted_at = None
    return user


@pytest.fixture
def viewer_user():
    """Create a viewer User mock for testing."""
    user = Mock()
    user.id = 4
    user.username = "viewer"
    user.email = "viewer@example.com"
    user.password_hash = "$2b$12$hashedpassword"
    user.full_name = "Viewer User"
    user.winery_id = 1
    user.role = UserRole.VIEWER.value
    user.is_active = True
    user.is_verified = True
    user.last_login_at = None
    user.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.updated_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    user.deleted_at = None
    return user


@pytest.fixture
def mock_db_session():
    """Create a mock database session for repository tests."""
    session = Mock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
    return session


@pytest.fixture
def user_repository(mock_db_session):
    """Create UserRepository instance with mocked session."""
    from src.shared.auth.infra.repositories.user_repository import UserRepository
    return UserRepository(mock_db_session)
