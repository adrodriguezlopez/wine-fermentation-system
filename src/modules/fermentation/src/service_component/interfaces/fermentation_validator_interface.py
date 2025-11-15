"""
Interface definition for Fermentation Validation.

Validates fermentation data and business rules.
Follows Single Responsibility Principle - separated from service orchestration.

Related:
- ADR-005: Service Layer Interfaces
- Consistent with IValidationOrchestrator pattern for samples
"""
from abc import ABC, abstractmethod

from src.modules.fermentation.src.domain.dtos import FermentationCreate
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult


class IFermentationValidator(ABC):
    """
    Interface for fermentation data validation.
    
    Responsibilities:
    - Validate fermentation creation data (ranges, business rules)
    - Validate status transitions (state machine)
    - Validate completion criteria
    
    Does NOT handle:
    - Data persistence (repository responsibility)
    - Business logic orchestration (service responsibility)
    - Sample validation (use IValidationOrchestrator)
    """

    @abstractmethod
    def validate_creation_data(self, data: FermentationCreate) -> ValidationResult:
        """
        Validates fermentation creation data.
        
        Validation Rules:
        - input_mass_kg > 0
        - initial_sugar_brix in range 0-30
        - initial_density > 0
        - vintage_year <= current year
        - vessel_code format
        
        Args:
            data: Fermentation creation DTO
            
        Returns:
            ValidationResult: Contains is_valid flag and list of errors
        """
        pass

    @abstractmethod
    def validate_status_transition(
        self,
        current_status: FermentationStatus,
        new_status: FermentationStatus
    ) -> ValidationResult:
        """
        Validates fermentation status transitions (state machine).
        
        Valid Transitions:
        - ACTIVE -> PAUSED
        - ACTIVE -> COMPLETED
        - ACTIVE -> FAILED
        - PAUSED -> ACTIVE
        - PAUSED -> FAILED
        
        Invalid Transitions:
        - COMPLETED -> * (terminal state)
        - FAILED -> * (terminal state)
        
        Args:
            current_status: Current fermentation status
            new_status: Desired new status
            
        Returns:
            ValidationResult: Contains is_valid flag and transition errors
        """
        pass

    @abstractmethod
    def validate_completion_criteria(
        self,
        input_mass_kg: float,
        final_sugar_brix: float,
        duration_days: int
    ) -> ValidationResult:
        """
        Validates fermentation completion criteria.
        
        Validation Rules:
        - final_sugar_brix < initial_sugar_brix (fermentation occurred)
        - duration_days >= minimum (e.g., 7 days)
        - Expected alcohol conversion achieved
        
        Args:
            input_mass_kg: Initial grape mass
            final_sugar_brix: Final sugar content
            duration_days: Fermentation duration
            
        Returns:
            ValidationResult: Contains is_valid flag and completion errors
        """
        pass
