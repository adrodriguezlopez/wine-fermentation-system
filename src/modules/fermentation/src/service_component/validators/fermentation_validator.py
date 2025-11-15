"""
Concrete implementation of IFermentationValidator.

Validates fermentation data and business rules.
Extracted from FermentationService to follow SRP.
"""
from datetime import datetime
from typing import List

from src.modules.fermentation.src.domain.dtos import FermentationCreate
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.service_component.interfaces.fermentation_validator_interface import IFermentationValidator
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_error import ValidationError


class FermentationValidator(IFermentationValidator):
    """
    Concrete validator for fermentation data.
    
    Implements business rules and data validation logic.
    Stateless - no internal state, pure validation logic.
    """

    def validate_creation_data(self, data: FermentationCreate) -> ValidationResult:
        """
        Validates fermentation creation data.
        
        Args:
            data: Fermentation creation DTO
            
        Returns:
            ValidationResult: Validation result with errors if any
        """
        errors: List[ValidationError] = []
        
        # Validate input_mass_kg
        if data.input_mass_kg <= 0:
            errors.append(ValidationError(
                field="input_mass_kg",
                message=f"Input mass must be positive, got {data.input_mass_kg}",
                current_value=data.input_mass_kg
            ))
        
        # Validate initial_sugar_brix (typical range: 0-30 Brix)
        if not (0 <= data.initial_sugar_brix <= 30):
            errors.append(ValidationError(
                field="initial_sugar_brix",
                message=f"Initial sugar Brix must be between 0 and 30, got {data.initial_sugar_brix}",
                current_value=data.initial_sugar_brix,
                expected_range="0-30"
            ))
        
        # Validate initial_density
        if data.initial_density <= 0:
            errors.append(ValidationError(
                field="initial_density",
                message=f"Initial density must be positive, got {data.initial_density}",
                current_value=data.initial_density
            ))
        
        # Validate vintage_year (cannot be in the future)
        current_year = datetime.now().year
        if data.vintage_year > current_year:
            errors.append(ValidationError(
                field="vintage_year",
                message=f"Vintage year cannot be in the future. Current year: {current_year}, got: {data.vintage_year}",
                current_value=data.vintage_year
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def validate_status_transition(
        self,
        current_status: FermentationStatus,
        new_status: FermentationStatus
    ) -> ValidationResult:
        """
        Validates fermentation status transitions (state machine).
        
        Args:
            current_status: Current fermentation status
            new_status: Desired new status
            
        Returns:
            ValidationResult: Validation result with errors if invalid transition
        """
        errors: List[ValidationError] = []
        
        # Define valid state transitions
        # Based on actual FermentationStatus enum: ACTIVE, LAG, DECLINE, SLOW, STUCK, COMPLETED
        valid_transitions = {
            FermentationStatus.ACTIVE: [
                FermentationStatus.DECLINE,
                FermentationStatus.SLOW,
                FermentationStatus.COMPLETED,
                FermentationStatus.STUCK
            ],
            FermentationStatus.LAG: [
                FermentationStatus.ACTIVE,
                FermentationStatus.STUCK
            ],
            FermentationStatus.DECLINE: [
                FermentationStatus.SLOW,
                FermentationStatus.STUCK,
                FermentationStatus.COMPLETED
            ],
            FermentationStatus.SLOW: [
                FermentationStatus.ACTIVE,
                FermentationStatus.STUCK,
                FermentationStatus.COMPLETED
            ],
            # Terminal states - no transitions allowed
            FermentationStatus.COMPLETED: [],
            FermentationStatus.STUCK: []
        }
        
        # Check if transition is valid
        allowed_transitions = valid_transitions.get(current_status, [])
        
        if new_status not in allowed_transitions:
            errors.append(ValidationError(
                field="status",
                message=f"Invalid status transition from {current_status.value} to {new_status.value}"
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def validate_completion_criteria(
        self,
        input_mass_kg: float,
        final_sugar_brix: float,
        duration_days: int
    ) -> ValidationResult:
        """
        Validates fermentation completion criteria.
        
        Args:
            input_mass_kg: Initial grape mass
            final_sugar_brix: Final sugar content
            duration_days: Fermentation duration
            
        Returns:
            ValidationResult: Validation result with errors if criteria not met
        """
        errors: List[ValidationError] = []
        
        # Minimum duration (typical: at least 7 days for proper fermentation)
        MIN_DURATION_DAYS = 7
        if duration_days < MIN_DURATION_DAYS:
            errors.append(ValidationError(
                field="duration",
                message=f"Fermentation duration must be at least {MIN_DURATION_DAYS} days, got {duration_days}",
                current_value=duration_days
            ))
        
        # Final sugar should be low (< 5 Brix for dry wines)
        MAX_FINAL_BRIX = 5.0
        if final_sugar_brix > MAX_FINAL_BRIX:
            errors.append(ValidationError(
                field="final_sugar_brix",
                message=f"Final sugar Brix too high for completion (expected < {MAX_FINAL_BRIX}, got {final_sugar_brix})",
                current_value=final_sugar_brix,
                expected_range=f"0-{MAX_FINAL_BRIX}"
            ))
        
        # Validate positive values
        if input_mass_kg <= 0:
            errors.append(ValidationError(
                field="input_mass_kg",
                message=f"Input mass must be positive, got {input_mass_kg}",
                current_value=input_mass_kg
            ))
        
        if final_sugar_brix < 0:
            errors.append(ValidationError(
                field="final_sugar_brix",
                message=f"Final sugar Brix cannot be negative, got {final_sugar_brix}",
                current_value=final_sugar_brix
            ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
