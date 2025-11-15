from abc import ABC, abstractmethod
from typing import List
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult

class IValidationOrchestrator(ABC):
    """
    Orchestrates multiple validation services to provide comprehensive validation.
    Combines granular validation methods from various services into high-level workflows.
    """

    @abstractmethod
    async def validate_sample_complete(
        self,
        fermentation_id: int,
        new_sample: BaseSample
    ) -> ValidationResult:
        """
        Run all validations for a single sample.

        Args:
            sample: sample entity to validate

        Returns:
            ValidationResult: Comprehensive validation results with errors and warnings
        """
        pass


    @abstractmethod
    async def validate_sample_batch(
        self,
        fermentation_id: int,
        samples: List[BaseSample]
    ) -> ValidationResult:
        """
        Validates a batch of samples for both value correctness and chronology.

        Args:
            fermentation_id: ID of the fermentation
            samples: List of sample entities to validate

        Returns:
            ValidationResult: Comprehensive validation results with errors and warnings
        """
        pass