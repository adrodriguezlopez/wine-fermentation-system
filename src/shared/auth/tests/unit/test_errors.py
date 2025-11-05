"""Tests for authentication exceptions."""

import pytest

from src.shared.auth.domain.errors import (
    AuthenticationError,
    AuthorizationError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    UserAlreadyExistsError,
    UserInactiveError,
    UserNotFoundError,
    UserNotVerifiedError,
)


class TestAuthenticationError:
    """Test AuthenticationError base exception."""

    def test_authentication_error_default_message(self):
        """Test AuthenticationError with default message."""
        error = AuthenticationError()
        assert str(error) == "Authentication failed"
        assert error.message == "Authentication failed"

    def test_authentication_error_custom_message(self):
        """Test AuthenticationError with custom message."""
        error = AuthenticationError("Custom auth error")
        assert str(error) == "Custom auth error"
        assert error.message == "Custom auth error"

    def test_authentication_error_inheritance(self):
        """Test that AuthenticationError is an Exception."""
        error = AuthenticationError()
        assert isinstance(error, Exception)


class TestInvalidCredentialsError:
    """Test InvalidCredentialsError exception."""

    def test_invalid_credentials_error_message(self):
        """Test InvalidCredentialsError has correct message."""
        error = InvalidCredentialsError()
        assert str(error) == "Invalid email or password"
        assert error.message == "Invalid email or password"

    def test_invalid_credentials_error_inheritance(self):
        """Test that InvalidCredentialsError inherits from AuthenticationError."""
        error = InvalidCredentialsError()
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, Exception)


class TestTokenExpiredError:
    """Test TokenExpiredError exception."""

    def test_token_expired_error_message(self):
        """Test TokenExpiredError has correct message."""
        error = TokenExpiredError()
        assert str(error) == "Token has expired"
        assert error.message == "Token has expired"

    def test_token_expired_error_inheritance(self):
        """Test that TokenExpiredError inherits from AuthenticationError."""
        error = TokenExpiredError()
        assert isinstance(error, AuthenticationError)


class TestInvalidTokenError:
    """Test InvalidTokenError exception."""

    def test_invalid_token_error_message(self):
        """Test InvalidTokenError has correct message."""
        error = InvalidTokenError()
        assert str(error) == "Invalid or malformed token"
        assert error.message == "Invalid or malformed token"

    def test_invalid_token_error_inheritance(self):
        """Test that InvalidTokenError inherits from AuthenticationError."""
        error = InvalidTokenError()
        assert isinstance(error, AuthenticationError)


class TestAuthorizationError:
    """Test AuthorizationError exception."""

    def test_authorization_error_default_message(self):
        """Test AuthorizationError with default message."""
        error = AuthorizationError()
        assert str(error) == "Insufficient permissions"
        assert error.message == "Insufficient permissions"

    def test_authorization_error_custom_message(self):
        """Test AuthorizationError with custom message."""
        error = AuthorizationError("Admin only")
        assert str(error) == "Admin only"
        assert error.message == "Admin only"

    def test_authorization_error_inheritance(self):
        """Test that AuthorizationError is an Exception."""
        error = AuthorizationError()
        assert isinstance(error, Exception)


class TestUserNotFoundError:
    """Test UserNotFoundError exception."""

    def test_user_not_found_error_with_identifier(self):
        """Test UserNotFoundError with user identifier."""
        error = UserNotFoundError("user@example.com")
        assert "user@example.com" in str(error)
        assert error.identifier == "user@example.com"

    def test_user_not_found_error_inheritance(self):
        """Test that UserNotFoundError is an Exception."""
        error = UserNotFoundError("123")
        assert isinstance(error, Exception)


class TestUserAlreadyExistsError:
    """Test UserAlreadyExistsError exception."""

    def test_user_already_exists_error_with_email(self):
        """Test UserAlreadyExistsError with email field."""
        error = UserAlreadyExistsError("email", "test@example.com")
        assert "email" in str(error)
        assert "test@example.com" in str(error)
        assert error.field == "email"
        assert error.value == "test@example.com"

    def test_user_already_exists_error_with_username(self):
        """Test UserAlreadyExistsError with username field."""
        error = UserAlreadyExistsError("username", "testuser")
        assert "username" in str(error)
        assert "testuser" in str(error)

    def test_user_already_exists_error_inheritance(self):
        """Test that UserAlreadyExistsError is an Exception."""
        error = UserAlreadyExistsError("email", "test@example.com")
        assert isinstance(error, Exception)


class TestUserInactiveError:
    """Test UserInactiveError exception."""

    def test_user_inactive_error_message(self):
        """Test UserInactiveError has correct message."""
        error = UserInactiveError()
        assert str(error) == "User account is inactive"
        assert error.message == "User account is inactive"

    def test_user_inactive_error_inheritance(self):
        """Test that UserInactiveError inherits from AuthenticationError."""
        error = UserInactiveError()
        assert isinstance(error, AuthenticationError)


class TestUserNotVerifiedError:
    """Test UserNotVerifiedError exception."""

    def test_user_not_verified_error_message(self):
        """Test UserNotVerifiedError has correct message."""
        error = UserNotVerifiedError()
        assert str(error) == "User account is not verified"
        assert error.message == "User account is not verified"

    def test_user_not_verified_error_inheritance(self):
        """Test that UserNotVerifiedError inherits from AuthenticationError."""
        error = UserNotVerifiedError()
        assert isinstance(error, AuthenticationError)


class TestExceptionHierarchy:
    """Test exception hierarchy and catching."""

    def test_catch_authentication_errors(self):
        """Test that all authentication-related errors can be caught as AuthenticationError."""
        errors = [
            InvalidCredentialsError(),
            TokenExpiredError(),
            InvalidTokenError(),
            UserInactiveError(),
            UserNotVerifiedError(),
        ]

        for error in errors:
            try:
                raise error
            except AuthenticationError:
                pass  # Successfully caught as AuthenticationError
            except Exception:
                pytest.fail(f"{type(error).__name__} not caught as AuthenticationError")

    def test_authorization_error_separate(self):
        """Test that AuthorizationError is NOT an AuthenticationError."""
        error = AuthorizationError()
        assert not isinstance(error, AuthenticationError)
        assert isinstance(error, Exception)

    def test_user_errors_separate(self):
        """Test that UserNotFoundError and UserAlreadyExistsError are not AuthenticationError."""
        errors = [
            UserNotFoundError("test"),
            UserAlreadyExistsError("email", "test@example.com"),
        ]

        for error in errors:
            assert not isinstance(error, AuthenticationError)
            assert isinstance(error, Exception)
