import datetime
from typing import Any, Dict, List, Optional, Union
from domain.entities.samples.base_sample import BaseSample
from domain.repositories import ISampleRepository
from service_component.interfaces import IValidationService
from domain.enums.fermentation_status import FermentationStatus
from domain.enums.sample_type import SampleType
from service_component.models.schemas.validations.validation_result import ValidationResult
from service_component.models.schemas.validations.validation_error import ValidationError


class ValidationService(IValidationService):
    """
    Business rule enforcement and data integrity validation for all sample 
    measurements and fermentation lifecycle operations.
    
    Implements both high-level workflow methods (async, repository-dependent) and 
    granular validation methods (sync, pure functions) for maximum flexibility.
    """


    def __init__(self, sample_repository: Optional[ISampleRepository] = None):
        """
        Initializes the validation service with an optional sample repository dependency.

        Args:
            sample_repository: Repository for historical data queries (required for async methods)
        """
        self.sample_repository = sample_repository


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
        # Handle None values
        if value is None:
            return self.failure(errors=[ValidationError(
                field=str(sample_type),
                message="Value cannot be None",
                current_value=value
            )])
        
        # Handle empty string values
        if isinstance(value, str) and value.strip() == "":
            return self.failure(errors=[ValidationError(
                field=str(sample_type),
                message="Value cannot be an empty string",
                current_value=value
            )])

        # Handle sample type is supported (convert string to enum if needed)
        if isinstance(sample_type, str):
            try:
                SampleType(sample_type)
            except ValueError:
                return self.failure(errors=[ValidationError(
                    field=str(sample_type),
                    message="Unsupported sample type",
                    current_value=sample_type
                )])
        
        # Convert to float for numeric validation
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            return self.failure(errors=[ValidationError(
                field=str(sample_type),
                message="Value must be a valid number",
                current_value=value
            )])

        # Validate positive values
        if numeric_value < 0:
            return self.failure(errors=[ValidationError(
                field=str(sample_type),
                message="Value must be greater than 0",
                current_value=numeric_value
            )])

        return ValidationResult.success()
    

    def validate_sugar_trend(
            self,
            previous: float,
            current: float,
            tolerance: float = 0.0
        ) -> ValidationResult:
        """
        Validate sugar trend follows expected fermentation progression.
        Sugar levels should decrease over time during fermentation.

        Args:
            previous: The previous sugar level.
            current: The current sugar level.
            tolerance: The acceptable tolerance for sugar level changes.

        Returns:
            ValidationResult: Success or failure of the validation with specific error details.
        """
        if current > previous + tolerance:
            return self.failure(errors=[ValidationError(
                field="sugar",
                message="Increasing trend is not allowed",
                current_value=current
            )])
        return self.success()


    def success(self) -> ValidationResult:
        """
        Factory method to create a successful validation result.

        Returns:
            ValidationResult: A successful validation result.
        """
        return ValidationResult.success()
    

    def failure(
            self,
            errors: list[ValidationError],
            warnings: list[ValidationError] = []
        ) -> ValidationResult:
        """
        Factory method to create a failed validation result.

        Args:
            errors: A list of validation errors.

        Returns:
            ValidationResult: A failed validation result.
        """
        return ValidationResult.failure(errors=errors, warnings=warnings)

    # =============================================
    # HIGH-LEVEL WORKFLOW METHODS (Async, Repository-dependent)
    # =============================================
    # TODO: this validate samples should return the valid samples as well


    async def validate_samples(
        self,
        samples: List[BaseSample]
    ) -> ValidationResult:
        """
        Validate a batch of samples using granular validation methods.
        Orchestrates multiple validation rules for complete sample validation.

        Args:
            samples: A list of dictionaries, each representing a fermentation sample to validate.

        Returns:
            ValidationResult: The result of the validation.
        """
        if not self.sample_repository:
            return self.failure(errors=[ValidationError(
                field="repository",
                message="Sample repository is not available for sample validation",
                current_value=None
            )])

        all_errors = []
        all_warnings = []

        # Validate each sample using granular methods
        for sample in samples:
            result = self.validate_sample_value(sample.sample_type, sample.value)
            if not result.is_valid:
                all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        if all_errors:
            return ValidationResult.failure(errors=all_errors, warnings=all_warnings)
        
        success_result = ValidationResult.success()
        success_result.warnings = all_warnings
        return success_result
    

    async def validate_chronology(
            self,
            fermentation_id: int,
            new_sample: BaseSample
    ) -> ValidationResult:
        """
        Validate that a new sample's timestamp maintains chronological order.

        Args:
            fermentation_id: ID of the fermentation
            new_sample: The new sample to validate

        Returns:
            ValidationResult: Success if chronology is valid, failure with details if not

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        if not self.sample_repository:
            return ValidationResult.failure(errors=[ValidationError(
                field="repository",
                message="Sample repository is not available for chronology validation",
                current_value=None
            )])
        
        sample_type = new_sample.sample_type
        new_sample_time = new_sample.recorded_at

        if not sample_type:
            return ValidationResult.failure([
                ValidationError(
                    field="sample_type",
                    message="Sample type is required for chronology validation",
                    current_value=sample_type
                )
            ])
        
        if not new_sample_time:
            return ValidationResult.failure([
                ValidationError(
                    field="recorded_at",
                    message="Sample timestamp is required for chronology validation",
                    current_value=new_sample_time
                )
            ])
        
        try:
            # Get samples for this fermentation
            all_samples = await self.sample_repository.get_samples_by_fermentation_id(fermentation_id)

            # Filter by sample type to get the latest sample of the same type
            same_type_samples = [s for s in all_samples if s.sample_type == sample_type]

            # If no previous samples of this type, any timestamp is valid (first sample of this type)
            if not same_type_samples:
                return ValidationResult.success()
            
            # Get the most recent sample of the same type
            latest_same_type_sample = max(same_type_samples, key=lambda s: s.recorded_at)

            if latest_same_type_sample.recorded_at > new_sample_time:
                return ValidationResult.failure([
                    ValidationError(
                        field="recorded_at",
                        message="New sample's timestamp must be after the latest sample of the same type",
                        current_value=new_sample_time
                    )
                ])

            return ValidationResult.success()

        except Exception as e:
            return ValidationResult.failure(errors=[ValidationError(
                field="chronology",
                message=f"Chronology validation failed: {str(e)}",
                current_value=new_sample_time
            )])