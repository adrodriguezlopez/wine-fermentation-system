"""
Integration tests for authentication flows.

Tests end-to-end authentication scenarios with real database operations,
including user registration, login, token refresh, and password management.
"""

import pytest
from datetime import datetime, timezone

from src.shared.auth.domain.dtos import (
    LoginRequest,
    UserCreate,
    PasswordChangeRequest,
    RefreshTokenRequest,
)
from src.shared.auth.domain.enums import UserRole
from src.shared.auth.domain.errors import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserInactiveError,
    UserNotFoundError,
)
from src.shared.auth.infra.services import AuthService


@pytest.mark.asyncio
class TestUserRegistrationFlow:
    """Test user registration end-to-end flow."""

    async def test_register_new_user_creates_in_database(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test that registering a new user persists to database."""
        # Arrange
        user_create = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123",
            full_name="New User",
            winery_id=sample_winery_id,
            role=UserRole.WINEMAKER,
        )

        # Act
        user_response = await auth_service.register_user(user_create)

        # Assert
        assert user_response.id is not None
        assert user_response.username == "newuser"
        assert user_response.email == "newuser@example.com"
        assert user_response.full_name == "New User"
        assert user_response.winery_id == sample_winery_id
        assert user_response.role == UserRole.WINEMAKER
        assert user_response.is_active is True
        assert user_response.is_verified is False

        # Verify user can be retrieved
        retrieved_user = await auth_service.get_user(user_response.id)
        assert retrieved_user.username == "newuser"

    async def test_register_duplicate_email_fails(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test that registering with duplicate email raises error."""
        # Arrange - Create first user
        user_create = UserCreate(
            username="user1",
            email="duplicate@example.com",
            password="SecurePass123",
            full_name="User One",
            winery_id=sample_winery_id,
        )
        await auth_service.register_user(user_create)

        # Act & Assert - Try to create user with same email
        duplicate_user = UserCreate(
            username="user2",
            email="duplicate@example.com",
            password="SecurePass456",
            full_name="User Two",
            winery_id=sample_winery_id,
        )
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await auth_service.register_user(duplicate_user)
        
        assert exc_info.value.field == "email"
        assert exc_info.value.value == "duplicate@example.com"

    async def test_register_duplicate_username_fails(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test that registering with duplicate username raises error."""
        # Arrange - Create first user
        user_create = UserCreate(
            username="duplicateuser",
            email="user1@example.com",
            password="SecurePass123",
            full_name="User One",
            winery_id=sample_winery_id,
        )
        await auth_service.register_user(user_create)

        # Act & Assert - Try to create user with same username
        duplicate_user = UserCreate(
            username="duplicateuser",
            email="user2@example.com",
            password="SecurePass456",
            full_name="User Two",
            winery_id=sample_winery_id,
        )
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await auth_service.register_user(duplicate_user)
        
        assert exc_info.value.field == "username"
        assert exc_info.value.value == "duplicateuser"


@pytest.mark.asyncio
class TestLoginFlow:
    """Test user login end-to-end flow."""

    async def test_login_with_valid_credentials_returns_tokens(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test successful login returns access and refresh tokens."""
        # Arrange - Register a user
        user_create = UserCreate(
            username="loginuser",
            email="login@example.com",
            password="LoginPass123",
            full_name="Login User",
            winery_id=sample_winery_id,
        )
        registered_user = await auth_service.register_user(user_create)
        
        # Activate and verify user (normally done via email verification)
        from src.shared.auth.domain.dtos import UserUpdate
        await auth_service.update_user(
            registered_user.id,
            UserUpdate(is_active=True, is_verified=True)
        )

        # Act - Login
        login_request = LoginRequest(
            email="login@example.com",
            password="LoginPass123",
        )
        login_response = await auth_service.login(login_request)

        # Assert
        assert login_response.access_token is not None
        assert login_response.refresh_token is not None
        assert login_response.token_type == "bearer"
        assert isinstance(login_response.access_token, str)
        assert len(login_response.access_token) > 0

    async def test_login_with_invalid_password_fails(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test login fails with incorrect password."""
        # Arrange - Register a user
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="CorrectPass123",
            full_name="Test User",
            winery_id=sample_winery_id,
        )
        registered_user = await auth_service.register_user(user_create)
        
        # Activate user
        from src.shared.auth.domain.dtos import UserUpdate
        await auth_service.update_user(
            registered_user.id,
            UserUpdate(is_active=True, is_verified=True)
        )

        # Act & Assert - Try login with wrong password
        login_request = LoginRequest(
            email="test@example.com",
            password="WrongPassword",
        )
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(login_request)

    async def test_login_with_nonexistent_email_fails(self, auth_service: AuthService):
        """Test login fails for non-existent user."""
        # Act & Assert
        login_request = LoginRequest(
            email="nonexistent@example.com",
            password="AnyPassword123",
        )
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(login_request)

    async def test_login_inactive_user_fails(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test login fails for inactive user."""
        # Arrange - Register and deactivate user
        user_create = UserCreate(
            username="inactiveuser",
            email="inactive@example.com",
            password="InactivePass123",
            full_name="Inactive User",
            winery_id=sample_winery_id,
        )
        registered_user = await auth_service.register_user(user_create)
        
        # Verify user and then deactivate
        from src.shared.auth.domain.dtos import UserUpdate
        await auth_service.update_user(
            registered_user.id,
            UserUpdate(is_verified=True, is_active=False)
        )

        # Act & Assert - Try to login
        login_request = LoginRequest(
            email="inactive@example.com",
            password="InactivePass123",
        )
        with pytest.raises(UserInactiveError):
            await auth_service.login(login_request)


@pytest.mark.asyncio
class TestTokenRefreshFlow:
    """Test token refresh end-to-end flow."""

    async def test_refresh_token_generates_new_access_token(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test that refresh token can generate new access token."""
        # Arrange - Register and login user
        user_create = UserCreate(
            username="refreshuser",
            email="refresh@example.com",
            password="RefreshPass123",
            full_name="Refresh User",
            winery_id=sample_winery_id,
        )
        registered_user = await auth_service.register_user(user_create)
        
        from src.shared.auth.domain.dtos import UserUpdate
        await auth_service.update_user(
            registered_user.id,
            UserUpdate(is_active=True, is_verified=True)
        )
        
        login_request = LoginRequest(
            email="refresh@example.com",
            password="RefreshPass123",
        )
        login_response = await auth_service.login(login_request)
        original_access_token = login_response.access_token

        # Act - Refresh token
        new_access_token = await auth_service.refresh_access_token(
            login_response.refresh_token
        )

        # Assert - New token is valid and contains correct user info
        assert new_access_token is not None
        assert isinstance(new_access_token, str)
        
        # Verify new token is valid and contains correct user context
        user_context = await auth_service.verify_token(new_access_token)
        assert user_context.user_id == registered_user.id
        assert user_context.email == "refresh@example.com"
        assert user_context.winery_id == sample_winery_id

    async def test_verify_token_extracts_user_context(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test that access token contains valid user context."""
        # Arrange - Register, activate, and login user
        user_create = UserCreate(
            username="verifyuser",
            email="verify@example.com",
            password="VerifyPass123",
            full_name="Verify User",
            winery_id=sample_winery_id,
            role=UserRole.WINEMAKER,
        )
        registered_user = await auth_service.register_user(user_create)
        
        from src.shared.auth.domain.dtos import UserUpdate
        await auth_service.update_user(
            registered_user.id,
            UserUpdate(is_active=True, is_verified=True)
        )
        
        login_request = LoginRequest(
            email="verify@example.com",
            password="VerifyPass123",
        )
        login_response = await auth_service.login(login_request)

        # Act - Verify token
        user_context = await auth_service.verify_token(login_response.access_token)

        # Assert
        assert user_context.user_id == registered_user.id
        assert user_context.email == "verify@example.com"
        assert user_context.winery_id == sample_winery_id
        assert user_context.role == UserRole.WINEMAKER


@pytest.mark.asyncio
class TestPasswordManagement:
    """Test password change and reset flows."""

    async def test_change_password_flow(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test complete password change flow."""
        # Arrange - Register user
        user_create = UserCreate(
            username="passuser",
            email="passchange@example.com",
            password="OldPassword123",
            full_name="Password User",
            winery_id=sample_winery_id,
        )
        registered_user = await auth_service.register_user(user_create)
        
        from src.shared.auth.domain.dtos import UserUpdate
        await auth_service.update_user(
            registered_user.id,
            UserUpdate(is_active=True, is_verified=True)
        )

        # Act - Change password
        password_change = PasswordChangeRequest(
            old_password="OldPassword123",
            new_password="NewPassword456",
        )
        await auth_service.change_password(registered_user.id, password_change)

        # Assert - Old password should not work
        login_old = LoginRequest(
            email="passchange@example.com",
            password="OldPassword123",
        )
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(login_old)

        # Assert - New password should work
        login_new = LoginRequest(
            email="passchange@example.com",
            password="NewPassword456",
        )
        login_response = await auth_service.login(login_new)
        assert login_response.access_token is not None

    async def test_change_password_with_wrong_old_password_fails(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test password change fails with incorrect old password."""
        # Arrange - Register user
        user_create = UserCreate(
            username="wrongpass",
            email="wrongpass@example.com",
            password="CorrectPass123",
            full_name="Wrong Pass User",
            winery_id=sample_winery_id,
        )
        registered_user = await auth_service.register_user(user_create)

        # Act & Assert - Try to change with wrong old password
        password_change = PasswordChangeRequest(
            old_password="WrongOldPassword",
            new_password="NewPassword456",
        )
        with pytest.raises(InvalidCredentialsError):
            await auth_service.change_password(registered_user.id, password_change)


@pytest.mark.asyncio
class TestUserDeactivation:
    """Test user deactivation flow."""

    async def test_deactivate_user_prevents_login(
        self, auth_service: AuthService, sample_winery_id: int
    ):
        """Test that deactivated user cannot login."""
        # Arrange - Register and activate user
        user_create = UserCreate(
            username="deactivateuser",
            email="deactivate@example.com",
            password="DeactivatePass123",
            full_name="Deactivate User",
            winery_id=sample_winery_id,
        )
        registered_user = await auth_service.register_user(user_create)
        
        from src.shared.auth.domain.dtos import UserUpdate
        await auth_service.update_user(
            registered_user.id,
            UserUpdate(is_active=True, is_verified=True)
        )
        
        # Verify user can login
        login_request = LoginRequest(
            email="deactivate@example.com",
            password="DeactivatePass123",
        )
        login_response = await auth_service.login(login_request)
        assert login_response.access_token is not None

        # Act - Deactivate user
        await auth_service.deactivate_user(registered_user.id)

        # Assert - User cannot login anymore
        with pytest.raises(UserInactiveError):
            await auth_service.login(login_request)
