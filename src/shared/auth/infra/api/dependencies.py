"""
FastAPI dependencies for authentication and authorization.

This module provides reusable dependencies for securing FastAPI endpoints,
including token validation, user context extraction, and role-based access control.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums import UserRole
from src.shared.auth.domain.errors import InvalidTokenError, TokenExpiredError
from src.shared.auth.domain.interfaces import IAuthService


# OAuth2 scheme for bearer token authentication
bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="JWT Bearer token authentication",
    auto_error=True,
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    auth_service: IAuthService = Depends(),
) -> UserContext:
    """
    Extract and validate user context from JWT bearer token.
    
    This dependency extracts the bearer token from the Authorization header,
    validates it using the auth service, and returns the user context.
    
    Args:
        credentials: HTTP bearer token credentials from request header
        auth_service: Authentication service for token validation
        
    Returns:
        UserContext with authenticated user information
        
    Raises:
        HTTPException: 401 if token is invalid, expired, or missing
        
    Example:
        ```python
        @router.get("/me")
        async def get_me(user: UserContext = Depends(get_current_user)):
            return {"user_id": user.user_id, "email": user.email}
        ```
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Extract token and validate
        token = credentials.credentials
        user_context = await auth_service.verify_token(token)
        return user_context
        
    except (InvalidTokenError, TokenExpiredError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: UserContext = Depends(get_current_user),
    auth_service: IAuthService = Depends(),
) -> UserContext:
    """
    Verify that the authenticated user is active.
    
    This dependency builds on get_current_user and additionally checks
    that the user account is active (not deactivated).
    
    Args:
        current_user: User context from get_current_user dependency
        auth_service: Authentication service for user status check
        
    Returns:
        UserContext if user is active
        
    Raises:
        HTTPException: 403 if user account is inactive
        
    Example:
        ```python
        @router.get("/protected")
        async def protected_route(user: UserContext = Depends(get_current_active_user)):
            return {"message": "Access granted"}
        ```
    """
    # Get full user details to check is_active status
    user = await auth_service.get_user(current_user.user_id)
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Create a dependency that requires one of the specified roles.
    
    This factory function creates a dependency that checks if the authenticated
    user has one of the allowed roles for accessing an endpoint.
    
    Args:
        *allowed_roles: One or more UserRole values that are allowed
        
    Returns:
        Async dependency function that validates user role
        
    Raises:
        HTTPException: 403 if user doesn't have any of the required roles
        
    Example:
        ```python
        # Single role
        @router.post("/admin")
        async def admin_only(user: UserContext = Depends(require_role(UserRole.ADMIN))):
            return {"message": "Admin access"}
        
        # Multiple roles
        @router.post("/write")
        async def write_access(
            user: UserContext = Depends(require_role(UserRole.ADMIN, UserRole.WINEMAKER))
        ):
            return {"message": "Write access granted"}
        ```
    """
    async def role_checker(
        current_user: UserContext = Depends(get_current_user),
    ) -> UserContext:
        """Check if user has one of the required roles."""
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[role.value for role in allowed_roles]}",
            )
        return current_user
    
    return role_checker


# Convenience dependencies for common role requirements
require_admin = require_role(UserRole.ADMIN)
require_winemaker = require_role(UserRole.ADMIN, UserRole.WINEMAKER)
require_operator = require_role(UserRole.ADMIN, UserRole.WINEMAKER, UserRole.OPERATOR)
