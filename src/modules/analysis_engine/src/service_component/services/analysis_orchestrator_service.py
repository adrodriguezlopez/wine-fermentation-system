"""
Analysis Orchestrator Service - Coordinate the complete analysis workflow.

This is the main service that orchestrates the analysis pipeline:
1. Comparison Service: Find historical context
2. Anomaly Detection Service: Identify problems
3. Recommendation Service: Generate actionable fixes

The orchestrator manages the Analysis aggregate root and coordinates
all sub-services to produce a complete analysis result.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.entities.recommendation import Recommendation
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus
from src.modules.analysis_engine.src.domain.value_objects.confidence_level import ConfidenceLevel
from src.modules.analysis_engine.src.service_component.services.comparison_service import ComparisonService
from src.modules.analysis_engine.src.service_component.services.anomaly_detection_service import AnomalyDetectionService
from src.modules.analysis_engine.src.service_component.services.recommendation_service import RecommendationService


class AnalysisOrchestratorService:
    """
    Orchestrates the complete fermentation analysis workflow.
    
    Workflow:
    1. Initialize Analysis (PENDING status)
    2. Call Comparison Service → build historical context
    3. Call Anomaly Detection Service → detect problems
    4. Call Recommendation Service → generate fixes
    5. Update Analysis (COMPLETE status)
    6. Persist all entities
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the Analysis Orchestrator.
        
        Args:
            session: AsyncSession for database operations
        """
        self.session = session
        self.comparison = ComparisonService(session)
        self.anomaly_detection = AnomalyDetectionService(session)
        self.recommendation = RecommendationService(session)
    
    async def execute_analysis(
        self,
        winery_id: UUID,
        fermentation_id: UUID,
        current_density: float,
        temperature_celsius: float,
        variety: str,
        fruit_origin_id: Optional[UUID] = None,
        starting_brix: Optional[float] = None,
        days_fermenting: float = 0.0,
        previous_densities: Optional[list] = None,
    ) -> Analysis:
        """
        Execute a complete fermentation analysis.
        
        This is the main entry point. It orchestrates all sub-services
        and returns a fully-populated Analysis with anomalies and recommendations.
        
        Args:
            winery_id: Current winery
            fermentation_id: Fermentation to analyze
            current_density: Current density reading (g/L)
            temperature_celsius: Current temperature
            variety: Grape variety
            fruit_origin_id: Fruit origin (optional, for similarity)
            starting_brix: Starting brix (optional, for similarity)
            days_fermenting: Days since fermentation start
            previous_densities: List of (datetime, float) density readings
        
        Returns:
            Complete Analysis object with anomalies and recommendations
        
        Raises:
            WineryAccessDenied: If attempting cross-winery access
        """
        # Step 1: Create and initialize Analysis
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.IN_PROGRESS.value,
            analyzed_at=datetime.now(timezone.utc),
            comparison_result={},  # Will populate below
            confidence_level={},  # Will populate below
            historical_samples_count=0,
        )
        
        try:
            # Step 2: Run Comparison Service (find historical context)
            similar_ids, total_count = await self.comparison.find_similar_fermentations(
                winery_id=winery_id,
                fermentation_id=fermentation_id,
                variety=variety,
                fruit_origin_id=fruit_origin_id,
                starting_brix=starting_brix,
            )
            
            comparison_result = await self.comparison.build_comparison_result(
                winery_id=winery_id,
                fermentation_id=fermentation_id,
                similar_fermentation_ids=similar_ids,
            )
            analysis.comparison_result = comparison_result.to_dict()
            analysis.historical_samples_count = len(similar_ids)
            
            # Step 3: Run Anomaly Detection Service
            anomalies = await self.anomaly_detection.detect_all_anomalies(
                fermentation_id=fermentation_id,
                current_density=current_density,
                temperature_celsius=temperature_celsius,
                variety=variety,
                days_fermenting=days_fermenting,
                previous_densities=previous_densities or [],
                historical_avg_duration=comparison_result.average_duration_days,
                historical_densities_band=None,  # TODO: fetch from historical data
            )
            
            # Attach anomalies to analysis
            analysis.anomalies = anomalies
            
            # Step 4: Run Recommendation Service
            recommendations = await self.recommendation.generate_recommendations(
                winery_id=winery_id,
                analysis_id=analysis.id,  # type: ignore
                anomalies=anomalies,
            )
            
            # Attach recommendations to analysis
            analysis.recommendations = recommendations
            
            # Step 5: Calculate confidence level
            confidence = self._calculate_confidence(
                historical_count=len(similar_ids),
                anomaly_count=len(anomalies),
                recommendation_count=len(recommendations),
            )
            analysis.confidence_level = confidence.to_dict()
            
            # Step 6: Mark complete
            analysis.status = AnalysisStatus.COMPLETED.value
            
        except Exception as e:
            # Mark as failed if anything goes wrong
            analysis.status = AnalysisStatus.FAILED.value
            raise
        
        return analysis
    
    async def get_analysis(
        self,
        analysis_id: UUID,
        winery_id: UUID
    ) -> Optional[Analysis]:
        """
        Retrieve a saved analysis (with multi-tenancy check).
        
        Args:
            analysis_id: Analysis to retrieve
            winery_id: Current winery (for security)
        
        Returns:
            Analysis object with all relationships, or None if not found
        
        Raises:
            WineryAccessDenied: If analysis belongs to different winery
        """
        result = await self.session.execute(
            select(Analysis).where(Analysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()
        
        if analysis is None:
            return None
        
        if analysis.winery_id != winery_id:
            from src.shared.domain.errors import CrossWineryAccessDenied
            raise CrossWineryAccessDenied(
                f"Analysis {analysis_id} belongs to winery {analysis.winery_id}, "
                f"not {winery_id}"
            )
        
        return analysis
    
    async def get_fermentation_analyses(
        self,
        fermentation_id: UUID,
        winery_id: UUID,
        limit: int = 10
    ) -> list[Analysis]:
        """
        Get analysis history for a fermentation.
        
        Args:
            fermentation_id: Fermentation to get history for
            winery_id: Current winery
            limit: Maximum results
        
        Returns:
            List of Analysis objects, most recent first
        """
        result = await self.session.execute(
            select(Analysis)
            .where(
                Analysis.fermentation_id == fermentation_id,
                Analysis.winery_id == winery_id,
            )
            .order_by(Analysis.analyzed_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    def _calculate_confidence(
        historical_count: int,
        anomaly_count: int,
        recommendation_count: int,
    ) -> ConfidenceLevel:
        """
        Calculate confidence levels for the analysis.
        
        Confidence is lower when:
        - Few historical samples (0-2 = low, 3-5 = medium, 6+ = high)
        - Many anomalies detected (suggests noisy detection)
        - Few recommendations (suggests incomplete analysis)
        
        Args:
            historical_count: Number of similar historical fermentations
            anomaly_count: Number of anomalies detected
            recommendation_count: Number of recommendations generated
        
        Returns:
            ConfidenceLevel value object
        """
        # Historical confidence (based on sample size)
        if historical_count == 0:
            historical_confidence = 0.3
        elif historical_count <= 2:
            historical_confidence = 0.5
        elif historical_count <= 5:
            historical_confidence = 0.7
        else:
            historical_confidence = 0.9
        
        # Detection confidence (fewer is often better - less "crying wolf")
        if anomaly_count == 0:
            detection_confidence = 0.8
        elif anomaly_count == 1:
            detection_confidence = 0.9
        elif anomaly_count <= 3:
            detection_confidence = 0.7
        else:
            detection_confidence = 0.5
        
        # Recommendation confidence (paired with anomalies)
        if recommendation_count == 0 and anomaly_count == 0:
            recommendation_confidence = 0.8  # All normal
        elif recommendation_count > 0 and anomaly_count > 0:
            recommendation_confidence = 0.85
        else:
            recommendation_confidence = 0.6
        
        # Overall confidence = weighted average (historical data weighted heavily)
        overall_confidence = (
            historical_confidence * 0.7 +
            detection_confidence * 0.2 +
            recommendation_confidence * 0.1
        )
        
        return ConfidenceLevel(
            overall_confidence=round(overall_confidence, 2),
            historical_data_confidence=round(historical_confidence, 2),
            detection_algorithm_confidence=round(detection_confidence, 2),
            recommendation_confidence=round(recommendation_confidence, 2),
            sample_size=historical_count,
            anomalies_detected=anomaly_count,
            recommendations_generated=recommendation_count,
        )
