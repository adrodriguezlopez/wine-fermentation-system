from typing import List, Optional
from ..validations.validation_error import ValidationError
from pydantic import BaseModel


class ValidationResult(BaseModel):
    """Result of business rule validation."""

    is_valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create successful validation result."""
        return cls(is_valid=True)

    @classmethod
    def failure(
        cls, errors: List[ValidationError], warnings: List[ValidationError] = []
    ) -> "ValidationResult":
        """Create failed validation result."""
        return cls(is_valid=False, errors=errors)

    def add_error(
        self, field: str, message: str, current_value: Optional[float] = None
    ) -> None:
        """Add validation error."""
        self.errors.append(
            ValidationError(field=field, message=message, current_value=current_value)
        )
        self.is_valid = False

    def add_warning(
        self, field: str, message: str, current_value: Optional[float] = None
    ) -> None:
        """Add validation warning."""
        self.warnings.append(
            ValidationError(field=field, message=message, current_value=current_value)
        )

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge this ValidationResult with another, combining errors and warnings."""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings
        )
