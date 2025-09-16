import datetime
from domain.entities.samples.base_sample import BaseSample
from domain.repositories.sample_repository_interface import ISampleRepository
from service_component.interfaces.chronology_validation_service_interface import IChronologyValidationService
from service_component.models.schemas.validations.validation_error import ValidationError
from service_component.models.schemas.validations.validation_result import ValidationResult


class ChronologyValidationService(IChronologyValidationService):
    def __init__(self, sample_repository: ISampleRepository):
        """
        Initializes the chronology validation service with an optional sample repository dependency.
        Args:
            sample_repository: Repository for historical data queries (required for async methods)
        """
        self.sample_repository = sample_repository
    
    async def validate_sample_chronology(
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


    async def validate_fermentation_timeline(
        self,
        fermentation_id: int,
        sample_timestamp: datetime
    ) -> ValidationResult:
        """Validate sample is after fermentation start"""
        if not self.sample_repository:
            return ValidationResult.failure(errors=[ValidationError(
                field="repository",
                message="Sample repository is not available for fermentation timeline validation",
                current_value=None
            )])
        
        if not sample_timestamp:
            return ValidationResult.failure([
                ValidationError(
                    field="recorded_at",
                    message="Sample timestamp is required for fermentation timeline validation",
                    current_value=sample_timestamp
                )
            ])
        
        try:
            # Get fermentation start date
            start_date = await self.sample_repository.get_fermentation_start_date(fermentation_id)

            if not start_date:
                return ValidationResult.failure([
                    ValidationError(
                        field="fermentation_start",
                        message="Fermentation start date not found for the given ID",
                        current_value=fermentation_id
                    )
                ])
            
            if sample_timestamp < start_date:
                return ValidationResult.failure([
                    ValidationError(
                        field="recorded_at",
                        message="Sample timestamp cannot be before fermentation start date",
                        current_value=sample_timestamp
                    )
                ])

            return ValidationResult.success()

        except Exception as e:
            return ValidationResult.failure(errors=[ValidationError(
                field="fermentation_timeline",
                message=f"Fermentation timeline validation failed: {str(e)}",
                current_value=sample_timestamp
            )])