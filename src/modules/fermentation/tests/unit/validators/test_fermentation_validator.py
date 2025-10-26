"""
Unit tests for FermentationValidator.

Tests validation logic independently from service orchestration.
Following SRP - validator has single responsibility: validate data.
"""

import pytest
from datetime import datetime

from src.modules.fermentation.src.service_component.validators.fermentation_validator import FermentationValidator
from src.modules.fermentation.src.service_component.interfaces.fermentation_validator_interface import IFermentationValidator
from src.modules.fermentation.src.domain.dtos import FermentationCreate
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus


class TestFermentationValidatorInterface:
    """Verify FermentationValidator implements interface correctly."""
    
    def test_validator_implements_interface(self):
        """
        GIVEN FermentationValidator class
        WHEN checking inheritance
        THEN it implements IFermentationValidator
        """
        assert issubclass(FermentationValidator, IFermentationValidator)


class TestValidateCreationData:
    """Test suite for validate_creation_data() method."""
    
    @pytest.fixture
    def validator(self) -> FermentationValidator:
        """Validator instance."""
        return FermentationValidator()
    
    def test_valid_data_passes(self, validator: FermentationValidator):
        """
        GIVEN valid fermentation creation data
        WHEN validate_creation_data is called
        THEN validation passes (is_valid = True, no errors)
        """
        # Arrange
        valid_data = FermentationCreate(
            fermented_by_user_id=42,
            vintage_year=2025,
            yeast_strain="EC-1118",
            input_mass_kg=1000.0,
            initial_sugar_brix=24.5,
            initial_density=1.105,
            vessel_code="T-001",
            start_date=datetime(2025, 10, 1, 8, 0, 0)
        )
        
        # Act
        result = validator.validate_creation_data(valid_data)
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_negative_mass_fails(self, validator: FermentationValidator):
        """
        GIVEN data with negative input_mass_kg
        WHEN validate_creation_data is called
        THEN validation fails with INVALID_MASS error
        """
        # Arrange
        invalid_data = FermentationCreate(
            fermented_by_user_id=42,
            vintage_year=2025,
            yeast_strain="EC-1118",
            input_mass_kg=-500.0,  # ❌ Negative
            initial_sugar_brix=24.5,
            initial_density=1.105,
            vessel_code="T-001",
            start_date=datetime(2025, 10, 1, 8, 0, 0)
        )
        
        # Act
        result = validator.validate_creation_data(invalid_data)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "input_mass_kg"
        assert "positive" in result.errors[0].message.lower()
    
    def test_brix_out_of_range_fails(self, validator: FermentationValidator):
        """
        GIVEN data with initial_sugar_brix > 30
        WHEN validate_creation_data is called
        THEN validation fails with INVALID_BRIX error
        """
        # Arrange
        invalid_data = FermentationCreate(
            fermented_by_user_id=42,
            vintage_year=2025,
            yeast_strain="EC-1118",
            input_mass_kg=1000.0,
            initial_sugar_brix=35.5,  # ❌ Out of range (0-30)
            initial_density=1.105,
            vessel_code="T-001",
            start_date=datetime(2025, 10, 1, 8, 0, 0)
        )
        
        # Act
        result = validator.validate_creation_data(invalid_data)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "initial_sugar_brix"
        assert "30" in result.errors[0].message
    
    def test_negative_density_fails(self, validator: FermentationValidator):
        """
        GIVEN data with negative initial_density
        WHEN validate_creation_data is called
        THEN validation fails with INVALID_DENSITY error
        """
        # Arrange
        invalid_data = FermentationCreate(
            fermented_by_user_id=42,
            vintage_year=2025,
            yeast_strain="EC-1118",
            input_mass_kg=1000.0,
            initial_sugar_brix=24.5,
            initial_density=-1.0,  # ❌ Negative
            vessel_code="T-001",
            start_date=datetime(2025, 10, 1, 8, 0, 0)
        )
        
        # Act
        result = validator.validate_creation_data(invalid_data)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "initial_density"
        assert "positive" in result.errors[0].message.lower()
    
    def test_future_vintage_year_fails(self, validator: FermentationValidator):
        """
        GIVEN data with vintage_year in the future
        WHEN validate_creation_data is called
        THEN validation fails with INVALID_VINTAGE_YEAR error
        """
        # Arrange
        invalid_data = FermentationCreate(
            fermented_by_user_id=42,
            vintage_year=2099,  # ❌ Future year
            yeast_strain="EC-1118",
            input_mass_kg=1000.0,
            initial_sugar_brix=24.5,
            initial_density=1.105,
            vessel_code="T-001",
            start_date=datetime(2025, 10, 1, 8, 0, 0)
        )
        
        # Act
        result = validator.validate_creation_data(invalid_data)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "vintage_year"
        assert "future" in result.errors[0].message.lower()
    
    def test_multiple_errors_accumulated(self, validator: FermentationValidator):
        """
        GIVEN data with multiple validation errors
        WHEN validate_creation_data is called
        THEN all errors are accumulated in result
        """
        # Arrange
        invalid_data = FermentationCreate(
            fermented_by_user_id=42,
            vintage_year=2099,  # ❌ Future
            yeast_strain="EC-1118",
            input_mass_kg=-100.0,  # ❌ Negative
            initial_sugar_brix=35.5,  # ❌ Out of range
            initial_density=-1.0,  # ❌ Negative
            vessel_code="T-001",
            start_date=datetime(2025, 10, 1, 8, 0, 0)
        )
        
        # Act
        result = validator.validate_creation_data(invalid_data)
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 4  # All 4 validation errors
        error_fields = {error.field for error in result.errors}
        assert error_fields == {"input_mass_kg", "initial_sugar_brix", "initial_density", "vintage_year"}


