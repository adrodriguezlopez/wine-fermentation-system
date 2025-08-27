"""
Interface definition for the Analysis Engine Client.
Defines the contract for communication with the Analysis Engine Module.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IAnalysisEngineClient(ABC):
    """
    Interface for communication with the Analysis Engine Module.
    Defines operations for analyzing fermentation data and getting insights.
    """

    @abstractmethod
    async def analyze_sample(
        self,
        fermentation_id: int,
        sample_id: int,
        historical_context: bool = True
    ) -> Dict[str, Any]:
        """
        Analyzes a new sample in the context of its fermentation.

        Args:
            fermentation_id: ID of the fermentation
            sample_id: ID of the new sample to analyze
            historical_context: Whether to include historical analysis context

        Returns:
            Dict[str, Any]: Analysis results including:
                - measurements_valid: bool
                - trend_analysis: Dict with trend indicators
                - warnings: List of potential issues
                - recommendations: List of suggested actions

        Raises:
            AnalysisError: If analysis fails
            NetworkError: If communication with Analysis Engine fails
            NotFoundError: If fermentation_id or sample_id don't exist
        """
        pass

    @abstractmethod
    async def get_trend_analysis(
        self,
        fermentation_id: int,
        time_window_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyzes fermentation trends over time.

        Args:
            fermentation_id: ID of the fermentation
            time_window_hours: Optional window for analysis, default analyzes
            all data

        Returns:
            Dict[str, Any]: Trend analysis including:
                - glucose_trend: Glucose consumption rate
                - ethanol_trend: Ethanol production rate
                - temperature_stability: Temperature variation analysis
                - stage_assessment: Current fermentation stage
                - comparison: Comparison with expected patterns

        Raises:
            AnalysisError: If trend analysis fails
            NetworkError: If communication fails
            NotFoundError: If fermentation_id doesn't exist
        """
        pass

    @abstractmethod
    async def predict_completion(self, fermentation_id: int) -> Dict[str, Any]:
        """
        Predicts fermentation completion time and final parameters.

        Args:
            fermentation_id: ID of the fermentation

        Returns:
            Dict[str, Any]: Prediction results including:
                - estimated_completion_time: datetime
                - confidence_level: float
                - expected_final_ethanol: float
                - completion_risks: List of potential risks
                - optimization_suggestions: List of suggestions

        Raises:
            AnalysisError: If prediction fails
            NetworkError: If communication fails
            NotFoundError: If fermentation_id doesn't exist
            InsufficientDataError: If not enough data for prediction
        """
        pass

    @abstractmethod
    async def detect_anomalies(
        self, fermentation_id: int, sensitivity: str = "MEDIUM"
    ) -> List[Dict[str, Any]]:
        """
        Detects anomalies in fermentation patterns.

        Args:
            fermentation_id: ID of the fermentation
            sensitivity: Detection sensitivity ('LOW', 'MEDIUM', 'HIGH')

        Returns:
            List[Dict[str, Any]]: Detected anomalies, each containing:
                - type: Anomaly type
                - severity: Severity level
                - description: Detailed description
                - affected_parameters: List of affected measurements
                - suggested_actions: List of recommended actions

        Raises:
            AnalysisError: If anomaly detection fails
            NetworkError: If communication fails
            NotFoundError: If fermentation_id doesn't exist
            ValidationError: If sensitivity is invalid
        """
        pass

    @abstractmethod
    async def get_recommendations(
        self, fermentation_id: int, context_type: str = "CURRENT"
    ) -> List[Dict[str, Any]]:
        """
        Gets actionable recommendations based on fermentation state.

        Args:
            fermentation_id: ID of the fermentation
            context_type: Type of recommendations
            ('CURRENT', 'PREVENTIVE', 'OPTIMIZATION')

        Returns:
            List[Dict[str, Any]]: List of recommendations, each containing:
                - priority: Priority level
                - category: Recommendation category
                - description: Detailed description
                - rationale: Why this is recommended
                - expected_impact: Expected outcome if implemented
                - implementation_steps: How to implement

        Raises:
            AnalysisError: If recommendation generation fails
            NetworkError: If communication fails
            NotFoundError: If fermentation_id doesn't exist
            ValidationError: If context_type is invalid
        """
        pass
