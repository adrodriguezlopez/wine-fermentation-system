"""
Tests for JwtService.

Following TDD - these tests define the expected behavior before implementation.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums import UserRole
from src.shared.auth.domain.errors import TokenExpiredError, InvalidTokenError
from src.shared.auth.domain.interfaces.jwt_service_interface import IJwtService


class TestJwtService:
    """Test JwtService implementation."""

    @pytest.fixture
    def jwt_service(self):
        """Create JwtService instance for testing."""
        from src.shared.auth.infra.services.jwt_service import JwtService
        
        # Use test secret key
        secret_key = "test_secret_key_for_jwt_tokens_min_32_chars"
        return JwtService(secret_key=secret_key)

    @pytest.fixture
    def sample_user_context(self):
        """Create sample UserContext for testing."""
        return UserContext(
            user_id=1,
            winery_id=1,
            email="test@example.com",
            role=UserRole.WINEMAKER,
        )

    def test_service_implements_interface(self, jwt_service):
        """Test that JwtService implements IJwtService."""
        assert isinstance(jwt_service, IJwtService)

    def test_encode_access_token_returns_string(self, jwt_service, sample_user_context):
        """Test that encode_access_token returns a JWT string."""
        # Act
        token = jwt_service.encode_access_token(sample_user_context)
        
        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts separated by dots

    def test_encode_refresh_token_returns_string(self, jwt_service):
        """Test that encode_refresh_token returns a JWT string."""
        # Act
        token = jwt_service.encode_refresh_token(user_id=1)
        
        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts separated by dots

    def test_decode_token_valid_token(self, jwt_service, sample_user_context):
        """Test that decode_token returns payload for valid token."""
        # Arrange
        token = jwt_service.encode_access_token(sample_user_context)
        
        # Act
        payload = jwt_service.decode_token(token)
        
        # Assert
        assert isinstance(payload, dict)
        assert payload["sub"] == str(sample_user_context.user_id)
        assert payload["email"] == sample_user_context.email
        assert payload["winery_id"] == sample_user_context.winery_id
        assert payload["role"] == sample_user_context.role.value

    def test_decode_token_expired_token(self, jwt_service, sample_user_context):
        """Test that decode_token raises TokenExpiredError for expired token."""
        # Arrange - Create token with past expiration
        with patch('src.shared.auth.infra.services.jwt_service.datetime') as mock_datetime:
            # Set time to past for encoding
            past_time = datetime.now(timezone.utc) - timedelta(minutes=30)
            mock_datetime.now.return_value = past_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            token = jwt_service.encode_access_token(sample_user_context)
        
        # Act & Assert
        with pytest.raises(TokenExpiredError):
            jwt_service.decode_token(token)

    def test_decode_token_invalid_signature(self, jwt_service, sample_user_context):
        """Test that decode_token raises InvalidTokenError for invalid signature."""
        # Arrange - Create token with one secret, decode with different secret
        from src.shared.auth.infra.services.jwt_service import JwtService
        other_service = JwtService(secret_key="different_secret_key_123456789012")
        token = other_service.encode_access_token(sample_user_context)
        
        # Act & Assert
        with pytest.raises(InvalidTokenError):
            jwt_service.decode_token(token)

    def test_decode_token_malformed_token(self, jwt_service):
        """Test that decode_token raises InvalidTokenError for malformed token."""
        # Arrange
        malformed_token = "not.a.valid.jwt.token"
        
        # Act & Assert
        with pytest.raises(InvalidTokenError):
            jwt_service.decode_token(malformed_token)

    def test_extract_user_context_valid_token(self, jwt_service, sample_user_context):
        """Test that extract_user_context returns UserContext for valid token."""
        # Arrange
        token = jwt_service.encode_access_token(sample_user_context)
        
        # Act
        user_context = jwt_service.extract_user_context(token)
        
        # Assert
        assert isinstance(user_context, UserContext)
        assert user_context.user_id == sample_user_context.user_id
        assert user_context.email == sample_user_context.email
        assert user_context.winery_id == sample_user_context.winery_id
        assert user_context.role == sample_user_context.role

    def test_extract_user_context_expired_token(self, jwt_service, sample_user_context):
        """Test that extract_user_context raises TokenExpiredError."""
        # Arrange - Create expired token
        with patch('src.shared.auth.infra.services.jwt_service.datetime') as mock_datetime:
            past_time = datetime.now(timezone.utc) - timedelta(minutes=30)
            mock_datetime.now.return_value = past_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            token = jwt_service.encode_access_token(sample_user_context)
        
        # Act & Assert
        with pytest.raises(TokenExpiredError):
            jwt_service.extract_user_context(token)

    def test_extract_user_context_missing_claims(self, jwt_service):
        """Test that extract_user_context raises InvalidTokenError for missing claims."""
        # Arrange - Create token with minimal payload (missing required fields)
        import jwt
        secret = "test_secret_key_for_jwt_tokens_min_32_chars"
        token = jwt.encode({"sub": "1"}, secret, algorithm="HS256")
        
        # Act & Assert
        with pytest.raises(InvalidTokenError):
            jwt_service.extract_user_context(token)

    def test_access_token_has_short_expiration(self, jwt_service, sample_user_context):
        """Test that access tokens have short expiration (15 minutes)."""
        # Arrange & Act
        token = jwt_service.encode_access_token(sample_user_context)
        payload = jwt_service.decode_token(token)
        
        # Assert - Check expiration time is approximately 15 minutes from now
        exp_timestamp = payload["exp"]
        exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = exp_time - now
        
        # Should be between 14 and 16 minutes (accounting for test execution time)
        assert 14 * 60 < time_diff.total_seconds() < 16 * 60

    def test_refresh_token_has_long_expiration(self, jwt_service):
        """Test that refresh tokens have long expiration (7 days)."""
        # Arrange & Act
        token = jwt_service.encode_refresh_token(user_id=1)
        payload = jwt_service.decode_token(token)
        
        # Assert - Check expiration time is approximately 7 days from now
        exp_timestamp = payload["exp"]
        exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = exp_time - now
        
        # Should be between 6.9 and 7.1 days
        assert 6.9 * 24 * 60 * 60 < time_diff.total_seconds() < 7.1 * 24 * 60 * 60

    def test_tokens_include_issued_at(self, jwt_service, sample_user_context):
        """Test that tokens include 'iat' (issued at) claim."""
        # Arrange & Act
        token = jwt_service.encode_access_token(sample_user_context)
        payload = jwt_service.decode_token(token)
        
        # Assert
        assert "iat" in payload
        iat_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Issued at should be very recent (within 5 seconds)
        time_diff = abs((now - iat_time).total_seconds())
        assert time_diff < 5
