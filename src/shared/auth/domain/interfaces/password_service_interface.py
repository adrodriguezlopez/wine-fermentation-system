"""Password hashing and verification service interface."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class IPasswordService(Protocol):
    """
    Protocol for password hashing and verification operations.
    
    Implementations should use secure algorithms (bcrypt, argon2, etc.)
    with appropriate cost factors for production security.
    """
    
    def hash_password(self, password: str) -> str:
        """
        Hash a plaintext password using secure algorithm.
        
        Args:
            password: Plaintext password to hash
            
        Returns:
            Hashed password string (includes salt and algorithm metadata)
            
        Raises:
            ValueError: If password is empty or too short
        """
        ...
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify plaintext password against stored hash.
        
        Args:
            password: Plaintext password to verify
            password_hash: Stored hash to compare against
            
        Returns:
            True if password matches hash, False otherwise
        """
        ...
    
    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """
        Validate password meets security requirements.
        
        Args:
            password: Plaintext password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            error_message is empty string if valid
        """
        ...
