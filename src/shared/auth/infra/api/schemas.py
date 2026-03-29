"""
Pydantic schemas for Auth API endpoints.

Contains only schemas whose shape differs from the domain DTOs:
  - LoginRequestSchema / RefreshTokenRequestSchema — request bodies
  - AccessTokenResponseSchema — the /refresh response (access token only)

LoginResponse and UserResponse live in src.shared.auth.domain.dtos and are
already Pydantic BaseModels, so they are used directly as response_model.
"""

from pydantic import BaseModel


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


class AccessTokenResponseSchema(BaseModel):
    """New access token returned by POST /auth/refresh."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # seconds (15 min)
