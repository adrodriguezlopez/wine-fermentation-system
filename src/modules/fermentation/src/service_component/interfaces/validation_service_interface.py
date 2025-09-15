"""
Extended interface definition for the Validation Service.
Combines high-level workflow methods with granular validation functions.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from domain.entities.samples.base_sample import BaseSample
from service_component.models.schemas.validations.validation_result import ValidationResult
from service_component.models.schemas.validations.validation_error import ValidationError
from domain.enums.sample_type import SampleType
from domain.enums.fermentation_status import FermentationStatus


class IValidationService(ABC):
    """
    Extended interface for fermentation validation service.
    
    Provides both high-level workflow methods for complete validation scenarios
    and granular methods for specific validation rules that can be composed
    and tested independently.
    """

    # =============================================
    # HIGH-LEVEL WORKFLOW METHODS (Async, Repository-dependent)
    # =============================================

    @abstractmethod
    async def validate_samples(
        self,
        samples: List[BaseSample]
    ) -> ValidationResult:
        """
        Validates a batch of samples using granular validation methods.
        Orchestrates multiple validation rules for complete sample validation.

        Args:
            fermentation_id: ID of the fermentation
            samples: List of sample dictionaries to validate
            fermentation_stage: Current stage of fermentation for context

        Returns:
            ValidationResult: Comprehensive validation results with errors and warnings

        Raises:
            ValidationError: If sample format is invalid
        """
        pass

    @abstractmethod
    async def validate_chronology(
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
            ValidationResult: Success if chronology is valid, failure with details if not

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        pass


    # =============================================
    # GRANULAR VALIDATION METHODS (Sync, Pure functions)
    # =============================================

    @abstractmethod
    def validate_sample_value(
        self,
        sample_type: Union[str, SampleType],
        value: Union[float, str, None]
    ) -> ValidationResult:
        """
        Validate individual measurement values are physically reasonable.
        
        Args:
            sample_type: Type of sample (sugar, temperature, density) - accepts both str and enum
            value: Measurement value to validate
            
        Returns:
            ValidationResult: Success or failure with specific error details
        """
        pass

    @abstractmethod
    def validate_sugar_trend(
        self,
        previous: float,
        current: float,
        tolerance: float = 0.0
    ) -> ValidationResult:
        """
        Validate sugar trend follows expected fermentation progression.
        
        Args:
            previous: Previous sugar measurement
            current: Current sugar measurement  
            tolerance: Acceptable tolerance for trend validation
            
        Returns:
            ValidationResult: Success if trend is valid, failure with details if not
        """
        pass

    # =============================================
    # FACTORY METHODS (Result builders)
    # =============================================

    @abstractmethod
    def success(self) -> ValidationResult:
        """
        Factory method for successful validation result.
        
        Returns:
            ValidationResult: Success result with no errors or warnings
        """
        pass

    @abstractmethod
    def failure(self, errors: List[ValidationError]) -> ValidationResult:
        """
        Factory method for failed validation result.
        
        Args:
            errors: List of validation errors that occurred
            
        Returns:
            ValidationResult: Failure result with specified errors
        """
        pass