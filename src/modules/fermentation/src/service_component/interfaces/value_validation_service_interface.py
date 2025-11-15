from abc import ABC, abstractmethod
from typing import Union
from src.modules.fermentation.src.domain.enums.sample_type import SampleType
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult

class IValueValidationService(ABC):
    """
    Pure value validation without external dependencies.
    Provides granular validation methods for individual sample values.
    """

    @abstractmethod
    def validate_sample_value(
            self,
            sample_type: Union[str, SampleType],
            value: Union[float, str, None]
        ) -> ValidationResult:
        """
        Validates measurement values are physically plausible.

        Args:
            sample_type: The type of the sample being validated.
            value: The value of the sample to validate.

        Returns:
            ValidationResult: Success or failure of the validation with specific error details.
        """
        pass

    @abstractmethod
    def validate_numeric_value(
            self,
            value: Union[float, str, None],
            min_value: float = float('-inf'),
            max_value: float = float('inf')
        ) -> ValidationResult:
        """
        Validates that a numeric value is within specified bounds.

        Args:
            value: The numeric value to validate.
            min_value: Minimum acceptable value (inclusive).
            max_value: Maximum acceptable value (inclusive).

        Returns:
            ValidationResult: Success if value is valid, failure with details if not.
        """
        pass