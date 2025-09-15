#poetry run pytest tests/service_component/services/ -v
import pytest
from service_component.models.schemas.validations.validation_error import ValidationError
from service_component.services.validation_service import ValidationService  # Add this import


@pytest.fixture
def validation_service():
    return ValidationService()


def test_validation_service_validates_positive_sugar_values(validation_service):
    # Act
    result = validation_service.validate_sample_value("sugar", 15.3)

    # Assert
    assert result.is_valid is True
    assert result.errors == []


def test_validation_service_validates_negative_sugar_values(validation_service):
    # Act
    result = validation_service.validate_sample_value("sugar", -5.0)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Value must be greater than 0" in result.errors[0].message


def test_validation_service_validates_zero_sugar_values(validation_service):
    # Act
    result = validation_service.validate_sample_value("sugar", 0.0)

    # Assert
    assert result.is_valid is True
    assert result.errors == []


def test_validation_service_validate_sample_type_not_supported(validation_service):
    # Act
    result = validation_service.validate_sample_value("unknown", 10.0)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Unsupported sample type" in result.errors[0].message


def test_validate_sugar_chronology_decreasing_trend(validation_service):
    # Act
    result = validation_service.validate_sugar_trend(previous=10.0, current=9.5, tolerance=0.2)

    # Assert
    assert result.is_valid is True
    assert result.errors == []


def test_validate_sugar_chronology_increasing_trend(validation_service):
    # Act
    result = validation_service.validate_sugar_trend(previous=9.0, current=9.5, tolerance=0.2)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Increasing trend is not allowed" in result.errors[0].message


def test_validation_service_result_success_factory_method(validation_service):
    # Act
    result = validation_service.success()

    # Assert
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


def test_validation_service_result_failure_with_multiple_errors(validation_service):
    # Arrange
    errors = [
        ValidationError(field="sugar", message="Value too low", current_value=5.0),
        ValidationError(field="temperature", message="Value out of range", current_value=105.0),
    ]
    # Act
    result = validation_service.failure(errors)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 2
    assert result.errors[0].field == "sugar"
    assert result.errors[1].field == "temperature"
    assert len(result.warnings) == 0


def test_validation_service_add_warning_does_not_invalidate_result(validation_service):
    # Arrange
    result = validation_service.success()
    
    # Act
    result.add_warning("temperature", "Temperature slightly high", current_value=35.0)

    # Assert
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 1
    assert result.warnings[0].field == "temperature"
    assert result.warnings[0].message == "Temperature slightly high"
    assert result.warnings[0].current_value == 35.0


def test_validation_service_with_none_values_should_fail(validation_service):  # Removed 'self'
    # Act
    result = validation_service.validate_sample_value("sugar", None)

    # Assert
    assert result.is_valid is False
    assert "Value cannot be None" in result.errors[0].message
    assert len(result.errors) == 1


def test_validation_service_with_empty_string_should_fail(validation_service):  # Removed 'self'
    # Act
    result = validation_service.validate_sample_value("sugar", "")

    # Assert
    assert result.is_valid is False
    assert "Value cannot be an empty string" in result.errors[0].message
    assert len(result.errors) == 1