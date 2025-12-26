"""
Unit tests for FastAPI dependencies.

Tests cover authentication dependencies including token extraction,
user context retrieval, and role-based access control.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums import UserRole
from src.shared.auth.domain.errors import (
    InvalidTokenError,
    TokenExpiredError,
    UserInactiveError,
    InsufficientPermissions,
)
from src.shared.auth.infra.api.dependencies import (
    get_current_user,
    get_current_active_user,
    require_role,
)


class TestGetCurrentUser:
    """Test suite for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test successful user context extraction from valid token."""
        # Arrange
        mock_auth_service = AsyncMock()
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"
        
        expected_context = UserContext(
            user_id=1,
            winery_id=1,
            email="test@example.com",
            role=UserRole.WINEMAKER,
        )
        mock_auth_service.verify_token.return_value = expected_context

        # Act
        result = await get_current_user(mock_credentials, mock_auth_service)

        # Assert
        assert result == expected_context
        mock_auth_service.verify_token.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test that invalid token raises InvalidTokenError (ADR-026)."""
        # Arrange
        mock_auth_service = AsyncMock()
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"
        mock_auth_service.verify_token.side_effect = InvalidTokenError()

        # Act & Assert - Now expects domain error instead of HTTPException
        with pytest.raises(InvalidTokenError):
            await get_current_user(mock_credentials, mock_auth_service)

    async def test_get_current_user_expired_token(self):
        """Test that expired token raises TokenExpiredError (ADR-026)."""
        # Arrange
        mock_auth_service = AsyncMock()
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "expired_token"
        mock_auth_service.verify_token.side_effect = TokenExpiredError()

        # Act & Assert - Now expects domain error instead of HTTPException
        with pytest.raises(TokenExpiredError):
            await get_current_user(mock_credentials, mock_auth_service)

    async def test_get_current_user_no_credentials(self):
        """Test that missing credentials raises InvalidTokenError (ADR-026)."""
        # Arrange
        mock_auth_service = AsyncMock()
        mock_credentials = None

        # Act & Assert - Now expects domain error instead of HTTPException
        with pytest.raises(InvalidTokenError):
            await get_current_user(mock_credentials, mock_auth_service)


class TestGetCurrentActiveUser:
    """Test suite for get_current_active_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self):
        """Test that active user is returned successfully."""
        # Arrange
        mock_auth_service = AsyncMock()
        mock_user = Mock()
        mock_user.is_active = True
        mock_auth_service.get_user.return_value = mock_user
        
        user_context = UserContext(
            user_id=1,
            winery_id=1,
            email="test@example.com",
            role=UserRole.WINEMAKER,
        )

        # Act
        result = await get_current_active_user(user_context, mock_auth_service)

        # Assert
        assert result == user_context
        mock_auth_service.get_user.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self):
        """Test that inactive user raises 403 HTTPException."""
        # Arrange
        mock_auth_service = AsyncMock()
        mock_user = Mock()
        mock_user.is_active = False
        mock_auth_service.get_user.return_value = mock_user
        
        user_context = UserContext(
            user_id=1,
            winery_id=1,
            email="test@example.com",
            role=UserRole.WINEMAKER,
        )

        # Act & Assert - Now expects domain error instead of HTTPException
        with pytest.raises(UserInactiveError):
            await get_current_active_user(user_context, mock_auth_service)


class TestRequireRole:
    """Test suite for require_role dependency factory."""

    @pytest.mark.asyncio
    async def test_require_role_single_role_allowed(self):
        """Test that user with required role is allowed."""
        # Arrange
        user_context = UserContext(
            user_id=1,
            winery_id=1,
            email="admin@example.com",
            role=UserRole.ADMIN,
        )
        dependency = require_role(UserRole.ADMIN)

        # Act
        result = await dependency(user_context)

        # Assert
        assert result == user_context

    @pytest.mark.asyncio
    async def test_require_role_multiple_roles_allowed(self):
        """Test that user with one of multiple required roles is allowed."""
        # Arrange
        user_context = UserContext(
            user_id=1,
            winery_id=1,
            email="winemaker@example.com",
            role=UserRole.WINEMAKER,
        )
        dependency = require_role(UserRole.ADMIN, UserRole.WINEMAKER)

        # Act
        result = await dependency(user_context)

        # Assert
        assert result == user_context

    async def test_require_role_insufficient_permissions(self):
        """Test that user without required role raises InsufficientPermissions (ADR-026)."""
        # Arrange
        user_context = UserContext(
            user_id=1,
            winery_id=1,
            email="viewer@example.com",
            role=UserRole.VIEWER,
        )
        dependency = require_role(UserRole.ADMIN)

        # Act & Assert - Now expects domain error instead of HTTPException
        with pytest.raises(InsufficientPermissions):
            await dependency(user_context)

    async def test_require_role_viewer_cannot_access_admin(self):
        """Test that VIEWER role cannot access ADMIN-only endpoints (ADR-026)."""
        # Arrange
        user_context = UserContext(
            user_id=1,
            winery_id=1,
            email="viewer@example.com",
            role=UserRole.VIEWER,
        )
        dependency = require_role(UserRole.ADMIN, UserRole.WINEMAKER)

        # Act & Assert - Now expects domain error instead of HTTPException
        with pytest.raises(InsufficientPermissions):
            await dependency(user_context)

    @pytest.mark.asyncio
    async def test_require_role_operator_allowed_for_operator(self):
        """Test that OPERATOR role can access OPERATOR endpoints."""
        # Arrange
        user_context = UserContext(
            user_id=1,
            winery_id=1,
            email="operator@example.com",
            role=UserRole.OPERATOR,
        )
        dependency = require_role(UserRole.OPERATOR, UserRole.WINEMAKER)

        # Act
        result = await dependency(user_context)

        # Assert
        assert result == user_context
