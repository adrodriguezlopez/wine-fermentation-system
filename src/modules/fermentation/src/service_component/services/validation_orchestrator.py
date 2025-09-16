from typing import List
from domain.entities.samples.base_sample import BaseSample
from domain.enums.sample_type import SampleType
from service_component.interfaces.business_rule_validation_service_interface import IBusinessRuleValidationService
from service_component.interfaces.chronology_validation_service_interface import IChronologyValidationService
from service_component.interfaces.validation_orchestrator_interface import IValidationOrchestrator
from service_component.interfaces.value_validation_service_interface import IValueValidationService
from service_component.models.schemas.validations.validation_result import ValidationResult


class ValidationOrchestrator(IValidationOrchestrator):
    def __init__(
        self,
        chronology_validator: IChronologyValidationService,
        value_validator: IValueValidationService,
        business_rules_validator: IBusinessRuleValidationService,

    ):
        self.chronology_validator = chronology_validator
        self.value_validator = value_validator
        self.business_rules_validator = business_rules_validator

    async def validate_sample_complete(
        self,
        fermentation_id: int,
        sample: BaseSample
    ) -> ValidationResult:
        """
        Run all validations for a single sample.

        Args:
            sample: sample entity to validate

        Returns:
            ValidationResult: Comprehensive validation results with errors and warnings
        """
        overall_result = ValidationResult.success()

        # Chronology Validation
        chronology_result = await self.chronology_validator.validate_chronology(
            fermentation_id=fermentation_id,
            new_sample=sample
        )
        overall_result = overall_result.merge(chronology_result)
        if not chronology_result.is_success:
            return overall_result
        # Value Validation
        value_result = self.value_validator.validate_values(
            sample=sample
        )
        overall_result = overall_result.merge(value_result)
        if not value_result.is_success:
            return overall_result
        # Business Rules Validation
        match sample.sample_type:
            case SampleType.SUGAR:
                if sample.value is not None:
                    business_rules_result = self.business_rules_validator.validate_sugar_trend(
                        current=sample.value,
                        fermentation_id=fermentation_id,
                        tolerance=0.1
                    )
                    overall_result = overall_result.merge(business_rules_result)
                    if not business_rules_result.is_success:
                        return overall_result
                    
            case SampleType.TEMPERATURE:
                if sample.value is not None and sample.fermentation_type is not None:
                    business_rules_result = self.business_rules_validator.validate_temperature_range(
                        temperature=sample.value,
                        fermentation_id=fermentation_id
                    )
                    overall_result = overall_result.merge(business_rules_result)
                    if not business_rules_result.is_success:
                        return overall_result        
                    
        return overall_result
    
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
        NotImplementedError("Batch validation not implemented yet.")