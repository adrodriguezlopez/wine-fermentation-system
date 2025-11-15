"""
Unit tests for AuthService.

Tests the authentication service implementation following TDD principles.
Covers login, registration, token refresh, user management, and password operations.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone

from src.shared.auth.domain.dtos import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
    PasswordChangeRequest,
    UserContext,
)
from src.shared.auth.domain.enums import UserRole
from src.shared.auth.domain.errors import (
    InvalidCredentialsError,
    UserNotFoundError,
    UserAlreadyExistsError,
    UserInactiveError,
    UserNotVerifiedError,
    InvalidTokenError,
)
from src.shared.auth.domain.interfaces import IAuthService
from src.shared.auth.infra.services import AuthService


@pytest.fixture
def mock_user_repository():
    """Create mock UserRepository."""
    return AsyncMock()


@pytest.fixture
def mock_password_service():
    """Create mock PasswordService."""
    return Mock()


@pytest.fixture
def mock_jwt_service():
    """Create mock JwtService."""
    return Mock()


@pytest.fixture
def auth_service(mock_user_repository, mock_password_service, mock_jwt_service):
    """Create AuthService instance with mocked dependencies."""
    return AuthService(
        user_repository=mock_user_repository,
        password_service=mock_password_service,
        jwt_service=mock_jwt_service,
    )


@pytest.fixture
def sample_user_entity():
    """Create a sample User entity for testing."""
    from unittest.mock import Mock
    
    user = Mock()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.password_hash = "$2b$12$hashed_password"
    user.winery_id = 1
    user.role = UserRole.WINEMAKER
    user.is_active = True
    user.is_verified = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    
    return user


class TestAuthServiceInterface:
    """Test that AuthService implements IAuthService interface."""

    def test_service_implements_interface(self, auth_service):
        """Test that AuthService implements IAuthService protocol."""
        assert isinstance(auth_service, IAuthService)


class TestLogin:
    """Test login functionality."""

    @pytest.mark.asyncio
    async def test_login_success(
        self, auth_service, mock_user_repository, mock_password_service, 
        mock_jwt_service, sample_user_entity
    ):
        """Test successful login returns tokens."""
        # Arrange
        login_request = LoginRequest(email="test@example.com", password="Password123")
        mock_user_repository.get_by_email.return_value = sample_user_entity
        mock_password_service.verify_password.return_value = True
        mock_jwt_service.encode_access_token.return_value = "access_token_123"
        mock_jwt_service.encode_refresh_token.return_value = "refresh_token_123"
        
        # Act
        response = await auth_service.login(login_request)
        
        # Assert
        assert isinstance(response, LoginResponse)
        assert response.access_token == "access_token_123"
        assert response.refresh_token == "refresh_token_123"
        assert response.token_type == "bearer"
        mock_user_repository.get_by_email.assert_awaited_once_with("test@example.com")
        mock_password_service.verify_password.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_user_not_found(
        self, auth_service, mock_user_repository
    ):
        """Test login fails when user doesn't exist."""
        # Arrange
        login_request = LoginRequest(email="nonexistent@example.com", password="Password123")
        mock_user_repository.get_by_email.return_value = None
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(login_request)

    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self, auth_service, mock_user_repository, mock_password_service, sample_user_entity
    ):
        """Test login fails with incorrect password."""
        # Arrange
        login_request = LoginRequest(email="test@example.com", password="WrongPassword")
        mock_user_repository.get_by_email.return_value = sample_user_entity
        mock_password_service.verify_password.return_value = False
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(login_request)

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self, auth_service, mock_user_repository, mock_password_service, sample_user_entity
    ):
        """Test login fails for inactive user."""
        # Arrange
        sample_user_entity.is_active = False
        login_request = LoginRequest(email="test@example.com", password="Password123")
        mock_user_repository.get_by_email.return_value = sample_user_entity
        mock_password_service.verify_password.return_value = True
        
        # Act & Assert
        with pytest.raises(UserInactiveError):
            await auth_service.login(login_request)

    @pytest.mark.asyncio
    async def test_login_unverified_user(
        self, auth_service, mock_user_repository, mock_password_service, sample_user_entity
    ):
        """Test login fails for unverified user."""
        # Arrange
        sample_user_entity.is_verified = False
        login_request = LoginRequest(email="test@example.com", password="Password123")
        mock_user_repository.get_by_email.return_value = sample_user_entity
        mock_password_service.verify_password.return_value = True
        
        # Act & Assert
        with pytest.raises(UserNotVerifiedError):
            await auth_service.login(login_request)


