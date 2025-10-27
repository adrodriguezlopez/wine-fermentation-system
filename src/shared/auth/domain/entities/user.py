from datetime import datetime
from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING, Optional

from src.shared.infra.orm.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
    from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample


class User(BaseEntity):
    """
    User entity representing winemakers and system users.
    Handles authentication and data ownership for multi-tenant isolation.
    
    MIGRATED from modules/fermentation to shared/auth (Oct 26, 2025)
    This entity is now shared infrastructure for all modules.
    """
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}  # Allow re-registration for testing

    # User identification and authentication
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Password hash for secure authentication
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # User profile information
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    winery_id: Mapped[int] = mapped_column(ForeignKey("wineries.id"), nullable=False)

    # Authorization (NEW - added during migration)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="viewer", server_default="viewer")

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Account management timestamps (RENAMED from last_login)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # NOTE: created_at and updated_at are inherited from BaseEntity - DO NOT duplicate here

    # Relationships - using fully qualified paths to avoid ambiguity
    fermentations: Mapped[List["Fermentation"]] = relationship(
        "src.modules.fermentation.src.domain.entities.fermentation.Fermentation", 
        back_populates="fermented_by_user", 
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    samples: Mapped[List["BaseSample"]] = relationship(
        "src.modules.fermentation.src.domain.entities.samples.base_sample.BaseSample",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Note: Winery relationship commented out - Winery is in a separate module
    # winery: Mapped["Winery"] = relationship("Winery", back_populates="users", foreign_keys='User.winery_id')

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email}, full_name={self.full_name})>"
    
    @property
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        return self.is_active and self.is_verified
