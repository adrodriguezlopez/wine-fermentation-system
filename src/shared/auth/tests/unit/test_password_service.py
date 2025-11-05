"""
Tests for PasswordService.

Following TDD - these tests define the expected behavior before implementation.
"""

import pytest
from unittest.mock import Mock

from src.shared.auth.domain.interfaces.password_service_interface import (
    IPasswordService,
)


class TestPasswordService:
    """Test PasswordService implementation."""

    @pytest.fixture
    def password_service(self):
        """Create PasswordService instance for testing."""
        from src.shared.auth.infra.services.password_service import PasswordService
        return PasswordService()

    def test_service_implements_interface(self, password_service):
        """Test that PasswordService implements IPasswordService."""
        assert isinstance(password_service, IPasswordService)

    def test_hash_password_returns_string(self, password_service):
        """Test that hash_password returns a string hash."""
        # Arrange
        plain_password = "MySecureP@ssw0rd"
        
        # Act
        hashed = password_service.hash_password(plain_password)
        
        # Assert
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != plain_password  # Should not be plain text

    def test_hash_password_generates_different_hashes(self, password_service):
        """Test that same password generates different hashes (salt)."""
        # Arrange
        plain_password = "MySecureP@ssw0rd"
        
        # Act
        hash1 = password_service.hash_password(plain_password)
        hash2 = password_service.hash_password(plain_password)
        
        # Assert
        assert hash1 != hash2  # Different salts should produce different hashes

    def test_verify_password_correct_password(self, password_service):
        """Test that verify_password returns True for correct password."""
        # Arrange
        plain_password = "MySecureP@ssw0rd"
        hashed = password_service.hash_password(plain_password)
        
        # Act
        result = password_service.verify_password(plain_password, hashed)
        
        # Assert
        assert result is True

    def test_verify_password_incorrect_password(self, password_service):
        """Test that verify_password returns False for incorrect password."""
        # Arrange
        plain_password = "MySecureP@ssw0rd"
        wrong_password = "WrongPassword123"
        hashed = password_service.hash_password(plain_password)
        
        # Act
        result = password_service.verify_password(wrong_password, hashed)
        
        # Assert
        assert result is False

    def test_verify_password_invalid_hash(self, password_service):
        """Test that verify_password returns False for invalid hash."""
        # Arrange
        plain_password = "MySecureP@ssw0rd"
        invalid_hash = "not_a_valid_bcrypt_hash"
        
        # Act
        result = password_service.verify_password(plain_password, invalid_hash)
        
        # Assert
        assert result is False

    def test_validate_password_strength_valid_password(self, password_service):
        """Test that validate_password_strength returns True for strong password."""
        # Arrange - Password with 8+ chars, upper, lower, number
        valid_passwords = [
            "MyPassword123",
            "SecureP@ss1",
            "Abcdefgh1",
            "Test1234Pass",
        ]
        
        # Act & Assert
        for password in valid_passwords:
            assert password_service.validate_password_strength(password) is True

    def test_validate_password_strength_too_short(self, password_service):
        """Test that validate_password_strength rejects short passwords."""
        # Arrange - Password with less than 8 characters
        short_password = "Pass1"
        
        # Act
        result = password_service.validate_password_strength(short_password)
        
        # Assert
        assert result is False

    def test_validate_password_strength_no_uppercase(self, password_service):
        """Test that validate_password_strength rejects passwords without uppercase."""
        # Arrange - Password with no uppercase letter
        no_upper = "password123"
        
        # Act
        result = password_service.validate_password_strength(no_upper)
        
        # Assert
        assert result is False

    def test_validate_password_strength_no_lowercase(self, password_service):
        """Test that validate_password_strength rejects passwords without lowercase."""
        # Arrange - Password with no lowercase letter
        no_lower = "PASSWORD123"
        
        # Act
        result = password_service.validate_password_strength(no_lower)
        
        # Assert
        assert result is False

    def test_validate_password_strength_no_digit(self, password_service):
        """Test that validate_password_strength rejects passwords without digit."""
        # Arrange - Password with no digit
        no_digit = "PasswordABC"
        
        # Act
        result = password_service.validate_password_strength(no_digit)
        
        # Assert
        assert result is False

    def test_validate_password_strength_empty_string(self, password_service):
        """Test that validate_password_strength rejects empty password."""
        # Arrange
        empty_password = ""
        
        # Act
        result = password_service.validate_password_strength(empty_password)
        
        # Assert
        assert result is False
