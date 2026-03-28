"""
Unit tests for auth_router.py.

Tests the three public auth endpoints using a mock AuthService so there
is no real database or JWT key needed.
"""

from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.shared.auth.domain.dtos import (
    LoginResponse,
    UserContext,
    UserResponse,
)
from src.shared.auth.domain.enums import UserRole
from src.shared.auth.domain.errors import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserNotFoundError,
)
from src.shared.auth.infra.api.auth_router import router
from src.shared.auth.infra.api.dependencies import get_auth_service, get_current_user
from src.shared.api.error_handlers import register_error_handlers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 3, 28, 12, 0, 0, tzinfo=timezone.utc)


def _make_user_response(**overrides) -> UserResponse:
    defaults = dict(
        id=1,
        username="winemaker1",
        email="winemaker@bodega.com",
        full_name="Ana García",
        winery_id=10,
        role=UserRole.WINEMAKER,
        is_active=True,
        is_verified=True,
        last_login_at=_NOW,
        created_at=_NOW,
        updated_at=_NOW,
    )
    defaults.update(overrides)
    return UserResponse(**defaults)


def _make_user_context(**overrides) -> UserContext:
    defaults = dict(
        user_id=1,
        winery_id=10,
        email="winemaker@bodega.com",
        role=UserRole.WINEMAKER,
    )
    defaults.update(overrides)
    return UserContext(**defaults)


def _app_with_mock(mock_service, user_context: UserContext = None) -> FastAPI:
    """Create a minimal FastAPI test app with overridden auth dependencies."""
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_auth_service] = lambda: mock_service
    if user_context is not None:
        app.dependency_overrides[get_current_user] = lambda: user_context
    return app


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login."""

    def test_login_success_returns_tokens(self):
        """Valid credentials → 200 with access_token, refresh_token."""
        mock = AsyncMock()
        mock.login.return_value = LoginResponse(
            access_token="acc.tok",
            refresh_token="ref.tok",
        )
        client = TestClient(_app_with_mock(mock))

        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "winemaker@bodega.com", "password": "Secret123"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "acc.tok"
        assert data["refresh_token"] == "ref.tok"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900

    def test_login_calls_service_with_correct_args(self):
        """Router must forward email + password to auth_service.login()."""
        mock = AsyncMock()
        mock.login.return_value = LoginResponse(
            access_token="a", refresh_token="r"
        )
        client = TestClient(_app_with_mock(mock))

        client.post(
            "/api/v1/auth/login",
            json={"email": "admin@bodega.com", "password": "Pass@123"},
        )

        mock.login.assert_called_once()
        call_arg = mock.login.call_args[0][0]
        assert call_arg.email == "admin@bodega.com"
        assert call_arg.password == "Pass@123"

    def test_login_invalid_credentials_returns_401(self):
        """InvalidCredentialsError → 401 via global error handler."""
        mock = AsyncMock()
        mock.login.side_effect = InvalidCredentialsError()
        client = TestClient(_app_with_mock(mock), raise_server_exceptions=False)

        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "x@x.com", "password": "wrong"},
        )

        assert resp.status_code == 401

    def test_login_missing_password_returns_422(self):
        """Missing required field → 422 Unprocessable Entity."""
        mock = AsyncMock()
        client = TestClient(_app_with_mock(mock))

        resp = client.post("/api/v1/auth/login", json={"email": "x@x.com"})

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/auth/refresh
# ---------------------------------------------------------------------------


class TestRefreshTokenEndpoint:
    """Tests for POST /api/v1/auth/refresh."""

    def test_refresh_success_returns_new_access_token(self):
        """Valid refresh token → 200 with new access_token."""
        mock = AsyncMock()
        mock.refresh_access_token.return_value = "new.acc.tok"
        client = TestClient(_app_with_mock(mock))

        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "valid.ref.tok"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"] == "new.acc.tok"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900

    def test_refresh_calls_service_with_token(self):
        """Router must forward refresh_token to auth_service.refresh_access_token()."""
        mock = AsyncMock()
        mock.refresh_access_token.return_value = "tok"
        client = TestClient(_app_with_mock(mock))

        client.post("/api/v1/auth/refresh", json={"refresh_token": "mytoken"})

        mock.refresh_access_token.assert_called_once_with("mytoken")

    def test_refresh_invalid_token_returns_401(self):
        """InvalidTokenError → 401 via global error handler."""
        mock = AsyncMock()
        mock.refresh_access_token.side_effect = InvalidTokenError()
        client = TestClient(_app_with_mock(mock), raise_server_exceptions=False)

        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "bad.token"},
        )

        assert resp.status_code == 401

    def test_refresh_missing_token_returns_422(self):
        """Missing refresh_token field → 422."""
        mock = AsyncMock()
        client = TestClient(_app_with_mock(mock))

        resp = client.post("/api/v1/auth/refresh", json={})

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me
# ---------------------------------------------------------------------------


class TestGetMeEndpoint:
    """Tests for GET /api/v1/auth/me."""

    def test_get_me_returns_user_profile(self):
        """Valid token → 200 with full Pydantic UserResponseSchema."""
        mock = AsyncMock()
        user_ctx = _make_user_context()
        mock.get_user.return_value = _make_user_response()
        client = TestClient(_app_with_mock(mock, user_context=user_ctx))

        resp = client.get("/api/v1/auth/me")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert data["username"] == "winemaker1"
        assert data["email"] == "winemaker@bodega.com"
        assert data["full_name"] == "Ana García"
        assert data["winery_id"] == 10
        assert data["role"] == UserRole.WINEMAKER.value
        assert data["is_active"] is True
        assert data["is_verified"] is True

    def test_get_me_calls_service_with_user_id(self):
        """Router must call auth_service.get_user(user_id) from token context."""
        mock = AsyncMock()
        user_ctx = _make_user_context(user_id=42)
        mock.get_user.return_value = _make_user_response(id=42)
        client = TestClient(_app_with_mock(mock, user_context=user_ctx))

        client.get("/api/v1/auth/me")

        mock.get_user.assert_called_once_with(42)

    def test_get_me_user_not_found_returns_404(self):
        """UserNotFoundError → 404 via global error handler."""
        mock = AsyncMock()
        user_ctx = _make_user_context()
        mock.get_user.side_effect = UserNotFoundError(1)
        client = TestClient(
            _app_with_mock(mock, user_context=user_ctx),
            raise_server_exceptions=False,
        )

        resp = client.get("/api/v1/auth/me")

        assert resp.status_code == 404

    def test_get_me_no_token_returns_403(self):
        """No auth override (no token) → 403 from bearer_scheme auto_error."""
        mock = AsyncMock()
        # Don't override get_current_user — let bearer_scheme reject the request
        app = FastAPI()
        register_error_handlers(app)
        app.include_router(router, prefix="/api/v1")
        app.dependency_overrides[get_auth_service] = lambda: mock
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.get("/api/v1/auth/me")

        assert resp.status_code == 403
