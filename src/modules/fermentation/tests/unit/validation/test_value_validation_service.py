import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from service_component.services.value_validation_service import ValueValidationService

@pytest.fixture
def value_validation_service():
    return ValueValidationService()

def test_value_validation_service_validates_positive_sugar_values(value_validation_service):
    # Act
    result = value_validation_service.validate_sample_value("sugar", 15.3)

    # Assert
    assert result.is_valid is True
    assert result.errors == []

def test_value_validation_service_validates_negative_sugar_values(value_validation_service):
    # Act
    result = value_validation_service.validate_sample_value("sugar", -5.0)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Value must be greater than 0" in result.errors[0].message


def test_value_validation_service_validates_zero_sugar_values(value_validation_service):
    # Act
    result = value_validation_service.validate_sample_value("sugar", 0.0)

    # Assert
    assert result.is_valid is True
    assert result.errors == []


def test_value_validation_service_validate_sample_type_not_supported(value_validation_service):
    # Act
    result = value_validation_service.validate_sample_value("unknown", 10.0)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Unsupported sample type" in result.errors[0].message


def test_value_validation_service_validate_value_none(value_validation_service):
    # Act
    result = value_validation_service.validate_sample_value("sugar", None)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Value cannot be None" in result.errors[0].message


def test_value_validation_service_validates_numeric_value_within_range(value_validation_service):
    # Act
    result = value_validation_service.validate_numeric_value(25.0, min_value=20.0, max_value=30.0)

    # Assert
    assert result.is_valid is True
    assert result.errors == []

def test_value_validation_service_validates_numeric_value_below_min(value_validation_service):
    # Act
    result = value_validation_service.validate_numeric_value(15.0, min_value=20.0, max_value=30.0)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Value must be at least 20.0" in result.errors[0].message


def test_value_validation_service_validates_numeric_value_above_max(value_validation_service):
    # Act
    result = value_validation_service.validate_numeric_value(35.0, min_value=20.0, max_value=30.0)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Value must be at most 30.0" in result.errors[0].message

def test_value_validation_service_validates_numeric_value_non_numeric(value_validation_service):
    # Act
    result = value_validation_service.validate_numeric_value("not_a_number", min_value=20.0, max_value=30.0)

    # Assert
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Value must be a valid number" in result.errors[0].message