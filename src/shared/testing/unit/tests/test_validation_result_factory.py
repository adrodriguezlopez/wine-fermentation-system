"""
Tests for ValidationResultFactory

Validates the behavior and API of the validation result factory.
Follows TDD principles from ADR-012.
"""

import pytest

from src.shared.testing.unit.fixtures.validation_result_factory import (
    ValidationError,
    ValidationResult,
    ValidationResultFactory,
    create_valid_result,
    create_invalid_result,
    create_single_error_result,
    create_field_errors_result,
    create_multiple_errors_result,
)


class TestValidationError:
    """Test suite for ValidationError dataclass"""
    
    def test_create_basic_error(self):
        """Should create error with field and message"""
        # Act
        error = ValidationError(field="name", message="Required field")
        
        # Assert
        assert error.field == "name"
        assert error.message == "Required field"
        assert error.code is None
    
    def test_create_error_with_code(self):
        """Should create error with optional code"""
        # Act
        error = ValidationError(
            field="vintage_year",
            message="Invalid year",
            code="INVALID_RANGE"
        )
        
        # Assert
        assert error.field == "vintage_year"
        assert error.message == "Invalid year"
        assert error.code == "INVALID_RANGE"
    
    def test_errors_equality(self):
        """Should support equality comparison"""
        # Arrange
        error1 = ValidationError(field="name", message="Required")
        error2 = ValidationError(field="name", message="Required")
        error3 = ValidationError(field="name", message="Different")
        
        # Assert
        assert error1 == error2
        assert error1 != error3
    
    def test_error_repr(self):
        """Should have readable repr"""
        # Arrange
        error = ValidationError(field="name", message="Required", code="REQ")
        
        # Act
        repr_str = repr(error)
        
        # Assert
        assert "ValidationError" in repr_str
        assert "name" in repr_str
        assert "Required" in repr_str


class TestValidationResult:
    """Test suite for ValidationResult dataclass"""
    
    def test_create_valid_result(self):
        """Should create valid result"""
        # Act
        result = ValidationResult(is_valid=True, errors=[])
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_create_invalid_result(self):
        """Should create invalid result with errors"""
        # Arrange
        errors = [
            ValidationError(field="name", message="Required"),
            ValidationError(field="year", message="Invalid"),
        ]
        
        # Act
        result = ValidationResult(is_valid=False, errors=errors)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 2
    
    def test_has_error(self):
        """Should check if field has error"""
        # Arrange
        errors = [
            ValidationError(field="name", message="Required"),
            ValidationError(field="year", message="Invalid"),
        ]
        result = ValidationResult(is_valid=False, errors=errors)
        
        # Assert
        assert result.has_error("name") is True
        assert result.has_error("year") is True
        assert result.has_error("other") is False
    
    def test_get_error(self):
        """Should get first error for field"""
        # Arrange
        error1 = ValidationError(field="name", message="Required")
        error2 = ValidationError(field="name", message="Too short")
        result = ValidationResult(is_valid=False, errors=[error1, error2])
        
        # Act
        found_error = result.get_error("name")
        
        # Assert
        assert found_error == error1
    
    def test_get_error_not_found(self):
        """Should return None for non-existent field"""
        # Arrange
        result = ValidationResult(is_valid=True, errors=[])
        
        # Act
        found_error = result.get_error("name")
        
        # Assert
        assert found_error is None
    
    def test_get_errors(self):
        """Should get all errors for field"""
        # Arrange
        error1 = ValidationError(field="password", message="Too short")
        error2 = ValidationError(field="password", message="No uppercase")
        error3 = ValidationError(field="name", message="Required")
        result = ValidationResult(is_valid=False, errors=[error1, error2, error3])
        
        # Act
        password_errors = result.get_errors("password")
        
        # Assert
        assert len(password_errors) == 2
        assert error1 in password_errors
        assert error2 in password_errors
        assert error3 not in password_errors
    
    def test_result_equality(self):
        """Should support equality comparison"""
        # Arrange
        errors1 = [ValidationError(field="name", message="Required")]
        errors2 = [ValidationError(field="name", message="Required")]
        
        result1 = ValidationResult(is_valid=False, errors=errors1)
        result2 = ValidationResult(is_valid=False, errors=errors2)
        result3 = ValidationResult(is_valid=True, errors=[])
        
        # Assert
        assert result1 == result2
        assert result1 != result3


