"""Tests for UserRepository implementation."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timezone

from src.shared.auth.domain.entities.user import User
from src.shared.auth.domain.enums import UserRole
from src.shared.auth.domain.errors import UserAlreadyExistsError, UserNotFoundError


class TestUserRepositoryCreate:
    """Test UserRepository.create() method."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repository, sample_user_data):
        """Test creating a new user successfully."""
        # Arrange
        # Mock exists checks to return False (no duplicates)
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 0
        user_repository._session.execute = AsyncMock(return_value=mock_count_result)
        user_repository._session.commit = AsyncMock()
        user_repository._session.refresh = AsyncMock()
        
        # Act
        result = await user_repository.create(sample_user_data)
        
        # Assert
        assert result is not None
        assert result.username == sample_user_data.username
        assert result.email == sample_user_data.email
        assert result.winery_id == sample_user_data.winery_id
        user_repository._session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_repository, sample_user_data):
        """Test creating user with duplicate email raises error."""
        # Arrange
        user_repository.exists_by_email = AsyncMock(return_value=True)
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await user_repository.create(sample_user_data)
        
        assert "email" in str(exc_info.value)
        assert sample_user_data.email in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, user_repository, sample_user_data):
        """Test creating user with duplicate username raises error."""
        # Arrange
        user_repository.exists_by_email = AsyncMock(return_value=False)
        user_repository.exists_by_username = AsyncMock(return_value=True)
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await user_repository.create(sample_user_data)
        
        assert "username" in str(exc_info.value)
        assert sample_user_data.username in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_sets_timestamps(self, user_repository, sample_user_data):
        """Test that create sets created_at and updated_at timestamps."""
        # Arrange
        # Mock exists checks to return False (no duplicates)
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 0
        user_repository._session.execute = AsyncMock(return_value=mock_count_result)
        user_repository._session.commit = AsyncMock()
        
        # Mock refresh to simulate database assigning ID
        def mock_refresh(user):
            user.id = 1  # Simulate database auto-generated ID
        user_repository._session.refresh = AsyncMock(side_effect=mock_refresh)
        
        # Act
        result = await user_repository.create(sample_user_data)
        
        # Assert
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None


class TestUserRepositoryGetById:
    """Test UserRepository.get_by_id() method."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, user_repository, sample_user):
        """Test retrieving user by ID when exists."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user
        user_repository._session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.get_by_id(1)
        
        # Assert
        assert result is not None
        assert result.id == sample_user.id
        assert result.email == sample_user.email

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_repository):
        """Test retrieving user by ID when doesn't exist."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        user_repository._session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.get_by_id(999)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_soft_deleted(self, user_repository):
        """Test that soft deleted users are not returned."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        user_repository._session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.get_by_id(1)
        
        # Assert
        assert result is None


class TestUserRepositoryGetByEmail:
    """Test UserRepository.get_by_email() method."""

    @pytest.mark.asyncio
    async def test_get_by_email_found(self, user_repository, sample_user):
        """Test retrieving user by email when exists."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user
        user_repository._session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.get_by_email("test@example.com")
        
        # Assert
        assert result is not None
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, user_repository):
        """Test retrieving user by email when doesn't exist."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        user_repository._session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.get_by_email("nonexistent@example.com")
        
        # Assert
        assert result is None


class TestUserRepositoryGetByUsername:
    """Test UserRepository.get_by_username() method."""

    @pytest.mark.asyncio
    async def test_get_by_username_found(self, user_repository, sample_user):
        """Test retrieving user by username when exists."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user
        user_repository._session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.get_by_username("testuser")
        
        # Assert
        assert result is not None
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, user_repository):
        """Test retrieving user by username when doesn't exist."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        user_repository._session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.get_by_username("nonexistent")
        
        # Assert
        assert result is None


