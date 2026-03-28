"""
Unit tests for UserContextMiddleware — JWT context binding (G8).

Verifies that user_id, winery_id, and user_role are correctly bound to
structlog contextvars from the Authorization Bearer header, and that any
failure (absent header, expired / invalid / malformed token) is silently
swallowed so the request always passes through.
"""

import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.shared.wine_fermentator_logging.middleware import UserContextMiddleware


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

TEST_SECRET = "test-secret-key-for-unit-tests-only-32chars"
TEST_USER_ID = 42
TEST_WINERY_ID = 7
TEST_ROLE = "winemaker"


def _make_token(
    user_id: int = TEST_USER_ID,
    winery_id: int = TEST_WINERY_ID,
    role: str = TEST_ROLE,
    secret: str = TEST_SECRET,
    expired: bool = False,
    algorithm: str = "HS256",
) -> str:
    """Build a signed JWT for testing."""
    now = datetime.now(timezone.utc)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    payload = {
        "sub": str(user_id),
        "winery_id": winery_id,
        "role": role,
        "iat": now,
        "exp": exp,
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def _make_app() -> FastAPI:
    """Create a minimal FastAPI app with only UserContextMiddleware."""
    app = FastAPI()
    app.add_middleware(UserContextMiddleware)

    @app.get("/test")
    async def endpoint():
        return {"ok": True}

    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestUserContextMiddlewareJwtBinding:
    """UserContextMiddleware decodes JWT and binds user context."""

    def test_valid_jwt_binds_user_id_winery_id_role(self, monkeypatch):
        """Valid Bearer token → user_id, winery_id, user_role bound to structlog."""
        monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
        token = _make_token()
        app = _make_app()

        with patch("structlog.contextvars.bind_contextvars") as mock_bind:
            client = TestClient(app)
            resp = client.get("/test", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        mock_bind.assert_called_once_with(
            user_id=str(TEST_USER_ID),
            winery_id=str(TEST_WINERY_ID),
            user_role=TEST_ROLE,
        )

    def test_no_authorization_header_skips_binding(self, monkeypatch):
        """No Authorization header → bind_contextvars not called."""
        monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
        app = _make_app()

        with patch("structlog.contextvars.bind_contextvars") as mock_bind:
            client = TestClient(app)
            resp = client.get("/test")

        assert resp.status_code == 200
        mock_bind.assert_not_called()

    def test_expired_jwt_skips_binding(self, monkeypatch):
        """Expired JWT → bind_contextvars not called (silent skip)."""
        monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
        token = _make_token(expired=True)
        app = _make_app()

        with patch("structlog.contextvars.bind_contextvars") as mock_bind:
            client = TestClient(app)
            resp = client.get("/test", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        mock_bind.assert_not_called()

    def test_invalid_signature_skips_binding(self, monkeypatch):
        """Token signed with wrong key → bind_contextvars not called."""
        monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
        token = _make_token(secret="completely-different-secret-key-!!")
        app = _make_app()

        with patch("structlog.contextvars.bind_contextvars") as mock_bind:
            client = TestClient(app)
            resp = client.get("/test", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        mock_bind.assert_not_called()

    def test_malformed_token_skips_binding(self, monkeypatch):
        """Completely garbage token string → bind_contextvars not called."""
        monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
        app = _make_app()

        with patch("structlog.contextvars.bind_contextvars") as mock_bind:
            client = TestClient(app)
            resp = client.get("/test", headers={"Authorization": "Bearer not.a.jwt"})

        assert resp.status_code == 200
        mock_bind.assert_not_called()

    def test_non_bearer_scheme_skips_binding(self, monkeypatch):
        """Authorization header without 'Bearer ' prefix is ignored."""
        monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
        token = _make_token()
        app = _make_app()

        with patch("structlog.contextvars.bind_contextvars") as mock_bind:
            client = TestClient(app)
            resp = client.get("/test", headers={"Authorization": f"Token {token}"})

        assert resp.status_code == 200
        mock_bind.assert_not_called()

    def test_invalid_token_never_blocks_request(self, monkeypatch):
        """Middleware must never block requests — even garbage tokens pass through."""
        monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
        app = _make_app()

        client = TestClient(app)
        resp = client.get("/test", headers={"Authorization": "Bearer garbage"})

        assert resp.status_code == 200

    def test_admin_role_is_bound_correctly(self, monkeypatch):
        """user_role is taken verbatim from the JWT 'role' claim."""
        monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
        token = _make_token(user_id=1, winery_id=1, role="admin")
        app = _make_app()

        with patch("structlog.contextvars.bind_contextvars") as mock_bind:
            client = TestClient(app)
            resp = client.get("/test", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        mock_bind.assert_called_once_with(
            user_id="1",
            winery_id="1",
            user_role="admin",
        )