class TestValidateStatusTransition:
    """Test suite for validate_status_transition() method."""
    
    @pytest.fixture
    def validator(self) -> FermentationValidator:
        """Validator instance."""
        return FermentationValidator()
    
    def test_active_to_completed_valid(self, validator: FermentationValidator):
        """
        GIVEN ACTIVE status
        WHEN transitioning to COMPLETED
        THEN validation passes
        """
        # Act
        result = validator.validate_status_transition(
            current_status=FermentationStatus.ACTIVE,
            new_status=FermentationStatus.COMPLETED
        )
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_completed_to_active_invalid(self, validator: FermentationValidator):
        """
        GIVEN COMPLETED status (terminal state)
        WHEN trying to transition to ACTIVE
        THEN validation fails (terminal state cannot transition)
        """
        # Act
        result = validator.validate_status_transition(
            current_status=FermentationStatus.COMPLETED,
            new_status=FermentationStatus.ACTIVE
        )
        
        # Assert
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field == "status"
        assert "transition" in result.errors[0].message.lower()


class TestValidateCompletionCriteria:
    """Test suite for validate_completion_criteria() method."""
    
    @pytest.fixture
    def validator(self) -> FermentationValidator:
        """Validator instance."""
        return FermentationValidator()
    
    def test_valid_completion_criteria_passes(self, validator: FermentationValidator):
        """
        GIVEN valid completion criteria
        WHEN validate_completion_criteria is called
        THEN validation passes
        """
        # Act
        result = validator.validate_completion_criteria(
            input_mass_kg=1000.0,
            final_sugar_brix=2.5,  # Low residual sugar
            duration_days=14  # >= 7 days
        )
        
        # Assert
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_short_duration_fails(self, validator: FermentationValidator):
        """
        GIVEN duration < 7 days
        WHEN validate_completion_criteria is called
        THEN validation fails with INSUFFICIENT_DURATION error
        """
        # Act
        result = validator.validate_completion_criteria(
            input_mass_kg=1000.0,
            final_sugar_brix=2.5,
            duration_days=3  # ❌ Too short
        )
        
        # Assert
        assert result.is_valid is False
        assert any(error.field == "duration" and "7 days" in error.message for error in result.errors)
    
    def test_high_residual_sugar_fails(self, validator: FermentationValidator):
        """
        GIVEN final_sugar_brix > 5
        WHEN validate_completion_criteria is called
        THEN validation fails with HIGH_RESIDUAL_SUGAR error
        """
        # Act
        result = validator.validate_completion_criteria(
            input_mass_kg=1000.0,
            final_sugar_brix=8.0,  # ❌ Too high
            duration_days=14
        )
        
        # Assert
        assert result.is_valid is False
        assert any(error.field == "final_sugar_brix" and "too high" in error.message.lower() for error in result.errors)
