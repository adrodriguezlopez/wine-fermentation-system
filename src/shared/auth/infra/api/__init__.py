"""
FastAPI API layer components.

This package contains FastAPI-specific components including
dependencies, middleware, and utilities for the auth module.
"""

from src.shared.auth.infra.api.dependencies import (
    bearer_scheme,
    get_auth_service,
    get_current_user,
    get_current_active_user,
    require_role,
    require_admin,
    require_winemaker,
    require_operator,
)
from src.shared.auth.infra.api.auth_router import router as auth_router

__all__ = [
    "auth_router",
    "bearer_scheme",
    "get_auth_service",
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "require_admin",
    "require_winemaker",
    "require_operator",
]
