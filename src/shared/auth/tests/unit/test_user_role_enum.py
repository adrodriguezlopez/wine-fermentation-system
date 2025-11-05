"""Tests for UserRole enum."""

import pytest

from src.shared.auth.domain.enums import UserRole


class TestUserRoleEnum:
    """Test UserRole enum values and behavior."""

    def test_enum_values(self):
        """Test that all expected role values exist."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.WINEMAKER.value == "winemaker"
        assert UserRole.OPERATOR.value == "operator"
        assert UserRole.VIEWER.value == "viewer"

    def test_enum_is_string(self):
        """Test that UserRole inherits from str."""
        assert isinstance(UserRole.ADMIN, str)
        assert isinstance(UserRole.WINEMAKER, str)

    def test_default_role(self):
        """Test that default() returns VIEWER role."""
        assert UserRole.default() == UserRole.VIEWER

    def test_can_manage_users_admin_only(self):
        """Test that only ADMIN can manage users."""
        assert UserRole.ADMIN.can_manage_users is True
        assert UserRole.WINEMAKER.can_manage_users is False
        assert UserRole.OPERATOR.can_manage_users is False
        assert UserRole.VIEWER.can_manage_users is False

    def test_can_write_fermentations(self):
        """Test that ADMIN and WINEMAKER can write fermentations."""
        assert UserRole.ADMIN.can_write_fermentations is True
        assert UserRole.WINEMAKER.can_write_fermentations is True
        assert UserRole.OPERATOR.can_write_fermentations is False
        assert UserRole.VIEWER.can_write_fermentations is False

    def test_can_write_samples(self):
        """Test that ADMIN, WINEMAKER, and OPERATOR can write samples."""
        assert UserRole.ADMIN.can_write_samples is True
        assert UserRole.WINEMAKER.can_write_samples is True
        assert UserRole.OPERATOR.can_write_samples is True
        assert UserRole.VIEWER.can_write_samples is False

    def test_can_modify_samples(self):
        """Test that only ADMIN and WINEMAKER can modify/delete samples."""
        assert UserRole.ADMIN.can_modify_samples is True
        assert UserRole.WINEMAKER.can_modify_samples is True
        assert UserRole.OPERATOR.can_modify_samples is False
        assert UserRole.VIEWER.can_modify_samples is False

    def test_can_read_all(self):
        """Test that all roles have read access."""
        assert UserRole.ADMIN.can_read_all is True
        assert UserRole.WINEMAKER.can_read_all is True
        assert UserRole.OPERATOR.can_read_all is True
        assert UserRole.VIEWER.can_read_all is True

    def test_enum_comparison(self):
        """Test that enum values can be compared."""
        role1 = UserRole.ADMIN
        role2 = UserRole.ADMIN
        role3 = UserRole.VIEWER

        assert role1 == role2
        assert role1 != role3

    def test_enum_in_collection(self):
        """Test that enum values can be used in collections."""
        admin_roles = [UserRole.ADMIN]
        write_roles = [UserRole.ADMIN, UserRole.WINEMAKER]

        assert UserRole.ADMIN in admin_roles
        assert UserRole.WINEMAKER in write_roles
        assert UserRole.OPERATOR not in admin_roles
