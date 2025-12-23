from typing import List

# ADR-027: Structured logging
from src.shared.wine_fermentator_logging import get_logger

from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.enums.sample_type import SampleType
from src.modules.fermentation.src.service_component.interfaces.business_rule_validation_service_interface import IBusinessRuleValidationService
from src.modules.fermentation.src.service_component.interfaces.chronology_validation_service_interface import IChronologyValidationService
from src.modules.fermentation.src.service_component.interfaces.validation_orchestrator_interface import IValidationOrchestrator
from src.modules.fermentation.src.service_component.interfaces.value_validation_service_interface import IValueValidationService
from src.modules.fermentation.src.service_component.models.schemas.validations.validation_result import ValidationResult

logger = get_logger(__name__)


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
        new_sample: BaseSample
    ) -> ValidationResult:
        """
        Run all validations for a single sample.

        Args:
            new_sample: sample entity to validate

        Returns:
            ValidationResult: Comprehensive validation results with errors and warnings
        """
        logger.debug(
            "validating_sample_complete",
            fermentation_id=fermentation_id,
            sample_type=new_sample.sample_type if isinstance(new_sample.sample_type, str) else new_sample.sample_type.value
        )
        
        overall_result = ValidationResult.success()

        # Chronology Validation
        chronology_result = await self.chronology_validator.validate_sample_chronology(
            fermentation_id=fermentation_id,
            new_sample=new_sample
        )
        overall_result = overall_result.merge(chronology_result)
        if not chronology_result.is_valid:
            logger.warning(
                "chronology_validation_failed",
                fermentation_id=fermentation_id,
                error_count=len(chronology_result.errors)
            )
            return overall_result
            
        # Value Validation
        value_result = self.value_validator.validate_sample_value(
            sample_type=new_sample.sample_type,
            value=new_sample.value
        )
        overall_result = overall_result.merge(value_result)
        if not value_result.is_valid:
            logger.warning(
                "value_validation_failed",
                fermentation_id=fermentation_id,
                sample_type=new_sample.sample_type if isinstance(new_sample.sample_type, str) else new_sample.sample_type.value
            )
            return overall_result
            
        # Business Rules Validation
        # Handle both enum and string values for sample_type
        sample_type_value = new_sample.sample_type if isinstance(new_sample.sample_type, str) else new_sample.sample_type.value
        
        if sample_type_value == SampleType.SUGAR.value or new_sample.sample_type == SampleType.SUGAR:
            if new_sample.value is not None:
                business_rules_result = await self.business_rules_validator.validate_sugar_trend(
                    current=new_sample.value,
                    fermentation_id=fermentation_id,
                    tolerance=0.1
                )
                overall_result = overall_result.merge(business_rules_result)
                if not business_rules_result.is_valid:
                    logger.warning(
                        "business_rules_validation_failed",
                        fermentation_id=fermentation_id,
                        rule="sugar_trend"
                    )
                    return overall_result

        elif sample_type_value == SampleType.TEMPERATURE.value or new_sample.sample_type == SampleType.TEMPERATURE:
            # TODO: Temperature validation disabled - FermentationRepository missing get_fermentation_temperature_range method
            # if new_sample.value is not None:
            #     business_rules_result = await self.business_rules_validator.validate_temperature_range(
            #         temperature=new_sample.value,
            #         fermentation_id=fermentation_id
            #     )
            #     overall_result = overall_result.merge(business_rules_result)
            #     if not business_rules_result.is_valid:
            #         return overall_result
            pass
        
        logger.debug(
            "sample_validation_complete",
            fermentation_id=fermentation_id,
            is_valid=overall_result.is_valid
        )

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