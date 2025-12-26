"""Custom exceptions for authentication and authorization.

ADR-026: This module now uses the shared error hierarchy for consistency.
Legacy error names are maintained as aliases for backward compatibility.
"""

# Import from shared ADR-026 error hierarchy
# Use try/except to handle both contexts: when running from shared/ and when imported from modules
try:
    from domain.errors import (
        AuthError,
        InvalidCredentials,
        TokenExpired,
        InvalidToken,
        UserNotFound,
        InsufficientPermissions,
    )
except ModuleNotFoundError:
    from shared.domain.errors import (
        AuthError,
        InvalidCredentials,
        TokenExpired,
        InvalidToken,
        UserNotFound,
        InsufficientPermissions,
    )

# Backward compatibility wrappers (DEPRECATED - use shared.domain.errors directly)
# These maintain the old API while using ADR-026 errors internally

class AuthenticationError(AuthError):
    """Legacy wrapper for AuthError with optional message."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class InvalidCredentialsError(AuthenticationError):
    """Legacy wrapper that maintains exact same API and inheritance."""
    def __init__(self):
        AuthError.__init__(self, "Invalid email or password")
        self.error_code = "INVALID_CREDENTIALS"


class TokenExpiredError(AuthenticationError):
    """Legacy wrapper that maintains exact same API and inheritance."""
    def __init__(self):
        AuthError.__init__(self, "Token has expired")
        self.error_code = "TOKEN_EXPIRED"
        self.http_status = 401


class InvalidTokenError(AuthenticationError):
    """Legacy wrapper that maintains exact same API and inheritance."""
    def __init__(self, message: str = "Invalid or malformed token"):
        AuthError.__init__(self, message)
        self.error_code = "INVALID_TOKEN"
        self.http_status = 401


class UserInactiveError(AuthenticationError):
    """Legacy wrapper for inactive user error."""
    def __init__(self):
        AuthError.__init__(self, "User account is inactive")
        self.error_code = "USER_INACTIVE"
        self.http_status = 403


class UserNotVerifiedError(AuthenticationError):
    """Legacy wrapper for unverified user error."""
    def __init__(self):
        AuthError.__init__(self, "User account is not verified")
        self.error_code = "USER_NOT_VERIFIED"
        self.http_status = 403


class AuthorizationError(AuthError):
    """Legacy wrapper for InsufficientPermissions with optional message."""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message)
        self.error_code = "INSUFFICIENT_PERMISSIONS"
        self.http_status = 403


class UserNotFoundError(AuthError):
    """Legacy wrapper that accepts identifier as before."""
    def __init__(self, identifier: str):
        super().__init__(f"User not found: {identifier}", identifier=identifier)
        self.error_code = "USER_NOT_FOUND"
        self.http_status = 404
        self.identifier = identifier

# These don't have direct equivalents in ADR-026, so we keep them as AuthError subclasses
class UserAlreadyExistsError(AuthError):
    """Raised when attempting to create user with existing email/username."""
    http_status = 409
    error_code = "USER_ALREADY_EXISTS"
    
    def __init__(self, field: str, value: str):
        super().__init__(
            f"User with {field} '{value}' already exists",
            field=field,
            value=value
        )
        self.field = field
        self.value = value


class UserInactiveError(AuthenticationError):
    """Raised when user account is deactivated (inherits from AuthenticationError)."""
    def __init__(self):
        AuthError.__init__(self, "User account is inactive")
        self.http_status = 403
        self.error_code = "USER_INACTIVE"


class UserNotVerifiedError(AuthenticationError):
    """Raised when user account is not verified (inherits from AuthenticationError)."""
    def __init__(self):
        AuthError.__init__(self, "User account is not verified")
        self.http_status = 403
        self.error_code = "USER_NOT_VERIFIED"
