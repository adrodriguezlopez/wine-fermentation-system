from typing import Union
from domain.enums.sample_type import SampleType
from service_component.interfaces.value_validation_service_interface import IValueValidationService
from service_component.models.schemas.validations.validation_error import ValidationError
from service_component.models.schemas.validations.validation_result import ValidationResult


class ValueValidationService(IValueValidationService):

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
            return ValidationResult.failure(errors=[ValidationError(
                field=str(sample_type),
                message="Value cannot be None",
                current_value=value
            )])
        
        # Handle empty string values
        if isinstance(value, str) and value.strip() == "":
            return ValidationResult.failure(errors=[ValidationError(
                field=str(sample_type),
                message="Value cannot be an empty string",
                current_value=value
            )])

        # Handle sample type is supported (convert string to enum if needed)
        if isinstance(sample_type, str):
            try:
                SampleType(sample_type)
            except ValueError:
                return ValidationResult.failure(errors=[ValidationError(
                    field=str(sample_type),
                    message="Unsupported sample type",
                    current_value=sample_type
                )])
        
        # Convert to float for numeric validation
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            return ValidationResult.failure(errors=[ValidationError(
                field=str(sample_type),
                message="Value must be a valid number",
                current_value=value
            )])

        # Validate positive values
        if numeric_value < 0:
            return ValidationResult.failure(errors=[ValidationError(
                field=str(sample_type),
                message="Value must be greater than 0",
                current_value=numeric_value
            )])

        return ValidationResult.success()
    

    def validate_numeric_value(
            self,
            value: Union[float, str, None],
            min_value: float = float('-inf'),
            max_value: float = float('inf')
        ) -> ValidationResult:
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            return ValidationResult.failure(errors=[ValidationError(
                field="value",
                message="Value must be a valid number",
                current_value=value
            )])
        if numeric_value < min_value:
            return ValidationResult.failure(errors=[ValidationError(
                field="value",
                message=f"Value must be at least {min_value}",
                current_value=numeric_value
            )])
        elif numeric_value > max_value:
            return ValidationResult.failure(errors=[ValidationError(
                field="value",
                message=f"Value must be at most {max_value}",
                current_value=numeric_value
            )])
        return ValidationResult.success()
    