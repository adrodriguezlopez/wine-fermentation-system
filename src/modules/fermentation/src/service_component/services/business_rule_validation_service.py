from domain.enums.sample_type import SampleType
from domain.repositories.sample_repository_interface import ISampleRepository
from domain.repositories.fermentation_repository_interface import IFermentationRepository
from service_component.interfaces.business_rule_validation_service_interface import IBusinessRuleValidationService
from service_component.models.schemas.validations.validation_error import ValidationError
from service_component.models.schemas.validations.validation_result import ValidationResult


class BusinessRuleValidationService(IBusinessRuleValidationService):
    def __init__(self, sample_repository: ISampleRepository, fermentation_repository: IFermentationRepository):
        self.sample_repository = sample_repository
        self.fermentation_repository = fermentation_repository

    async def validate_sugar_trend(
            self,
            current: float,
            fermentation_id: int,
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
        if not self.sample_repository:
            return ValidationResult.failure(errors=[ValidationError(
                field="repository",
                message="Sample repository is not available for business rule validation",
                current_value=None
            )])
        
        previous_sample = await self.sample_repository.get_latest_sample_by_type(fermentation_id, SampleType.SUGAR)
        previous = previous_sample.value if previous_sample else None
        if not previous:
            return ValidationResult.success()
        
        if current > previous + tolerance:
            return ValidationResult.failure(errors=[ValidationError(
                field="sugar",
                message="Increasing trend is not allowed",
                current_value=current
            )])
        return ValidationResult.success()
    

    async def validate_temperature_range(
        self,
        temperature: float,
        fermentation_id: int
    ) -> ValidationResult:
        """
        Validate temperature is within acceptable fermentation range.
        Args:
            temperature: The temperature to validate.
            fermentation_type: The type of fermentation (e.g., "red", "white", "sparkling").
        Returns:
            ValidationResult: Success or failure of the validation with specific error details.
        """
        if not self.fermentation_repository:
            return ValidationResult.failure(errors=[ValidationError(
                field="repository",
                message="Fermentation repository is not available for business rule validation",
                current_value=None
            )])
        fermentation_range = await self.fermentation_repository.get_fermentation_temperature_range(fermentation_id)
        if not fermentation_range:
            return ValidationResult.success()
        min_temp, max_temp = fermentation_range
        if temperature < min_temp or temperature > max_temp:
            return ValidationResult.failure(errors=[ValidationError(
                field="temperature",
                message=f"Temperature {temperature} is out of acceptable range ({min_temp} - {max_temp})",
                current_value=temperature
            )])

        return ValidationResult.success()
        