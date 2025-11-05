"""Custom exceptions for authentication and authorization."""


class AuthenticationError(Exception):
    """Base exception for authentication failures."""
    
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""
    
    def __init__(self):
        super().__init__("Invalid email or password")


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""
    
    def __init__(self):
        super().__init__("Token has expired")


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is malformed or invalid."""
    
    def __init__(self):
        super().__init__("Invalid or malformed token")


class AuthorizationError(Exception):
    """Raised when user lacks permission for an operation."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        self.message = message
        super().__init__(self.message)


class UserNotFoundError(Exception):
    """Raised when user does not exist."""
    
    def __init__(self, identifier: str):
        self.identifier = identifier
        message = f"User not found: {identifier}"
        super().__init__(message)


class UserAlreadyExistsError(Exception):
    """Raised when attempting to create user with existing email/username."""
    
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        message = f"User with {field} '{value}' already exists"
        super().__init__(message)


class UserInactiveError(AuthenticationError):
    """Raised when user account is deactivated."""
    
    def __init__(self):
        super().__init__("User account is inactive")


class UserNotVerifiedError(AuthenticationError):
    """Raised when user account is not verified."""
    
    def __init__(self):
        super().__init__("User account is not verified")
