"""
FastAPI API layer components.

This package contains FastAPI-specific components including
dependencies, middleware, and utilities for the auth module.
"""

from src.shared.auth.infra.api.dependencies import (
    bearer_scheme,
    get_current_user,
    get_current_active_user,
    require_role,
    require_admin,
    require_winemaker,
    require_operator,
)

__all__ = [
    "bearer_scheme",
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "require_admin",
    "require_winemaker",
    "require_operator",
]
