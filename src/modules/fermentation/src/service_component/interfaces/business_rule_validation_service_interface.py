from abc import ABC, abstractmethod
from domain.entities.samples.base_sample import BaseSample
from service_component.models.schemas.validations.validation_result import ValidationResult

class IBusinessRuleValidationService(ABC):
    """
    Interface for business rule validation service.
    
    Defines methods for enforcing business rules and data integrity
    in fermentation workflows.
    """

    @abstractmethod
    def validate_sugar_trend(
        self,
        current: float,
        fermentation_id: int,
        tolerance: float = 0.0
    ) -> ValidationResult:
        """
        Validates that sugar levels are non-increasing over time.

        Args:
            current: Current sugar measurement
            fermentation_id: ID of the fermentation
            tolerance: Acceptable tolerance for minor increases

        Returns:
            ValidationResult: Success if trend is valid, failure with details if not.
        """
        pass
    

    @abstractmethod
    def validate_temperature_range(
        self,
        temperature: float,
        fermentation_id: int,
    ) -> ValidationResult:
        """
        Validates that temperature is within acceptable fermentation range.
        """
        pass


    