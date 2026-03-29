"""
Contract tests for POST /api/v1/auth/login via TestClient.

Uses a real AuthService backed by a shared-cache in-memory SQLite database
so that:
  - test-setup code (registering / updating users) runs async in the pytest
    event loop with its own session, committing to the shared-cache DB;
  - TestClient request-handling runs in its own event loop with its own session
    that opens a fresh connection to the *same* named shared-cache DB.

This avoids cross-event-loop session sharing while still letting both sides
see committed data.

Test matrix
-----------
Scenario                               | HTTP | error code
-------------------------------------- | ---- | -------------------
Valid credentials (active + verified)  | 200  | –
Wrong password                         | 401  | INVALID_CREDENTIALS
Unknown email                          | 401  | INVALID_CREDENTIALS
Unknown email ≡ bad password (no leak) | 401  | INVALID_CREDENTIALS
Inactive user  (is_active=False)       | 403  | USER_INACTIVE
Unverified user (is_verified=False)    | 403  | USER_NOT_VERIFIED
Missing password field                 | 422  | –
Missing email field                    | 422  | –
Empty JSON body                        | 422  | –
Response body shape (all fields)       | 200  | –
access_token ≠ refresh_token           | 200  | –
"""

import os
from typing import AsyncGenerator, Optional

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from src.shared.api.constants import API_V1_PREFIX
from src.shared.api.error_handlers import register_error_handlers
from src.shared.auth.domain.dtos import UserCreate, UserResponse, UserUpdate
from src.shared.auth.domain.enums import UserRole
from src.shared.auth.infra.api.auth_router import router
from src.shared.auth.infra.repositories import UserRepository
from src.shared.auth.infra.services import AuthService, JwtService, PasswordService
from src.shared.infra.database.fastapi_session import get_db_session
from src.shared.infra.orm.base_entity import Base

# Apply asyncio mark to every async test in this module.
pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Plain in-memory SQLite with StaticPool — one physical connection shared by
# all SQLAlchemy sessions on the same engine.  Because UserRepository.create()
# and update() always call session.commit(), data written by the setup service
# is immediately durable in the single connection and visible to the
# TestClient's sessions (which are also backed by the same StaticPool).
_DB_URL = "sqlite+aiosqlite:///:memory:"
_JWT_SECRET = "contract-test-secret-key"
_PASSWORD = "ValidPass123"