class TestRefreshAccessToken:
    """Test token refresh functionality."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, auth_service, mock_jwt_service, mock_user_repository, sample_user_entity
    ):
        """Test successful token refresh."""
        # Arrange
        refresh_token = "valid_refresh_token"
        mock_jwt_service.decode_token.return_value = {"sub": "1"}  # Returns user_id
        mock_user_repository.get_by_id.return_value = sample_user_entity
        mock_jwt_service.encode_access_token.return_value = "new_access_token"
        
        # Act
        new_token = await auth_service.refresh_access_token(refresh_token)
        
        # Assert
        assert new_token == "new_access_token"
        mock_jwt_service.decode_token.assert_called_once_with(refresh_token)
        mock_user_repository.get_by_id.assert_awaited_once_with(1)

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_token(
        self, auth_service, mock_jwt_service
    ):
        """Test refresh fails with invalid token."""
        # Arrange
        mock_jwt_service.decode_token.side_effect = InvalidTokenError()
        
        # Act & Assert
        with pytest.raises(InvalidTokenError):
            await auth_service.refresh_access_token("invalid_token")

    @pytest.mark.asyncio
    async def test_refresh_token_user_not_found(
        self, auth_service, mock_jwt_service, mock_user_repository
    ):
        """Test refresh fails when user no longer exists."""
        # Arrange
        mock_jwt_service.decode_token.return_value = {"sub": "999"}  # Non-existent user
        mock_user_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await auth_service.refresh_access_token("valid_token")


class TestRegisterUser:
    """Test user registration functionality."""

    @pytest.mark.asyncio
    async def test_register_user_success(
        self, auth_service, mock_user_repository, mock_password_service, sample_user_entity
    ):
        """Test successful user registration."""
        # Arrange
        user_create = UserCreate(
            username="newuser",
            email="new@example.com",
            password="Password123",
            full_name="New User",
            winery_id=1,
            role=UserRole.WINEMAKER,
        )
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.exists_by_username.return_value = False
        mock_password_service.validate_password_strength.return_value = True
        mock_password_service.hash_password.return_value = "$2b$12$hashed_new_password"
        mock_user_repository.create.return_value = sample_user_entity
        
        # Act
        response = await auth_service.register_user(user_create)
        
        # Assert
        assert isinstance(response, UserResponse)
        assert response.id == sample_user_entity.id
        mock_password_service.validate_password_strength.assert_called_once_with("Password123")
        mock_password_service.hash_password.assert_called_once_with("Password123")

    @pytest.mark.asyncio
    async def test_register_user_email_exists(
        self, auth_service, mock_user_repository
    ):
        """Test registration fails when email already exists."""
        # Arrange
        user_create = UserCreate(
            username="newuser",
            email="existing@example.com",
            password="Password123",
            full_name="New User",
            winery_id=1,
        )
        mock_user_repository.exists_by_email.return_value = True
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError):
            await auth_service.register_user(user_create)

    @pytest.mark.asyncio
    async def test_register_user_username_exists(
        self, auth_service, mock_user_repository
    ):
        """Test registration fails when username already exists."""
        # Arrange
        user_create = UserCreate(
            username="existinguser",
            email="new@example.com",
            password="Password123",
            full_name="New User",
            winery_id=1,
        )
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.exists_by_username.return_value = True
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError):
            await auth_service.register_user(user_create)

    @pytest.mark.asyncio
    async def test_register_user_weak_password(
        self, auth_service, mock_user_repository, mock_password_service
    ):
        """Test registration fails with weak password."""
        # Arrange
        user_create = UserCreate(
            username="newuser",
            email="new@example.com",
            password="weak",
            full_name="New User",
            winery_id=1,
        )
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.exists_by_username.return_value = False
        mock_password_service.validate_password_strength.return_value = False
        
        # Act & Assert
        with pytest.raises(ValueError):
            await auth_service.register_user(user_create)


class TestVerifyToken:
    """Test token verification functionality."""

    @pytest.mark.asyncio
    async def test_verify_token_success(
        self, auth_service, mock_jwt_service
    ):
        """Test successful token verification."""
        # Arrange
        token = "valid_token"
        user_context = UserContext(
            user_id=1, winery_id=1, email="test@example.com", role=UserRole.WINEMAKER
        )
        mock_jwt_service.extract_user_context.return_value = user_context
        
        # Act
        result = await auth_service.verify_token(token)
        
        # Assert
        assert result == user_context
        mock_jwt_service.extract_user_context.assert_called_once_with(token)

    @pytest.mark.asyncio
    async def test_verify_token_invalid(
        self, auth_service, mock_jwt_service
    ):
        """Test verification fails with invalid token."""
        # Arrange
        mock_jwt_service.extract_user_context.side_effect = InvalidTokenError()
        
        # Act & Assert
        with pytest.raises(InvalidTokenError):
            await auth_service.verify_token("invalid_token")


class TestGetUser:
    """Test get user functionality."""

    @pytest.mark.asyncio
    async def test_get_user_success(
        self, auth_service, mock_user_repository, sample_user_entity
    ):
        """Test successful user retrieval."""
        # Arrange
        mock_user_repository.get_by_id.return_value = sample_user_entity
        
        # Act
        response = await auth_service.get_user(1)
        
        # Assert
        assert isinstance(response, UserResponse)
        assert response.id == sample_user_entity.id
        mock_user_repository.get_by_id.assert_awaited_once_with(1)

    @pytest.mark.asyncio
    async def test_get_user_not_found(
        self, auth_service, mock_user_repository
    ):
        """Test get user fails when user doesn't exist."""
        # Arrange
        mock_user_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await auth_service.get_user(999)


