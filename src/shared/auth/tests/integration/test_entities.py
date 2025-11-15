"""
Test-specific entities for integration testing.
These entities are simplified versions without external module dependencies.
"""
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from typing import Optional


# Create test-specific declarative base
class TestBase(DeclarativeBase):
    """Test-specific declarative base."""
    pass


class TestUser(TestBase):
    """
    Test version of User entity without fermentation module relationships.
    Used for integration testing of auth module in isolation.
    
    Includes all BaseEntity fields (id, created_at, updated_at) directly
    to avoid metadata conflicts.
    """
    __tablename__ = "users"

    # BaseEntity fields (replicated to avoid metadata conflicts)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # User identification and authentication
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Password hash for secure authentication
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # User profile information
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    winery_id: Mapped[int] = mapped_column(nullable=False)

    # Authorization
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="viewer", server_default="viewer")

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Account management timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Soft delete support
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<TestUser(id={self.id}, username={self.username}, email={self.email}, full_name={self.full_name})>"
    
    @property
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        return self.is_active and self.is_verified
