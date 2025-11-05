"""Auth domain layer - entities, DTOs, interfaces, and business rules."""

from .dtos import (
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    UserContext,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from .entities.user import User
from .enums import UserRole
from .errors import (
    AuthenticationError,
    AuthorizationError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    UserAlreadyExistsError,
    UserInactiveError,
    UserNotFoundError,
    UserNotVerifiedError,
)
from .interfaces import (
    IAuthService,
    IJwtService,
    IPasswordService,
    IUserRepository,
)

__all__ = [
    # Entities
    "User",
    # Enums
    "UserRole",
    # DTOs
    "UserContext",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    # Interfaces
    "IAuthService",
    "IJwtService",
    "IPasswordService",
    "IUserRepository",
    # Errors
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "InvalidTokenError",
    "AuthorizationError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "UserInactiveError",
    "UserNotVerifiedError",
]
