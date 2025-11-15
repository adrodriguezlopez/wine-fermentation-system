from typing import List, Optional
from ..validations.validation_error import ValidationError
from pydantic import BaseModel, Field, ConfigDict


class ValidationResult(BaseModel):
    """Result of business rule validation."""
    
    model_config = ConfigDict(revalidate_instances='never')

    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create successful validation result."""
        return cls.model_construct(is_valid=True, errors=[], warnings=[])

    @classmethod
    def failure(
        cls, errors: List[ValidationError], warnings: List[ValidationError] = []
    ) -> "ValidationResult":
        """Create failed validation result."""
        # Use model_construct to bypass validation since errors/warnings are already ValidationError instances
        return cls.model_construct(is_valid=False, errors=errors, warnings=warnings)

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
        return ValidationResult.model_construct(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings
        )
