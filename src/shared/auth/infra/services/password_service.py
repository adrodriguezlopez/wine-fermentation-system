"""
Password service implementation using bcrypt.

This service handles secure password hashing, verification, and strength validation.
"""

import re
import bcrypt


from src.shared.auth.domain.interfaces.password_service_interface import (
    IPasswordService,
)


class PasswordService(IPasswordService):
    """
    Password service implementation using bcrypt hashing.
    
    Provides secure password hashing with automatic salting,
    password verification, and password strength validation.
    
    Uses bcrypt with 12 rounds (industry standard for security vs performance).
    """

    def __init__(self):
        """Initialize password service."""
        self._rounds = 12  # Bcrypt rounds (2^12 = 4096 iterations)

    def hash_password(self, password: str) -> str:
        """
        Hash a plain-text password using bcrypt.
        
        Args:
            password: Plain-text password to hash
            
        Returns:
            Bcrypt hash string with embedded salt
            
        Note:
            Each call generates a new salt, so the same password
            will produce different hashes (this is expected behavior).
            
        Raises:
            ValueError: If password is empty or exceeds bcrypt's 72-byte limit
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Convert to bytes (bcrypt requires bytes)
        password_bytes = password.encode('utf-8')
        
        # Bcrypt has a 72-byte limit
        if len(password_bytes) > 72:
            raise ValueError("Password too long (max 72 bytes when UTF-8 encoded)")
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=self._rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain-text password against a bcrypt hash.
        
        Args:
            plain_password: Plain-text password to verify
            hashed_password: Bcrypt hash to compare against
            
        Returns:
            True if password matches hash, False otherwise
            
        Note:
            Returns False for invalid hash formats instead of raising exceptions.
        """
        try:
            password_bytes = plain_password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except (ValueError, TypeError, AttributeError):
            # Invalid hash format or other errors - treat as verification failure
            return False

    def validate_password_strength(self, password: str) -> bool:
        """
        Validate password meets minimum security requirements.
        
        Requirements:
        - At least 8 characters long
        - Contains at least one uppercase letter (A-Z)
        - Contains at least one lowercase letter (a-z)
        - Contains at least one digit (0-9)
        
        Args:
            password: Plain-text password to validate
            
        Returns:
            True if password meets all requirements, False otherwise
        """
        if not password or len(password) < 8:
            return False
        
        # Check for at least one uppercase letter
        if not re.search(r"[A-Z]", password):
            return False
        
        # Check for at least one lowercase letter
        if not re.search(r"[a-z]", password):
            return False
        
        # Check for at least one digit
        if not re.search(r"\d", password):
            return False
        
        return True
