"""Data Transfer Objects for authentication and user management."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .enums.user_role import UserRole


@dataclass(frozen=True)
class UserContext:
    """
    Authenticated user context extracted from JWT token.
    
    This DTO represents the current user's identity and permissions
    for request processing. Immutable to prevent tampering.
    """
    
    user_id: int
    winery_id: int
    email: str
    role: UserRole
    
    def has_role(self, *roles: UserRole) -> bool:
        """Check if user has any of the specified roles."""
        return self.role in roles
    
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN


@dataclass
class LoginRequest:
    """Login credentials provided by user."""
    
    email: str
    password: str


@dataclass
class LoginResponse:
    """Successful login response with JWT tokens."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds


@dataclass
class RefreshTokenRequest:
    """Request to refresh access token using refresh token."""
    
    refresh_token: str


@dataclass
class UserCreate:
    """Data required to create a new user."""
    
    username: str
    email: str
    password: str
    full_name: str
    winery_id: int
    role: UserRole = UserRole.VIEWER
    is_active: bool = True
    is_verified: bool = False


@dataclass
class UserUpdate:
    """Data for updating an existing user (all fields optional)."""
    
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


@dataclass
class UserResponse:
    """Public user data returned by API (excludes password_hash)."""
    
    id: int
    username: str
    email: str
    full_name: str
    winery_id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_entity(cls, user) -> "UserResponse":
        """
        Create UserResponse from User entity.
        
        Args:
            user: User entity instance
            
        Returns:
            UserResponse with safe public data
        """
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            winery_id=user.winery_id,
            role=UserRole(user.role),
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


@dataclass
class PasswordChangeRequest:
    """Request to change user's password."""
    
    old_password: str
    new_password: str


@dataclass
class PasswordResetRequest:
    """Request to initiate password reset (forgot password)."""
    
    email: str


@dataclass
class PasswordResetConfirm:
    """Confirm password reset with token."""
    
    token: str
    new_password: str