class TestUpdateUser:
    """Test user update functionality."""

    @pytest.mark.asyncio
    async def test_update_user_success(
        self, auth_service, mock_user_repository, sample_user_entity
    ):
        """Test successful user update."""
        # Arrange
        user_update = UserUpdate(email="updated@example.com")
        updated_user = sample_user_entity
        updated_user.email = "updated@example.com"
        mock_user_repository.get_by_id.return_value = sample_user_entity
        mock_user_repository.update.return_value = updated_user
        
        # Act
        response = await auth_service.update_user(1, user_update)
        
        # Assert
        assert isinstance(response, UserResponse)
        assert response.email == "updated@example.com"
        mock_user_repository.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found(
        self, auth_service, mock_user_repository
    ):
        """Test update fails when user doesn't exist."""
        # Arrange
        user_update = UserUpdate(email="updated@example.com")
        mock_user_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await auth_service.update_user(999, user_update)


class TestChangePassword:
    """Test password change functionality."""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, auth_service, mock_user_repository, mock_password_service, sample_user_entity
    ):
        """Test successful password change."""
        # Arrange
        password_change = PasswordChangeRequest(
            old_password="OldPassword123",
            new_password="NewPassword123",
        )
        mock_user_repository.get_by_id.return_value = sample_user_entity
        mock_password_service.verify_password.return_value = True
        mock_password_service.validate_password_strength.return_value = True
        mock_password_service.hash_password.return_value = "$2b$12$new_hash"
        
        # Act
        await auth_service.change_password(1, password_change)
        
        # Assert
        mock_password_service.verify_password.assert_called_once()
        mock_password_service.validate_password_strength.assert_called_once_with("NewPassword123")
        mock_user_repository.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_change_password_user_not_found(
        self, auth_service, mock_user_repository
    ):
        """Test password change fails when user doesn't exist."""
        # Arrange
        password_change = PasswordChangeRequest(
            old_password="OldPassword123",
            new_password="NewPassword123",
        )
        mock_user_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await auth_service.change_password(999, password_change)

    @pytest.mark.asyncio
    async def test_change_password_incorrect_old_password(
        self, auth_service, mock_user_repository, mock_password_service, sample_user_entity
    ):
        """Test password change fails with incorrect old password."""
        # Arrange
        password_change = PasswordChangeRequest(
            old_password="WrongOldPassword",
            new_password="NewPassword123",
        )
        mock_user_repository.get_by_id.return_value = sample_user_entity
        mock_password_service.verify_password.return_value = False
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await auth_service.change_password(1, password_change)

    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(
        self, auth_service, mock_user_repository, mock_password_service, sample_user_entity
    ):
        """Test password change fails with weak new password."""
        # Arrange
        password_change = PasswordChangeRequest(
            old_password="OldPassword123",
            new_password="weak",
        )
        mock_user_repository.get_by_id.return_value = sample_user_entity
        mock_password_service.verify_password.return_value = True
        mock_password_service.validate_password_strength.return_value = False
        
        # Act & Assert
        with pytest.raises(ValueError):
            await auth_service.change_password(1, password_change)


class TestDeactivateUser:
    """Test user deactivation functionality."""

    @pytest.mark.asyncio
    async def test_deactivate_user_success(
        self, auth_service, mock_user_repository, sample_user_entity
    ):
        """Test successful user deactivation."""
        # Arrange
        mock_user_repository.get_by_id.return_value = sample_user_entity
        
        # Act
        await auth_service.deactivate_user(1)
        
        # Assert
        mock_user_repository.get_by_id.assert_awaited_once_with(1)
        mock_user_repository.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(
        self, auth_service, mock_user_repository
    ):
        """Test deactivation fails when user doesn't exist."""
        # Arrange
        mock_user_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundError):
            await auth_service.deactivate_user(999)
