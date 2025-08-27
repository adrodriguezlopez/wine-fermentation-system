"""
Interface definition for the Validation Service.
Defines the contract that any validation service implementation must follow.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime


class IValidationService(ABC):
    """
    Interface for fermentation validation service.
    Defines core operations for validating measurements, chronology,
    and trends.
    """

    @abstractmethod
    async def validate_measurements(
        self, measurements: Dict[str, float], fermentation_stage: str
    ) -> Dict[str, Any]:
        """
        Validates that measurements are within expected ranges
        for the fermentation stage.

        Args:
            measurements: Dictionary with measurement values
            (glucose, ethanol, temperature)
            fermentation_stage: Current stage of fermentation
            (e.g., 'INITIAL', 'ACTIVE', 'FINAL')

        Returns:
            Dict[str, Any]: Validation results including:
                - is_valid: bool
                - errors: List of validation errors if any
                - warnings: List of warnings if measurements are near bounds

        Raises:
            ValidationError: If measurement format is invalid
        """
        pass

    @abstractmethod
    async def validate_chronology(
        self, fermentation_id: int, new_sample_time: datetime
    ) -> bool:
        """
        Validates that a new sample's timestamp maintains chronological order.

        Args:
            fermentation_id: ID of the fermentation
            new_sample_time: Timestamp of the new sample

        Returns:
            bool: True if chronology is valid, False otherwise

        Raises:
            NotFoundError: If fermentation_id doesn't exist
        """
        pass

    @abstractmethod
    async def validate_trend(
        self, fermentation_id: int, new_measurements: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Validates that new measurements follow expected fermentation trends.

        Args:
            fermentation_id: ID of the fermentation
            new_measurements: Latest measurements to validate

        Returns:
            Dict[str, Any]: Trend analysis including:
                - trend_valid: bool
                - deviations: List of parameters deviating from expected trends
                - recommendations: List of suggested actions if trends are off

        Raises:
            NotFoundError: If fermentation_id doesn't exist
            ValidationError: If measurement format is invalid
        """
        pass

    @abstractmethod
    async def check_anomalies(
        self, fermentation_id: int, time_window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Checks for anomalies in recent measurements.

        Args:
            fermentation_id: ID of the fermentation
            time_window_hours: Hours of history to analyze, defaults to 24

        Returns:
            List[Dict[str, Any]]: List of detected anomalies, each containing:
                - parameter: Name of the parameter showing anomaly
                - severity: Severity level ('WARNING', 'CRITICAL')
                - description: Detailed description of the anomaly
                - suggested_action: Recommended action to address the anomaly

        Raises:
            NotFoundError: If fermentation_id doesn't exist
            ValidationError: If time window is invalid
        """
        pass
