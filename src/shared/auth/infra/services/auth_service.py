"""
AuthService implementation.

Core authentication service that orchestrates user authentication,
registration, token management, and user operations.
"""

from typing import Optional

from src.shared.auth.domain.dtos import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
    PasswordChangeRequest,
    UserContext,
)
from src.shared.auth.domain.entities import User
from src.shared.auth.domain.enums import UserRole
from src.shared.auth.domain.errors import (
    InvalidCredentialsError,
    UserNotFoundError,
    UserAlreadyExistsError,
    UserInactiveError,
    UserNotVerifiedError,
)
from src.shared.auth.domain.interfaces import (
    IAuthService,
    IUserRepository,
    IPasswordService,
    IJwtService,
)


class AuthService(IAuthService):
    """
    Authentication service implementation.
    
    Orchestrates authentication flows, user management, and token operations
    by coordinating between UserRepository, PasswordService, and JwtService.
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        password_service: IPasswordService,
        jwt_service: IJwtService,
    ):
        """
        Initialize AuthService with required dependencies.
        
        Args:
            user_repository: Repository for user data operations
            password_service: Service for password hashing and validation
            jwt_service: Service for JWT token operations
        """
        self._user_repository = user_repository
        self._password_service = password_service
        self._jwt_service = jwt_service

    async def login(self, request: LoginRequest) -> LoginResponse:
        """
        Authenticate user and generate tokens.
        
        Args:
            request: Login credentials (email and password)
            
        Returns:
            LoginResponse with access and refresh tokens
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            UserInactiveError: If user account is inactive
            UserNotVerifiedError: If user account is not verified
        """
        # Get user by email
        user = await self._user_repository.get_by_email(request.email)
        if not user:
            raise InvalidCredentialsError()

        # Verify password
        if not self._password_service.verify_password(request.password, user.password_hash):
            raise InvalidCredentialsError()

        # Check user status
        if not user.is_active:
            raise UserInactiveError()
        if not user.is_verified:
            raise UserNotVerifiedError()

        # Create user context for token
        user_context = UserContext(
            user_id=user.id,
            winery_id=user.winery_id,
            email=user.email,
            role=UserRole(user.role) if isinstance(user.role, str) else user.role,
        )

        # Generate tokens
        access_token = self._jwt_service.encode_access_token(user_context)
        refresh_token = self._jwt_service.encode_refresh_token(user.id)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token string
            
        Raises:
            InvalidTokenError: If refresh token is invalid
            UserNotFoundError: If user no longer exists
        """
        # Decode refresh token to extract user_id
        payload = self._jwt_service.decode_token(refresh_token)
        user_id = int(payload.get("sub"))
        
        if not user_id:
            from src.shared.auth.domain.errors import InvalidTokenError
            raise InvalidTokenError()

        # Verify user still exists and get current state
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Create fresh user context from current user state
        user_context = UserContext(
            user_id=user.id,
            winery_id=user.winery_id,
            email=user.email,
            role=UserRole(user.role) if isinstance(user.role, str) else user.role,
        )

        # Generate new access token with current user context
        return self._jwt_service.encode_access_token(user_context)

    async def register_user(self, user_create: UserCreate) -> UserResponse:
        """
        Register a new user.
        
        Args:
            user_create: User registration data
            
        Returns:
            UserResponse with created user details
            
        Raises:
            UserAlreadyExistsError: If email or username already exists
            ValueError: If password doesn't meet strength requirements
        """
        # Check if email already exists
        if await self._user_repository.exists_by_email(user_create.email):
            raise UserAlreadyExistsError(field="email", value=user_create.email)

        # Check if username already exists
        if await self._user_repository.exists_by_username(user_create.username):
            raise UserAlreadyExistsError(field="username", value=user_create.username)

        # Validate password strength
        if not self._password_service.validate_password_strength(user_create.password):
            raise ValueError(
                "Password must be at least 8 characters and contain "
                "uppercase, lowercase, and digit"
            )

        # Hash password
        password_hash = self._password_service.hash_password(user_create.password)

        # Create user entity from DTO
        from src.shared.auth.domain.entities.user import User
        from datetime import datetime
        
        user = User(
            username=user_create.username,
            email=user_create.email,
            password_hash=password_hash,
            full_name=user_create.full_name,
            winery_id=user_create.winery_id,
            role=user_create.role.value if user_create.role else "viewer",
            is_active=True,
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Persist to database
        created_user = await self._user_repository.create(user)

        # Return user response
        return UserResponse.from_entity(created_user)

    async def verify_token(self, token: str) -> UserContext:
        """
        Verify token and extract user context.
        
        Args:
            token: JWT token to verify
            
        Returns:
            UserContext extracted from token
            
        Raises:
            InvalidTokenError: If token is invalid
            TokenExpiredError: If token has expired
        """
        return self._jwt_service.extract_user_context(token)

    async def get_user(self, user_id: int) -> UserResponse:
        """
        Get user by ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserResponse with user details
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        return UserResponse.from_entity(user)

    async def update_user(self, user_id: int, user_update: UserUpdate) -> UserResponse:
        """
        Update user information.
        
        Args:
            user_id: User identifier
            user_update: Fields to update
            
        Returns:
            UserResponse with updated user details
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        # Verify user exists
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Apply updates to user entity
        if user_update.username is not None:
            user.username = user_update.username
        if user_update.email is not None:
            user.email = user_update.email
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.role is not None:
            user.role = user_update.role
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
        if user_update.is_verified is not None:
            user.is_verified = user_update.is_verified

        # Update user
        updated_user = await self._user_repository.update(user)

        return UserResponse.from_entity(updated_user)

    async def change_password(
        self, user_id: int, password_change: PasswordChangeRequest
    ) -> None:
        """
        Change user password.
        
        Args:
            user_id: User identifier
            password_change: Old and new password
            
        Raises:
            UserNotFoundError: If user doesn't exist
            InvalidCredentialsError: If old password is incorrect
            ValueError: If new password doesn't meet strength requirements
        """
        # Get user
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Verify old password
        if not self._password_service.verify_password(
            password_change.old_password, user.password_hash
        ):
            raise InvalidCredentialsError()

        # Validate new password strength
        if not self._password_service.validate_password_strength(
            password_change.new_password
        ):
            raise ValueError(
                "Password must be at least 8 characters and contain "
                "uppercase, lowercase, and digit"
            )

        # Hash new password
        new_password_hash = self._password_service.hash_password(
            password_change.new_password
        )

        # Update user with new password
        user.password_hash = new_password_hash
        await self._user_repository.update(user)

    async def request_password_reset(self, email: str) -> str:
        """
        Generate password reset token.
        
        Args:
            email: User email address
            
        Returns:
            Password reset token
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        # Note: This is a placeholder for Phase 6 API implementation
        # Full implementation would generate a special reset token
        # and potentially send an email
        raise NotImplementedError("Password reset will be implemented in Phase 6")

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        """
        Reset password using reset token.
        
        Args:
            token: Password reset token
            new_password: New password
            
        Raises:
            InvalidTokenError: If reset token is invalid
            ValueError: If new password doesn't meet strength requirements
        """
        # Note: This is a placeholder for Phase 6 API implementation
        raise NotImplementedError("Password reset will be implemented in Phase 6")

    async def deactivate_user(self, user_id: int) -> None:
        """
        Deactivate user account.
        
        Args:
            user_id: User identifier
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        # Get user
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)

        # Deactivate user
        user.is_active = False
        await self._user_repository.update(user)
