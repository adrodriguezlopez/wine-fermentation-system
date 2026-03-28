"""
Pydantic schemas for Auth API endpoints.

Separates wire-format validation (Pydantic) from domain DTOs (dataclasses)
so FastAPI can generate accurate OpenAPI docs and perform request validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.shared.auth.domain.enums import UserRole


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class LoginRequestSchema(BaseModel):
    """Credentials for POST /auth/login."""

    email: str
    password: str


class RefreshTokenRequestSchema(BaseModel):
    """Refresh token for POST /auth/refresh."""

    refresh_token: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class LoginResponseSchema(BaseModel):
    """Tokens returned on successful login or refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # seconds (15 min)


class AccessTokenResponseSchema(BaseModel):
    """New access token returned by POST /auth/refresh."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # seconds (15 min)


class UserResponseSchema(BaseModel):
    """Public user data returned by GET /auth/me (Pydantic, not dataclass)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: str
    winery_id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