class TestValidationResultFactory:
    """Test suite for ValidationResultFactory"""
    
    def test_create_valid(self):
        """Should create valid result"""
        # Act
        result = ValidationResultFactory.create_valid()
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_create_invalid(self):
        """Should create invalid result with errors"""
        # Arrange
        errors = [
            ValidationError(field="name", message="Required"),
            ValidationError(field="year", message="Invalid"),
        ]
        
        # Act
        result = ValidationResultFactory.create_invalid(errors)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert result.errors == errors
    
    def test_create_single_error(self):
        """Should create result with single error"""
        # Act
        result = ValidationResultFactory.create_single_error(
            field="vintage_year",
            message="Year must be between 1900 and 2100"
        )
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "vintage_year"
        assert result.errors[0].message == "Year must be between 1900 and 2100"
        assert result.errors[0].code is None
    
    def test_create_single_error_with_code(self):
        """Should create single error with code"""
        # Act
        result = ValidationResultFactory.create_single_error(
            field="vintage_year",
            message="Invalid range",
            code="INVALID_RANGE"
        )
        
        # Assert
        assert len(result.errors) == 1
        assert result.errors[0].code == "INVALID_RANGE"
    
    def test_create_field_errors(self):
        """Should create multiple errors for same field"""
        # Arrange
        messages = [
            "Must be at least 8 characters",
            "Must contain uppercase letter",
            "Must contain number"
        ]
        
        # Act
        result = ValidationResultFactory.create_field_errors(
            field="password",
            messages=messages
        )
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 3
        assert all(e.field == "password" for e in result.errors)
        assert result.errors[0].message == messages[0]
        assert result.errors[1].message == messages[1]
        assert result.errors[2].message == messages[2]
    
    def test_create_multiple_field_errors(self):
        """Should create errors for multiple fields"""
        # Arrange
        field_errors = {
            "name": "Required field",
            "vintage_year": "Invalid year",
            "lot_number": "Already exists"
        }
        
        # Act
        result = ValidationResultFactory.create_multiple_field_errors(field_errors)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 3
        assert result.has_error("name")
        assert result.has_error("vintage_year")
        assert result.has_error("lot_number")


class TestConvenienceFunctions:
    """Test convenience factory functions"""
    
    def test_create_valid_result(self):
        """Should create valid result via convenience function"""
        # Act
        result = create_valid_result()
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_create_invalid_result(self):
        """Should create invalid result via convenience function"""
        # Arrange
        errors = [ValidationError(field="name", message="Required")]
        
        # Act
        result = create_invalid_result(errors)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 1
    
    def test_create_single_error_result(self):
        """Should create single error result via convenience function"""
        # Act
        result = create_single_error_result("year", "Invalid year")
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "year"
    
    def test_create_field_errors_result(self):
        """Should create field errors result via convenience function"""
        # Act
        result = create_field_errors_result("password", ["Too short", "No uppercase"])
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 2
    
    def test_create_multiple_errors_result(self):
        """Should create multiple errors result via convenience function"""
        # Act
        result = create_multiple_errors_result({
            "name": "Required",
            "year": "Invalid"
        })
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 2


class TestRealWorldScenarios:
    """Test realistic usage scenarios"""
    
    def test_service_validation_success(self):
        """Should support successful service validation scenario"""
        # Act
        result = create_valid_result()
        
        # Simulate service check
        if result.is_valid:
            # Proceed with business logic
            success = True
        else:
            success = False
        
        # Assert
        assert success is True
    
    def test_service_validation_failure(self):
        """Should support failed service validation scenario"""
        # Arrange
        result = create_single_error_result(
            field="vintage_year",
            message="Year cannot be in the future"
        )
        
        # Act
        if not result.is_valid:
            error_message = result.errors[0].message
        
        # Assert
        assert error_message == "Year cannot be in the future"
    
    def test_form_validation_multiple_errors(self):
        """Should support form validation with multiple field errors"""
        # Arrange
        result = create_multiple_errors_result({
            "name": "Name is required",
            "vintage_year": "Year must be between 1900 and 2100",
            "lot_number": "Lot number already exists"
        })
        
        # Act - Check specific field error
        year_error = result.get_error("vintage_year")
        
        # Assert
        assert year_error is not None
        assert year_error.message == "Year must be between 1900 and 2100"
    
    def test_password_validation_multiple_rules(self):
        """Should support multi-rule validation for same field"""
        # Arrange
        result = create_field_errors_result("password", [
            "Must be at least 8 characters",
            "Must contain uppercase letter",
            "Must contain number",
            "Must contain special character"
        ])
        
        # Act
        password_errors = result.get_errors("password")
        
        # Assert
        assert len(password_errors) == 4
        assert all(e.field == "password" for e in password_errors)
