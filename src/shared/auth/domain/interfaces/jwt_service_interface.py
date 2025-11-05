"""JWT token encoding and decoding service interface."""

from typing import Dict, Protocol, runtime_checkable

from ..dtos import UserContext


@runtime_checkable
class IJwtService(Protocol):
    """
    Protocol for JWT token operations.
    
    Implementations must handle token generation, validation, and claims extraction
    using HS256 algorithm with configurable expiry times.
    """
    
    def encode_access_token(self, user_id: int, winery_id: int, email: str, role: str) -> str:
        """
        Generate JWT access token for authenticated user.
        
        Args:
            user_id: User's unique identifier
            winery_id: User's winery identifier (for multi-tenancy)
            email: User's email address
            role: User's role (admin, winemaker, operator, viewer)
            
        Returns:
            Signed JWT access token (expires in 15 minutes)
        """
        ...
    
    def encode_refresh_token(self, user_id: int) -> str:
        """
        Generate JWT refresh token for token renewal.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Signed JWT refresh token (expires in 7 days)
        """
        ...
    
    def decode_token(self, token: str) -> Dict[str, any]:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token string to decode
            
        Returns:
            Dictionary of token claims (user_id, winery_id, email, role, exp, iat, jti)
            
        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is malformed or signature invalid
        """
        ...
    
    def extract_user_context(self, token: str) -> UserContext:
        """
        Extract UserContext from valid access token.
        
        Args:
            token: JWT access token string
            
        Returns:
            UserContext with user_id, winery_id, email, role
            
        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is malformed or missing required claims
        """
        ...