# ---------------------------------------------------------------------------
# Per-test engine — tables created fresh for every test
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def contract_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Per-test in-memory SQLite engine with StaticPool.

    StaticPool ensures all SQLAlchemy sessions (setup service + TestClient
    request sessions) share the same underlying aiosqlite connection, so
    committed data is immediately visible across sessions.

    Tables are created once per test and dropped on teardown.
    """
    os.environ.setdefault("AUTH_TEST_MODE", "1")
    os.environ["JWT_SECRET_KEY"] = _JWT_SECRET

    engine = create_async_engine(
        _DB_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    os.environ.pop("JWT_SECRET_KEY", None)


# ---------------------------------------------------------------------------
# Setup service — creates / modifies users in the shared DB before HTTP calls
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def setup_service(
    contract_engine: AsyncEngine,
) -> AsyncGenerator[AuthService, None]:
    """
    Real AuthService in a per-test async session.

    All writes are committed by UserRepository.create / update, so they are
    immediately visible to other connections on the shared-cache DB — including
    the connections opened by TestClient during request handling.
    """
    maker = async_sessionmaker(
        contract_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with maker() as session:
        yield AuthService(
            user_repository=UserRepository(session),
            password_service=PasswordService(),
            jwt_service=JwtService(secret_key=_JWT_SECRET),
        )


# ---------------------------------------------------------------------------
# TestClient fixture — each request gets its own independent DB session
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def login_client(contract_engine: AsyncEngine) -> TestClient:
    """
    TestClient backed by a minimal FastAPI app that includes only the auth
    router.  get_db_session is overridden so that every incoming request opens
    a fresh connection to the shared-cache engine (in TestClient's own event
    loop), then builds AuthService from it via the normal get_auth_service
    dependency chain.
    """
    maker = async_sessionmaker(
        contract_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with maker() as session:
            yield session

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router, prefix=API_V1_PREFIX)
    app.dependency_overrides[get_db_session] = _override_get_db

    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------

_LOGIN_URL = f"{API_V1_PREFIX}/auth/login"


async def _register_active_verified(
    service: AuthService,
    *,
    email: str,
    password: str = _PASSWORD,
    username: Optional[str] = None,
) -> UserResponse:
    """Register a user and immediately set is_active=True, is_verified=True."""
    _username = username or email.split("@")[0].replace(".", "_")
    user = await service.register_user(
        UserCreate(
            username=_username,
            email=email,
            password=password,
            full_name="Test User",
            winery_id=1,
            role=UserRole.WINEMAKER,
        )
    )
    # register_user always sets is_active=True, is_verified=False; verify now
    return await service.update_user(
        user.id, UserUpdate(is_active=True, is_verified=True)
    )


async def _register_inactive(
    service: AuthService,
    *,
    email: str,
    password: str = _PASSWORD,
    username: Optional[str] = None,
) -> UserResponse:
    """Register a user and immediately deactivate it (is_active=False)."""
    _username = username or email.split("@")[0].replace(".", "_")
    user = await service.register_user(
        UserCreate(
            username=_username,
            email=email,
            password=password,
            full_name="Test User",
            winery_id=1,
        )
    )
    return await service.update_user(user.id, UserUpdate(is_active=False))


# ---------------------------------------------------------------------------
# Tests — 200 happy path
# ---------------------------------------------------------------------------


async def test_valid_credentials_returns_200(
    setup_service: AuthService,
    login_client: TestClient,
) -> None:
    """Active + verified user with the correct password → 200."""
    await _register_active_verified(setup_service, email="ok@bodega.com")

    resp = login_client.post(
        _LOGIN_URL, json={"email": "ok@bodega.com", "password": _PASSWORD}
    )

    assert resp.status_code == 200


async def test_valid_credentials_response_body_has_all_fields(
    setup_service: AuthService,
    login_client: TestClient,
) -> None:
    """Response body must contain access_token, refresh_token, token_type, expires_in."""
    await _register_active_verified(setup_service, email="shape@bodega.com")

    resp = login_client.post(
        _LOGIN_URL, json={"email": "shape@bodega.com", "password": _PASSWORD}
    )

    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900


async def test_valid_credentials_tokens_are_jwt_strings(
    setup_service: AuthService,
    login_client: TestClient,
) -> None:
    """Both tokens must be non-empty strings with the three JWT dot-segments."""
    await _register_active_verified(setup_service, email="jwt@bodega.com")

    resp = login_client.post(
        _LOGIN_URL, json={"email": "jwt@bodega.com", "password": _PASSWORD}
    )

    data = resp.json()
    # JWT format: header.payload.signature — at least two dots
    assert data["access_token"].count(".") >= 2
    assert data["refresh_token"].count(".") >= 2


async def test_valid_credentials_access_and_refresh_are_distinct(
    setup_service: AuthService,
    login_client: TestClient,
) -> None:
    """access_token and refresh_token must be different values."""
    await _register_active_verified(setup_service, email="distinct@bodega.com")

    resp = login_client.post(
        _LOGIN_URL, json={"email": "distinct@bodega.com", "password": _PASSWORD}
    )

    data = resp.json()
    assert data["access_token"] != data["refresh_token"]


# ---------------------------------------------------------------------------
# Tests — 401 invalid credentials
# ---------------------------------------------------------------------------


async def test_wrong_password_returns_401(
    setup_service: AuthService,
    login_client: TestClient,
) -> None:
    """Correct email, wrong password → 401."""
    await _register_active_verified(setup_service, email="badpw@bodega.com")

    resp = login_client.post(
        _LOGIN_URL,
        json={"email": "badpw@bodega.com", "password": "ThisIsWrong99"},
    )

    assert resp.status_code == 401


async def test_wrong_password_error_body(
    setup_service: AuthService,
    login_client: TestClient,
) -> None:
    """Wrong password error body must follow RFC-7807 with code INVALID_CREDENTIALS."""
    await _register_active_verified(setup_service, email="errorbody@bodega.com")

    resp = login_client.post(
        _LOGIN_URL,
        json={"email": "errorbody@bodega.com", "password": "ThisIsWrong99"},
    )

    data = resp.json()
    assert data["status"] == 401
    assert data["code"] == "INVALID_CREDENTIALS"
    assert "detail" in data


async def test_unknown_email_returns_401(
    login_client: TestClient,
) -> None:
    """Email that does not exist in the database → 401."""
    resp = login_client.post(
        _LOGIN_URL,
        json={"email": "ghost@bodega.com", "password": _PASSWORD},
    )

    assert resp.status_code == 401


async def test_unknown_email_same_code_as_wrong_password(
    login_client: TestClient,
) -> None:
    """
    Unknown email must return the same error code as wrong password.

    This is a security requirement: the API must not reveal whether an email
    address is registered (enumeration protection).
    """
    resp = login_client.post(
        _LOGIN_URL,
        json={"email": "nobody@bodega.com", "password": _PASSWORD},
    )

    assert resp.json()["code"] == "INVALID_CREDENTIALS"


# ---------------------------------------------------------------------------
# Tests — 403 account status problems
# ---------------------------------------------------------------------------


async def test_inactive_user_returns_403(
    setup_service: AuthService,
    login_client: TestClient,
) -> None:
    """User with is_active=False → 403 (not 401)."""
    await _register_inactive(setup_service, email="inactive@bodega.com")

    resp = login_client.post(
        _LOGIN_URL,
        json={"email": "inactive@bodega.com", "password": _PASSWORD},
    )

    assert resp.status_code == 403


async def test_inactive_user_error_code(
    setup_service: AuthService,
    login_client: TestClient,
) -> None:
    """is_active=False must return code USER_INACTIVE."""
    await _register_inactive(setup_service, email="inactive2@bodega.com")

    resp = login_client.post(
        _LOGIN_URL,
        json={"email": "inactive2@bodega.com", "password": _PASSWORD},
    )

    assert resp.json()["code"] == "USER_INACTIVE"


async def test_unverified_user_returns_403(
    setup_service: AuthService,
    login_client: TestClient,
) -> None:
    """
    Freshly registered user (is_verified=False by default) → 403.

    register_user always sets is_verified=False; no update needed.
    """
    await setup_service.register_user(
        UserCreate(
            username="unverified1",
            email="unverified@bodega.com",
            password=_PASSWORD,
            full_name="Unverified User",
            winery_id=1,
        )
    )

    resp = login_client.post(
        _LOGIN_URL,
        json={"email": "unverified@bodega.com", "password": _PASSWORD},
    )

    assert resp.status_code == 403


async def test_unverified_user_error_code(
    setup_service: AuthService,
    login_client: TestClient,
) -> None:
    """is_verified=False must return code USER_NOT_VERIFIED."""
    await setup_service.register_user(
        UserCreate(
            username="unverified2",
            email="unverified2@bodega.com",
            password=_PASSWORD,
            full_name="Unverified User",
            winery_id=1,
        )
    )

    resp = login_client.post(
        _LOGIN_URL,
        json={"email": "unverified2@bodega.com", "password": _PASSWORD},
    )

    assert resp.json()["code"] == "USER_NOT_VERIFIED"


# ---------------------------------------------------------------------------
# Tests — 422 request validation (FastAPI / Pydantic)
# ---------------------------------------------------------------------------


async def test_missing_password_returns_422(login_client: TestClient) -> None:
    """Omitting the required `password` field → 422."""
    resp = login_client.post(_LOGIN_URL, json={"email": "x@bodega.com"})

    assert resp.status_code == 422


async def test_missing_email_returns_422(login_client: TestClient) -> None:
    """Omitting the required `email` field → 422."""
    resp = login_client.post(_LOGIN_URL, json={"password": _PASSWORD})

    assert resp.status_code == 422


async def test_empty_body_returns_422(login_client: TestClient) -> None:
    """Completely empty JSON body → 422."""
    resp = login_client.post(_LOGIN_URL, json={})

    assert resp.status_code == 422
