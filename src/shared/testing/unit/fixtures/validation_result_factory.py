"""
ValidationResultFactory - Creates ValidationResult objects for testing

Provides factories for creating ValidationResult and ValidationError
objects with sensible defaults for unit tests.

Usage:
    # Valid result
    result = create_valid_result()
    
    # Invalid result with errors
    result = create_invalid_result([
        ValidationError(field="vintage_year", message="Invalid year")
    ])
    
    # Single error convenience
    result = create_single_error_result("vintage_year", "Invalid year")
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ValidationError:
    """
    Represents a validation error for testing.
    
    Mirrors the production ValidationError structure.
    """
    field: str
    message: str
    code: Optional[str] = None
    
    def __eq__(self, other):
        if not isinstance(other, ValidationError):
            return False
        return (
            self.field == other.field and
            self.message == other.message and
            self.code == other.code
        )
    
    def __repr__(self):
        return f"ValidationError(field='{self.field}', message='{self.message}', code='{self.code}')"


@dataclass
class ValidationResult:
    """
    Represents a validation result for testing.
    
    Mirrors the production ValidationResult structure.
    """
    is_valid: bool
    errors: List[ValidationError]
    
    def __eq__(self, other):
        if not isinstance(other, ValidationResult):
            return False
        return (
            self.is_valid == other.is_valid and
            self.errors == other.errors
        )
    
    def __repr__(self):
        return f"ValidationResult(is_valid={self.is_valid}, errors={self.errors})"
    
    def has_error(self, field: str) -> bool:
        """Check if result has error for specific field"""
        return any(error.field == field for error in self.errors)
    
    def get_error(self, field: str) -> Optional[ValidationError]:
        """Get first error for specific field"""
        for error in self.errors:
            if error.field == field:
                return error
        return None
    
    def get_errors(self, field: str) -> List[ValidationError]:
        """Get all errors for specific field"""
        return [error for error in self.errors if error.field == field]


class ValidationResultFactory:
    """
    Factory for creating ValidationResult objects for testing.
    
    Provides convenient methods for common validation scenarios.
    """
    
    @staticmethod
    def create_valid() -> ValidationResult:
        """
        Create a valid ValidationResult with no errors.
        
        Returns:
            ValidationResult with is_valid=True and empty errors list
            
        Example:
            result = ValidationResultFactory.create_valid()
            assert result.is_valid
            assert len(result.errors) == 0
        """
        return ValidationResult(is_valid=True, errors=[])
    
    @staticmethod
    def create_invalid(errors: List[ValidationError]) -> ValidationResult:
        """
        Create an invalid ValidationResult with specified errors.
        
        Args:
            errors: List of validation errors
            
        Returns:
            ValidationResult with is_valid=False and provided errors
            
        Example:
            result = ValidationResultFactory.create_invalid([
                ValidationError(field="name", message="Required"),
                ValidationError(field="year", message="Invalid year")
            ])
        """
        return ValidationResult(is_valid=False, errors=errors)
    
    @staticmethod
    def create_single_error(
        field: str,
        message: str,
        code: Optional[str] = None
    ) -> ValidationResult:
        """
        Create an invalid ValidationResult with a single error.
        
        Args:
            field: Field name that failed validation
            message: Error message
            code: Optional error code
            
        Returns:
            ValidationResult with single error
            
        Example:
            result = ValidationResultFactory.create_single_error(
                field="vintage_year",
                message="Year must be between 1900 and 2100",
                code="INVALID_RANGE"
            )
        """
        error = ValidationError(field=field, message=message, code=code)
        return ValidationResult(is_valid=False, errors=[error])
    
    @staticmethod
    def create_field_errors(
        field: str,
        messages: List[str]
    ) -> ValidationResult:
        """
        Create an invalid ValidationResult with multiple errors for same field.
        
        Args:
            field: Field name that failed validation
            messages: List of error messages
            
        Returns:
            ValidationResult with multiple errors for one field
            
        Example:
            result = ValidationResultFactory.create_field_errors(
                field="password",
                messages=[
                    "Must be at least 8 characters",
                    "Must contain uppercase letter",
                    "Must contain number"
                ]
            )
        """
        errors = [ValidationError(field=field, message=msg) for msg in messages]
        return ValidationResult(is_valid=False, errors=errors)
    
    @staticmethod
    def create_multiple_field_errors(
        field_errors: dict[str, str]
    ) -> ValidationResult:
        """
        Create an invalid ValidationResult with errors for multiple fields.
        
        Args:
            field_errors: Dictionary mapping field names to error messages
            
        Returns:
            ValidationResult with errors for multiple fields
            
        Example:
            result = ValidationResultFactory.create_multiple_field_errors({
                "name": "Required field",
                "vintage_year": "Invalid year",
                "lot_number": "Already exists"
            })
        """
        errors = [
            ValidationError(field=field, message=message)
            for field, message in field_errors.items()
        ]
        return ValidationResult(is_valid=False, errors=errors)


# Convenience functions

def create_valid_result() -> ValidationResult:
    """
    Create a valid ValidationResult.
    
    Returns:
        Valid ValidationResult
        
    Example:
        result = create_valid_result()
        assert result.is_valid
    """
    return ValidationResultFactory.create_valid()


def create_invalid_result(errors: List[ValidationError]) -> ValidationResult:
    """
    Create an invalid ValidationResult with errors.
    
    Args:
        errors: List of validation errors
        
    Returns:
        Invalid ValidationResult
        
    Example:
        result = create_invalid_result([
            ValidationError(field="name", message="Required")
        ])
    """
    return ValidationResultFactory.create_invalid(errors)


def create_single_error_result(
    field: str,
    message: str,
    code: Optional[str] = None
) -> ValidationResult:
    """
    Create an invalid ValidationResult with single error.
    
    Args:
        field: Field name
        message: Error message
        code: Optional error code
        
    Returns:
        Invalid ValidationResult with one error
        
    Example:
        result = create_single_error_result("year", "Invalid year")
    """
    return ValidationResultFactory.create_single_error(field, message, code)


def create_field_errors_result(field: str, messages: List[str]) -> ValidationResult:
    """
    Create an invalid ValidationResult with multiple errors for one field.
    
    Args:
        field: Field name
        messages: List of error messages
        
    Returns:
        Invalid ValidationResult
        
    Example:
        result = create_field_errors_result("password", [
            "Too short",
            "No uppercase"
        ])
    """
    return ValidationResultFactory.create_field_errors(field, messages)


def create_multiple_errors_result(field_errors: dict[str, str]) -> ValidationResult:
    """
    Create an invalid ValidationResult with errors for multiple fields.
    
    Args:
        field_errors: Field to message mapping
        
    Returns:
        Invalid ValidationResult
        
    Example:
        result = create_multiple_errors_result({
            "name": "Required",
            "year": "Invalid"
        })
    """
    return ValidationResultFactory.create_multiple_field_errors(field_errors)
