"""User role enumeration for role-based authorization."""

from enum import Enum


class UserRole(str, Enum):
    """
    User roles with hierarchical permissions.
    
    Permission hierarchy (from highest to lowest):
    - ADMIN: Full system access, user management, all CRUD operations
    - WINEMAKER: CRUD on fermentations and samples, read wineries
    - OPERATOR: Read fermentations, create/read samples (no delete/update)
    - VIEWER: Read-only access to fermentations and samples
    """
    
    ADMIN = "admin"
    WINEMAKER = "winemaker"
    OPERATOR = "operator"
    VIEWER = "viewer"
    
    @classmethod
    def default(cls) -> "UserRole":
        """Return the default role for new users."""
        return cls.VIEWER
    
    @property
    def can_manage_users(self) -> bool:
        """Check if role can create, update, or delete users."""
        return self == UserRole.ADMIN
    
    @property
    def can_write_fermentations(self) -> bool:
        """Check if role can create, update, or delete fermentations."""
        return self in (UserRole.ADMIN, UserRole.WINEMAKER)
    
    @property
    def can_write_samples(self) -> bool:
        """Check if role can create samples (operator can add but not modify/delete)."""
        return self in (UserRole.ADMIN, UserRole.WINEMAKER, UserRole.OPERATOR)
    
    @property
    def can_modify_samples(self) -> bool:
        """Check if role can update or delete samples."""
        return self in (UserRole.ADMIN, UserRole.WINEMAKER)
    
    @property
    def can_read_all(self) -> bool:
        """Check if role has read access (all roles have read access)."""
        return True
