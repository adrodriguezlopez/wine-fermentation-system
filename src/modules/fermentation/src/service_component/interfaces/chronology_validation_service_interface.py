from abc import ABC, abstractmethod
from datetime import datetime
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult

class IChronologyValidationService(ABC):
    """
    Time-based validation rules for fermentation samples.
    Required repository access for historical data queries.
    """

    @abstractmethod
    async def validate_sample_chronology(
            self,
            fermentation_id: int,
            new_sample: BaseSample
    ) -> ValidationResult:
        """
        Validates that a new sample's timestamp maintains chronological order.

        Args:
            fermentation_id: ID of the fermentation
            new_sample: The new sample to validate

        Returns:
            ValidationResult: Success if chronology is valid, failure with details if not.

        Raises:
            NotFoundError: If fermentation_id doesn't exist
            UnauthorizedError: If caller is not authorized to access this fermentation
        """
        pass

    @abstractmethod
    async def validate_fermentation_timeline(
        self,
        fermentation_id: int,
        sample_timestamp: datetime
    ) -> ValidationResult:
        """Validate sample is after fermentation start"""
        pass