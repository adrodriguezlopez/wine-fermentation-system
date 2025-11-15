"""Tests for authentication DTOs."""

from datetime import datetime, timezone

import pytest

from src.shared.auth.domain.dtos import (
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    UserContext,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from src.shared.auth.domain.enums import UserRole


class TestUserContext:
    """Test UserContext DTO."""

    def test_user_context_creation(self):
        """Test creating a UserContext."""
        context = UserContext(
            user_id=1,
            winery_id=1,
            email="test@example.com",
            role=UserRole.WINEMAKER,
        )

        assert context.user_id == 1
        assert context.winery_id == 1
        assert context.email == "test@example.com"
        assert context.role == UserRole.WINEMAKER

    def test_user_context_is_frozen(self):
        """Test that UserContext is immutable."""
        context = UserContext(
            user_id=1,
            winery_id=1,
            email="test@example.com",
            role=UserRole.WINEMAKER,
        )

        with pytest.raises(Exception):  # FrozenInstanceError in dataclasses
            context.user_id = 2

    def test_has_role_single(self):
        """Test has_role() with single role."""
        context = UserContext(
            user_id=1,
            winery_id=1,
            email="test@example.com",
            role=UserRole.WINEMAKER,
        )

        assert context.has_role(UserRole.WINEMAKER) is True
        assert context.has_role(UserRole.ADMIN) is False

    def test_has_role_multiple(self):
        """Test has_role() with multiple roles."""
        context = UserContext(
            user_id=1,
            winery_id=1,
            email="test@example.com",
            role=UserRole.OPERATOR,
        )

        assert context.has_role(UserRole.WINEMAKER, UserRole.OPERATOR) is True
        assert context.has_role(UserRole.ADMIN, UserRole.VIEWER) is False

    def test_is_admin(self):
        """Test is_admin() helper method."""
        admin_context = UserContext(
            user_id=1,
            winery_id=1,
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        user_context = UserContext(
            user_id=2,
            winery_id=1,
            email="user@example.com",
            role=UserRole.WINEMAKER,
        )

        assert admin_context.is_admin() is True
        assert user_context.is_admin() is False


class TestLoginRequest:
    """Test LoginRequest DTO."""

    def test_login_request_creation(self):
        """Test creating a LoginRequest."""
        request = LoginRequest(
            email="test@example.com",
            password="secretpassword",
        )

        assert request.email == "test@example.com"
        assert request.password == "secretpassword"


class TestLoginResponse:
    """Test LoginResponse DTO."""

    def test_login_response_creation(self):
        """Test creating a LoginResponse."""
        response = LoginResponse(
            access_token="access.token.here",
            refresh_token="refresh.token.here",
        )

        assert response.access_token == "access.token.here"
        assert response.refresh_token == "refresh.token.here"
        assert response.token_type == "bearer"
        assert response.expires_in == 900

    def test_login_response_custom_values(self):
        """Test LoginResponse with custom token_type and expires_in."""
        response = LoginResponse(
            access_token="access.token.here",
            refresh_token="refresh.token.here",
            token_type="custom",
            expires_in=1800,
        )

        assert response.token_type == "custom"
        assert response.expires_in == 1800


class TestRefreshTokenRequest:
    """Test RefreshTokenRequest DTO."""

    def test_refresh_token_request_creation(self):
        """Test creating a RefreshTokenRequest."""
        request = RefreshTokenRequest(refresh_token="refresh.token.here")

        assert request.refresh_token == "refresh.token.here"


class TestUserCreate:
    """Test UserCreate DTO."""

    def test_user_create_with_defaults(self):
        """Test creating UserCreate with default values."""
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="password123",
            full_name="New User",
            winery_id=1,
        )

        assert user_data.username == "newuser"
        assert user_data.email == "newuser@example.com"
        assert user_data.password == "password123"
        assert user_data.full_name == "New User"
        assert user_data.winery_id == 1
        assert user_data.role == UserRole.VIEWER
        assert user_data.is_active is True
        assert user_data.is_verified is False

    def test_user_create_with_custom_values(self):
        """Test creating UserCreate with custom values."""
        user_data = UserCreate(
            username="admin",
            email="admin@example.com",
            password="adminpass",
            full_name="Admin User",
            winery_id=1,
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )

        assert user_data.role == UserRole.ADMIN
        assert user_data.is_verified is True


class TestUserUpdate:
    """Test UserUpdate DTO."""

    def test_user_update_all_none(self):
        """Test creating UserUpdate with all None values."""
        update_data = UserUpdate()

        assert update_data.username is None
        assert update_data.email is None
        assert update_data.full_name is None
        assert update_data.role is None
        assert update_data.is_active is None
        assert update_data.is_verified is None

    def test_user_update_partial(self):
        """Test UserUpdate with partial fields."""
        update_data = UserUpdate(
            full_name="Updated Name",
            is_verified=True,
        )

        assert update_data.full_name == "Updated Name"
        assert update_data.is_verified is True
        assert update_data.email is None


class TestUserResponse:
    """Test UserResponse DTO."""

    def test_user_response_creation(self):
        """Test creating a UserResponse."""
        now = datetime.now(timezone.utc)
        response = UserResponse(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            winery_id=1,
            role=UserRole.WINEMAKER,
            is_active=True,
            is_verified=True,
            last_login_at=now,
            created_at=now,
            updated_at=now,
        )

        assert response.id == 1
        assert response.username == "testuser"
        assert response.role == UserRole.WINEMAKER
        assert "password" not in response.__dict__
        assert "password_hash" not in response.__dict__

    def test_from_entity(self, sample_user):
        """Test creating UserResponse from User entity (using Mock)."""
        response = UserResponse.from_entity(sample_user)

        assert response.id == sample_user.id
        assert response.username == sample_user.username
        assert response.email == sample_user.email
        assert response.full_name == sample_user.full_name
        assert response.winery_id == sample_user.winery_id
        assert response.role == UserRole(sample_user.role)
        assert response.is_active == sample_user.is_active
        assert response.is_verified == sample_user.is_verified
        assert "password_hash" not in response.__dict__


class TestPasswordChangeRequest:
    """Test PasswordChangeRequest DTO."""

    def test_password_change_request_creation(self):
        """Test creating a PasswordChangeRequest."""
        request = PasswordChangeRequest(
            old_password="oldpassword",
            new_password="newpassword",
        )

        assert request.old_password == "oldpassword"
        assert request.new_password == "newpassword"


class TestPasswordResetRequest:
    """Test PasswordResetRequest DTO."""

    def test_password_reset_request_creation(self):
        """Test creating a PasswordResetRequest."""
        request = PasswordResetRequest(email="test@example.com")

        assert request.email == "test@example.com"


class TestPasswordResetConfirm:
    """Test PasswordResetConfirm DTO."""

    def test_password_reset_confirm_creation(self):
        """Test creating a PasswordResetConfirm."""
        confirm = PasswordResetConfirm(
            token="reset.token.here",
            new_password="newpassword",
        )

        assert confirm.token == "reset.token.here"
        assert confirm.new_password == "newpassword"
