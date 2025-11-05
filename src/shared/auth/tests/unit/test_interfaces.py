"""Tests for authentication service and repository interfaces."""

import inspect

import pytest

from src.shared.auth.domain.interfaces import (
    IAuthService,
    IJwtService,
    IPasswordService,
    IUserRepository,
)


class TestIUserRepository:
    """Test IUserRepository interface definition."""

    def test_interface_is_protocol(self):
        """Test that IUserRepository is a Protocol."""
        # Protocols are special classes, check for runtime_checkable or _is_protocol
        assert hasattr(IUserRepository, "__protocol_attrs__") or \
               IUserRepository.__class__.__name__ == "ProtocolMeta" or \
               "_is_protocol" in dir(IUserRepository)

    def test_interface_has_create_method(self):
        """Test that interface defines create method."""
        assert hasattr(IUserRepository, "create")
        sig = inspect.signature(IUserRepository.create)
        # Should be async
        assert inspect.iscoroutinefunction(IUserRepository.create)

    def test_interface_has_get_by_id_method(self):
        """Test that interface defines get_by_id method."""
        assert hasattr(IUserRepository, "get_by_id")
        assert inspect.iscoroutinefunction(IUserRepository.get_by_id)

    def test_interface_has_get_by_email_method(self):
        """Test that interface defines get_by_email method."""
        assert hasattr(IUserRepository, "get_by_email")
        assert inspect.iscoroutinefunction(IUserRepository.get_by_email)

    def test_interface_has_get_by_username_method(self):
        """Test that interface defines get_by_username method."""
        assert hasattr(IUserRepository, "get_by_username")
        assert inspect.iscoroutinefunction(IUserRepository.get_by_username)

    def test_interface_has_update_method(self):
        """Test that interface defines update method."""
        assert hasattr(IUserRepository, "update")
        assert inspect.iscoroutinefunction(IUserRepository.update)

    def test_interface_has_delete_method(self):
        """Test that interface defines delete method."""
        assert hasattr(IUserRepository, "delete")
        assert inspect.iscoroutinefunction(IUserRepository.delete)

    def test_interface_has_exists_by_email_method(self):
        """Test that interface defines exists_by_email method."""
        assert hasattr(IUserRepository, "exists_by_email")
        assert inspect.iscoroutinefunction(IUserRepository.exists_by_email)

    def test_interface_has_exists_by_username_method(self):
        """Test that interface defines exists_by_username method."""
        assert hasattr(IUserRepository, "exists_by_username")
        assert inspect.iscoroutinefunction(IUserRepository.exists_by_username)


class TestIPasswordService:
    """Test IPasswordService interface definition."""

    def test_interface_is_protocol(self):
        """Test that IPasswordService is a Protocol."""
        assert hasattr(IPasswordService, "__protocol_attrs__") or \
               IPasswordService.__class__.__name__ == "ProtocolMeta" or \
               "_is_protocol" in dir(IPasswordService)

    def test_interface_has_hash_password_method(self):
        """Test that interface defines hash_password method."""
        assert hasattr(IPasswordService, "hash_password")
        # Should be sync
        assert not inspect.iscoroutinefunction(IPasswordService.hash_password)

    def test_interface_has_verify_password_method(self):
        """Test that interface defines verify_password method."""
        assert hasattr(IPasswordService, "verify_password")
        assert not inspect.iscoroutinefunction(IPasswordService.verify_password)

    def test_interface_has_validate_password_strength_method(self):
        """Test that interface defines validate_password_strength method."""
        assert hasattr(IPasswordService, "validate_password_strength")
        assert not inspect.iscoroutinefunction(IPasswordService.validate_password_strength)


class TestIJwtService:
    """Test IJwtService interface definition."""

    def test_interface_is_protocol(self):
        """Test that IJwtService is a Protocol."""
        assert hasattr(IJwtService, "__protocol_attrs__") or \
               IJwtService.__class__.__name__ == "ProtocolMeta" or \
               "_is_protocol" in dir(IJwtService)

    def test_interface_has_encode_access_token_method(self):
        """Test that interface defines encode_access_token method."""
        assert hasattr(IJwtService, "encode_access_token")
        assert not inspect.iscoroutinefunction(IJwtService.encode_access_token)

    def test_interface_has_encode_refresh_token_method(self):
        """Test that interface defines encode_refresh_token method."""
        assert hasattr(IJwtService, "encode_refresh_token")
        assert not inspect.iscoroutinefunction(IJwtService.encode_refresh_token)

    def test_interface_has_decode_token_method(self):
        """Test that interface defines decode_token method."""
        assert hasattr(IJwtService, "decode_token")
        assert not inspect.iscoroutinefunction(IJwtService.decode_token)

    def test_interface_has_extract_user_context_method(self):
        """Test that interface defines extract_user_context method."""
        assert hasattr(IJwtService, "extract_user_context")
        assert not inspect.iscoroutinefunction(IJwtService.extract_user_context)


class TestIAuthService:
    """Test IAuthService interface definition."""

    def test_interface_is_protocol(self):
        """Test that IAuthService is a Protocol."""
        assert hasattr(IAuthService, "__protocol_attrs__") or \
               IAuthService.__class__.__name__ == "ProtocolMeta" or \
               "_is_protocol" in dir(IAuthService)

    def test_interface_has_login_method(self):
        """Test that interface defines login method."""
        assert hasattr(IAuthService, "login")
        assert inspect.iscoroutinefunction(IAuthService.login)

    def test_interface_has_refresh_access_token_method(self):
        """Test that interface defines refresh_access_token method."""
        assert hasattr(IAuthService, "refresh_access_token")
        assert inspect.iscoroutinefunction(IAuthService.refresh_access_token)

    def test_interface_has_register_user_method(self):
        """Test that interface defines register_user method."""
        assert hasattr(IAuthService, "register_user")
        assert inspect.iscoroutinefunction(IAuthService.register_user)

    def test_interface_has_verify_token_method(self):
        """Test that interface defines verify_token method."""
        assert hasattr(IAuthService, "verify_token")
        assert inspect.iscoroutinefunction(IAuthService.verify_token)

    def test_interface_has_get_user_method(self):
        """Test that interface defines get_user method."""
        assert hasattr(IAuthService, "get_user")
        assert inspect.iscoroutinefunction(IAuthService.get_user)

    def test_interface_has_update_user_method(self):
        """Test that interface defines update_user method."""
        assert hasattr(IAuthService, "update_user")
        assert inspect.iscoroutinefunction(IAuthService.update_user)

    def test_interface_has_change_password_method(self):
        """Test that interface defines change_password method."""
        assert hasattr(IAuthService, "change_password")
        assert inspect.iscoroutinefunction(IAuthService.change_password)

    def test_interface_has_request_password_reset_method(self):
        """Test that interface defines request_password_reset method."""
        assert hasattr(IAuthService, "request_password_reset")
        assert inspect.iscoroutinefunction(IAuthService.request_password_reset)

    def test_interface_has_confirm_password_reset_method(self):
        """Test that interface defines confirm_password_reset method."""
        assert hasattr(IAuthService, "confirm_password_reset")
        assert inspect.iscoroutinefunction(IAuthService.confirm_password_reset)

    def test_interface_has_deactivate_user_method(self):
        """Test that interface defines deactivate_user method."""
        assert hasattr(IAuthService, "deactivate_user")
        assert inspect.iscoroutinefunction(IAuthService.deactivate_user)
