"""Authentication service interface."""

from typing import Optional, Protocol, runtime_checkable

from ..dtos import (
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    UserCreate,
    UserContext,
    UserResponse,
    UserUpdate,
)
from ..entities.user import User


@runtime_checkable
class IAuthService(Protocol):
    """
    Protocol for authentication and user management operations.
    
    Coordinates password verification, token generation, and user lifecycle.
    Implements business logic for authentication flows.
    """
    
    async def login(self, request: LoginRequest) -> LoginResponse:
        """
        Authenticate user and generate JWT tokens.
        
        Args:
            request: LoginRequest with email and password
            
        Returns:
            LoginResponse with access_token and refresh_token
            
        Raises:
            InvalidCredentialsError: If email/password incorrect
            UserInactiveError: If user account is deactivated
            UserNotVerifiedError: If user account not verified (optional check)
        """
        ...
    
    async def refresh_access_token(self, refresh_token: str) -> LoginResponse:
        """
        Generate new access token using valid refresh token.
        
        Args:
            refresh_token: Valid JWT refresh token
            
        Returns:
            LoginResponse with new access_token and same refresh_token
            
        Raises:
            TokenExpiredError: If refresh token expired
            InvalidTokenError: If token malformed
            UserNotFoundError: If user no longer exists
            UserInactiveError: If user account deactivated since token issued
        """
        ...
    
    async def register_user(
        self,
        user_data: UserCreate,
        created_by: UserContext,
    ) -> UserResponse:
        """
        Create new user account (admin only).
        
        Args:
            user_data: UserCreate with username, email, password, etc.
            created_by: UserContext of admin creating the user
            
        Returns:
            UserResponse with created user data (excludes password_hash)
            
        Raises:
            AuthorizationError: If created_by is not admin
            UserAlreadyExistsError: If email or username already exists
            ValueError: If password doesn't meet strength requirements
        """
        ...
    
    async def verify_token(self, token: str) -> UserContext:
        """
        Validate JWT token and extract user context.
        
        Args:
            token: JWT access token string
            
        Returns:
            UserContext with user_id, winery_id, email, role
            
        Raises:
            TokenExpiredError: If token expired
            InvalidTokenError: If token malformed
            UserNotFoundError: If user no longer exists
            UserInactiveError: If user account deactivated
        """
        ...
    
    async def get_user(self, user_id: int, requester: UserContext) -> UserResponse:
        """
        Get user by ID with authorization check.
        
        Args:
            user_id: User's unique identifier
            requester: UserContext of user making request
            
        Returns:
            UserResponse with user data
            
        Raises:
            AuthorizationError: If requester not admin and user_id != requester.user_id
            UserNotFoundError: If user doesn't exist
        """
        ...
    
    async def update_user(
        self,
        user_id: int,
        user_data: UserUpdate,
        updated_by: UserContext,
    ) -> UserResponse:
        """
        Update user information (admin only, or self for non-role fields).
        
        Args:
            user_id: User's unique identifier
            user_data: UserUpdate with fields to modify
            updated_by: UserContext of user performing update
            
        Returns:
            UserResponse with updated user data
            
        Raises:
            AuthorizationError: If updated_by lacks permission
            UserNotFoundError: If user doesn't exist
            UserAlreadyExistsError: If new email/username conflicts
        """
        ...
    
    async def change_password(
        self,
        user_id: int,
        request: PasswordChangeRequest,
        changed_by: UserContext,
    ) -> bool:
        """
        Change user password (requires old password verification).
        
        Args:
            user_id: User's unique identifier
            request: PasswordChangeRequest with old and new passwords
            changed_by: UserContext of user performing change
            
        Returns:
            True if password changed successfully
            
        Raises:
            AuthorizationError: If changed_by.user_id != user_id and not admin
            UserNotFoundError: If user doesn't exist
            InvalidCredentialsError: If old_password incorrect
            ValueError: If new_password doesn't meet strength requirements
        """
        ...
    
    async def request_password_reset(self, email: str) -> bool:
        """
        Initiate password reset flow (send reset token/email).
        
        Args:
            email: User's email address
            
        Returns:
            True (always, to prevent user enumeration)
            
        Note:
            Implementation should generate reset token and send email
            but always return True even if user doesn't exist
        """
        ...
    
    async def confirm_password_reset(self, token: str, new_password: str) -> bool:
        """
        Complete password reset with valid token.
        
        Args:
            token: Password reset token
            new_password: New password to set
            
        Returns:
            True if password reset successful
            
        Raises:
            InvalidTokenError: If reset token invalid or expired
            ValueError: If new_password doesn't meet strength requirements
        """
        ...
    
    async def deactivate_user(self, user_id: int, by_user: UserContext) -> bool:
        """
        Deactivate user account (admin only, soft delete).
        
        Args:
            user_id: User's unique identifier
            by_user: UserContext of admin performing deactivation
            
        Returns:
            True if user deactivated successfully
            
        Raises:
            AuthorizationError: If by_user is not admin
            UserNotFoundError: If user doesn't exist
        """
        ...