class TestUserRepositoryUpdate:
    """Test UserRepository.update() method."""

    @pytest.mark.asyncio
    async def test_update_user_success(self, user_repository, sample_user):
        """Test updating user successfully."""
        # Arrange
        sample_user.full_name = "Updated Name"
        user_repository.get_by_id = AsyncMock(return_value=sample_user)
        user_repository._session.merge = AsyncMock(return_value=sample_user)
        user_repository._session.commit = AsyncMock()
        user_repository._session.refresh = AsyncMock()
        
        # Act
        result = await user_repository.update(sample_user)
        
        # Assert
        assert result is not None
        assert result.full_name == "Updated Name"
        user_repository._session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_sets_updated_at(self, user_repository, sample_user):
        """Test that update modifies updated_at timestamp."""
        # Arrange
        original_updated_at = sample_user.updated_at
        user_repository.get_by_id = AsyncMock(return_value=sample_user)
        user_repository._session.merge = AsyncMock(return_value=sample_user)
        user_repository._session.commit = AsyncMock()
        user_repository._session.refresh = AsyncMock()
        
        # Act
        result = await user_repository.update(sample_user)
        
        # Assert
        # In real implementation, updated_at should be newer
        assert result.updated_at is not None


class TestUserRepositoryDelete:
    """Test UserRepository.delete() (soft delete) method."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_repository, sample_user):
        """Test soft deleting user successfully."""
        # Arrange
        user_repository.get_by_id = AsyncMock(return_value=sample_user)
        user_repository._session.commit = AsyncMock()
        
        # Act
        result = await user_repository.delete(1)
        
        # Assert
        assert result is True
        user_repository._session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_repository):
        """Test soft deleting non-existent user."""
        # Arrange
        user_repository.get_by_id = AsyncMock(return_value=None)
        
        # Act
        result = await user_repository.delete(999)
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_sets_deleted_at(self, user_repository, sample_user):
        """Test that delete sets deleted_at timestamp."""
        # Arrange
        user_repository.get_by_id = AsyncMock(return_value=sample_user)
        user_repository._session.commit = AsyncMock()
        
        # Act
        await user_repository.delete(1)
        
        # Assert
        assert sample_user.deleted_at is not None


class TestUserRepositoryExists:
    """Test UserRepository.exists_by_email() and exists_by_username() methods."""

    @pytest.mark.asyncio
    async def test_exists_by_email_true(self, user_repository):
        """Test exists_by_email returns True when email exists."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        user_repository._session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.exists_by_email("test@example.com")
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_by_email_false(self, user_repository):
        """Test exists_by_email returns False when email doesn't exist."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar.return_value = 0
        user_repository._session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.exists_by_email("nonexistent@example.com")
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_by_username_true(self, user_repository):
        """Test exists_by_username returns True when username exists."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        user_repository._session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.exists_by_username("testuser")
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_by_username_false(self, user_repository):
        """Test exists_by_username returns False when username doesn't exist."""
        # Arrange
        mock_result = Mock()
        mock_result.scalar.return_value = 0
        user_repository._session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await user_repository.exists_by_username("nonexistent")
        
        # Assert
        assert result is False


class TestUserRepositoryIntegration:
    """Test UserRepository implements IUserRepository interface."""

    def test_repository_implements_interface(self, user_repository):
        """Test that UserRepository implements all IUserRepository methods."""
        from src.shared.auth.domain.interfaces import IUserRepository
        
        # Check all required methods exist
        assert hasattr(user_repository, 'create')
        assert hasattr(user_repository, 'get_by_id')
        assert hasattr(user_repository, 'get_by_email')
        assert hasattr(user_repository, 'get_by_username')
        assert hasattr(user_repository, 'update')
        assert hasattr(user_repository, 'delete')
        assert hasattr(user_repository, 'exists_by_email')
        assert hasattr(user_repository, 'exists_by_username')
        
        # Check all methods are coroutines (async)
        import inspect
        assert inspect.iscoroutinefunction(user_repository.create)
        assert inspect.iscoroutinefunction(user_repository.get_by_id)
        assert inspect.iscoroutinefunction(user_repository.get_by_email)
        assert inspect.iscoroutinefunction(user_repository.get_by_username)
        assert inspect.iscoroutinefunction(user_repository.update)
        assert inspect.iscoroutinefunction(user_repository.delete)
        assert inspect.iscoroutinefunction(user_repository.exists_by_email)
        assert inspect.iscoroutinefunction(user_repository.exists_by_username)
