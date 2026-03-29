"""
Auth API router — public authentication endpoints.

Endpoints:
  POST /auth/login    — exchange credentials for JWT tokens
  POST /auth/refresh  — exchange refresh token for new access token
  GET  /auth/me       — get authenticated user profile

All three endpoints are registered with prefix /api/v1 in each module's
main.py, producing final paths:
  POST /api/v1/auth/login
  POST /api/v1/auth/refresh
  GET  /api/v1/auth/me
"""

from fastapi import APIRouter, Depends, status

from src.shared.auth.domain.dtos import LoginRequest, LoginResponse, UserContext, UserResponse
from src.shared.auth.domain.interfaces import IAuthService
from src.shared.auth.infra.api.dependencies import get_auth_service, get_current_user
from src.shared.auth.infra.api.schemas import (
    AccessTokenResponseSchema,
    LoginRequestSchema,
    RefreshTokenRequestSchema,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and obtain JWT tokens",
)
async def login(
    request: LoginRequestSchema,
    auth_service: IAuthService = Depends(get_auth_service),
) -> LoginResponse:
    """
    Authenticate with email + password.

    Returns access_token (15 min) and refresh_token (7 days).
    Raises 401 on invalid credentials, 403 if account is inactive.
    """
    return await auth_service.login(
        LoginRequest(email=request.email, password=request.password)
    )


@router.post(
    "/refresh",
    response_model=AccessTokenResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    request: RefreshTokenRequestSchema,
    auth_service: IAuthService = Depends(get_auth_service),
) -> AccessTokenResponseSchema:
    """
    Exchange a valid refresh token for a new access token.

    The refresh token itself is NOT rotated — it remains valid until it
    expires (7 days from login).  Raises 401 if the refresh token is
    invalid or expired.
    """
    new_access_token = await auth_service.refresh_access_token(request.refresh_token)
    return AccessTokenResponseSchema(access_token=new_access_token)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user profile",
)
async def get_me(
    current_user: UserContext = Depends(get_current_user),
    auth_service: IAuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Return full profile of the currently authenticated user.

    Requires a valid Bearer token in the Authorization header.
    Raises 401 if the token is missing or invalid.
    """
    return await auth_service.get_user(current_user.user_id)
