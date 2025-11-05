"""
JWT service implementation using PyJWT.

This service handles JWT token encoding, decoding, and user context extraction.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict
import jwt

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums import UserRole
from src.shared.auth.domain.errors import TokenExpiredError, InvalidTokenError
from src.shared.auth.domain.interfaces.jwt_service_interface import IJwtService


class JwtService(IJwtService):
    """
    JWT service implementation using PyJWT library.
    
    Provides token encoding/decoding with configurable expiration times
    and user context extraction from JWT tokens.
    
    Token types:
    - Access tokens: Short-lived (15 minutes) for API requests
    - Refresh tokens: Long-lived (7 days) for obtaining new access tokens
    """

    # Token expiration times
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT service with secret key and algorithm.
        
        Args:
            secret_key: Secret key for signing tokens (min 32 characters recommended)
            algorithm: JWT algorithm (default: HS256)
        """
        self._secret_key = secret_key
        self._algorithm = algorithm

    def encode_access_token(self, user_context: UserContext) -> str:
        """
        Encode user context into a short-lived JWT access token.
        
        Args:
            user_context: User context to encode
            
        Returns:
            JWT token string with 15-minute expiration
            
        Token payload includes:
        - sub: User ID (subject)
        - email: Email address
        - winery_id: Winery identifier
        - role: User role
        - iat: Issued at timestamp
        - exp: Expiration timestamp
        """
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": str(user_context.user_id),
            "email": user_context.email,
            "winery_id": user_context.winery_id,
            "role": user_context.role.value,
            "iat": now,
            "exp": expires,
        }
        
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def encode_refresh_token(self, user_id: int) -> str:
        """
        Encode user ID into a long-lived JWT refresh token.
        
        Args:
            user_id: User identifier
            
        Returns:
            JWT token string with 7-day expiration
            
        Token payload includes:
        - sub: User ID (subject)
        - type: Token type ("refresh")
        - iat: Issued at timestamp
        - exp: Expiration timestamp
        """
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expires,
        }
        
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_token(self, token: str) -> Dict:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string to decode
            
        Returns:
            Decoded token payload as dictionary
            
        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token signature is invalid or malformed
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidTokenError):
            raise InvalidTokenError()

    def extract_user_context(self, token: str) -> UserContext:
        """
        Extract user context from a JWT access token.
        
        Args:
            token: JWT access token string
            
        Returns:
            UserContext extracted from token payload
            
        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is invalid or missing required claims
        """
        try:
            payload = self.decode_token(token)
            
            # Extract and validate required claims
            user_id = int(payload["sub"])
            email = payload["email"]
            winery_id = payload["winery_id"]
            role_value = payload["role"]
            
            # Convert role string to UserRole enum
            role = UserRole(role_value)
            
            return UserContext(
                user_id=user_id,
                email=email,
                winery_id=winery_id,
                role=role,
            )
        except KeyError:
            raise InvalidTokenError()
        except (ValueError, TypeError):
            raise InvalidTokenError()
