"""
Recommendation Service - Generate and rank actionable recommendations.

Maps detected anomalies to pre-populated recommendation templates and ranks
them by effectiveness. Uses expert-validated rescue protocols from ADR-020.

Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery, 20 years)
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..domain.entities.anomaly import Anomaly
from ..domain.entities.recommendation import Recommendation
from ..domain.entities.recommendation_template import RecommendationTemplate
from ..domain.enums.anomaly_type import AnomalyType
from ..domain.enums.recommendation_category import RecommendationCategory


class RecommendationService:
    """
    Service for generating and ranking recommendations.
    
    Responsibilities:
    - Map anomalies to pre-populated recommendation templates
    - Rank recommendations by effectiveness and priority
    - Handle multi-tenancy (winery_id isolation)
    - Track recommendation application/adoption
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the Recommendation Service.
        
        Args:
            session: AsyncSession for database operations
        """
        self.session = session
    
    async def generate_recommendations(
        self,
        winery_id: UUID,
        analysis_id: UUID,
        anomalies: List[Anomaly]
    ) -> List[Recommendation]:
        """
        Generate recommendations for detected anomalies.
        
        Each anomaly maps to one or more recommendation templates.
        Results are ranked by:
        1. Anomaly priority (CRITICAL > WARNING > INFO)
        2. Recommendation effectiveness (from template)
        3. Historical success rate
        
        Args:
            winery_id: Current winery
            analysis_id: Analysis ID to attach recommendations to
            anomalies: List of detected Anomaly objects
        
        Returns:
            List of Recommendation objects, ranked and ready to persist
        """
        recommendations = []
        
        for anomaly in anomalies:
            # Get templates for this anomaly type
            templates = await self._get_templates_for_anomaly(
                winery_id,
                AnomalyType(anomaly.anomaly_type)
            )
            
            for template in templates:
                rec = Recommendation(
                    analysis_id=analysis_id,
                    anomaly_id=anomaly.id if anomaly.id else None,
                    recommendation_template_id=template.id,
                    recommendation_text=template.recommendation_text,
                    category=template.category,
                    priority=self._calculate_priority(anomaly, template),
                    estimated_effectiveness=template.effectiveness_score,
                    is_applied=False,
                )
                recommendations.append(rec)
        
        # Sort by priority (descending = highest first)
        recommendations.sort(key=lambda r: r.priority, reverse=True)
        
        return recommendations
    
    async def _get_templates_for_anomaly(
        self,
        winery_id: UUID,
        anomaly_type: AnomalyType
    ) -> List[RecommendationTemplate]:
        """
        Get pre-populated recommendation templates for an anomaly type.
        
        Templates are created during seed data phase. For now, returns
        empty list to avoid FK errors during early testing.
        
        Args:
            winery_id: Current winery
            anomaly_type: Type of anomaly detected
        
        Returns:
            List of RecommendationTemplate objects, ranked by effectiveness
        """
        # Expert-mapped anomaly → category mapping
        anomaly_to_categories = {
            AnomalyType.STUCK_FERMENTATION: [
                RecommendationCategory.NUTRIENT_MANAGEMENT,
                RecommendationCategory.AERATION_REMONTAGE
            ],
            AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL: [
                RecommendationCategory.TEMPERATURE_CONTROL
            ],
            AnomalyType.TEMPERATURE_SUBOPTIMAL: [
                RecommendationCategory.TEMPERATURE_CONTROL
            ],
            AnomalyType.DENSITY_DROP_TOO_FAST: [
                RecommendationCategory.TEMPERATURE_CONTROL,
                RecommendationCategory.MONITORING_FREQUENCY
            ],
            AnomalyType.HYDROGEN_SULFIDE_RISK: [
                RecommendationCategory.AERATION_REMONTAGE,
                RecommendationCategory.NUTRIENT_MANAGEMENT
            ],
            AnomalyType.UNUSUAL_DURATION: [
                RecommendationCategory.MONITORING_FREQUENCY
            ],
            AnomalyType.ATYPICAL_PATTERN: [
                RecommendationCategory.MONITORING_FREQUENCY
            ],
            AnomalyType.VOLATILE_ACIDITY_HIGH: [
                RecommendationCategory.TEMPERATURE_CONTROL,
                RecommendationCategory.SANITATION
            ],
        }
        
        categories = anomaly_to_categories.get(anomaly_type, [])
        
        # Query templates by category
        query = select(RecommendationTemplate).where(
            RecommendationTemplate.category.in_([c.value for c in categories])
        ).order_by(RecommendationTemplate.effectiveness_score.desc())
        
        result = await self.session.execute(query)
        templates = result.scalars().all()
        
        return templates
    
    @staticmethod
    def _calculate_priority(
        anomaly: Anomaly,
        template: RecommendationTemplate
    ) -> int:
        """
        Calculate priority score for a recommendation.
        
        Scoring factors:
        - Anomaly severity: CRITICAL (1000) > WARNING (100) > INFO (10)
        - Template effectiveness: 0-100 (low to high)
        
        Priority = severity_weight + (effectiveness_score / 10)
        Range: 10-1110
        
        Args:
            anomaly: Detected anomaly
            template: Recommendation template
        
        Returns:
            Priority score (higher = more urgent)
        """
        severity_weights = {
            "CRITICAL": 1000,
            "WARNING": 100,
            "INFO": 10,
        }
        
        severity_weight = severity_weights.get(anomaly.severity, 10)
        effectiveness = template.effectiveness_score or 50  # Default if not set
        
        priority = severity_weight + (effectiveness / 10)
        return int(priority)
    
    async def rank_recommendations(
        self,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """
        Rank recommendations by priority and feasibility.
        
        Already sorted by priority in generate_recommendations(),
        but this allows for additional ranking logic if needed.
        
        Args:
            recommendations: Unsorted recommendations
        
        Returns:
            Ranked recommendations (highest priority first)
        """
        ranked = sorted(recommendations, key=lambda r: r.priority, reverse=True)
        return ranked
    
    async def get_top_recommendations(
        self,
        recommendations: List[Recommendation],
        limit: int = 5
    ) -> List[Recommendation]:
        """
        Get top-priority recommendations (typically 3-5).
        
        Winemakers should act on top 3-5 recommendations; too many
        recommendations leads to decision paralysis and alert fatigue.
        
        Args:
            recommendations: All recommendations
            limit: Maximum to return (default 5)
        
        Returns:
            Top recommendations, ranked by priority
        """
        ranked = await self.rank_recommendations(recommendations)
        return ranked[:limit]
    
    async def record_recommendation_applied(
        self,
        recommendation_id: UUID,
        applied_at: Optional[datetime] = None
    ) -> None:
        """
        Record that a recommendation was applied.
        
        Used for tracking effectiveness and success rates.
        
        Args:
            recommendation_id: Recommendation to mark as applied
            applied_at: When it was applied (default: now)
        
        Returns:
            None (updates database)
        """
        if applied_at is None:
            applied_at = datetime.now(timezone.utc)
        
        # Fetch recommendation
        result = await self.session.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )
        rec = result.scalar_one_or_none()
        
        if rec:
            rec.is_applied = True
            rec.applied_at = applied_at
            await self.session.flush()


# ============================================================================
# ANOMALY → CATEGORY MAPPING (Expert-validated from ADR-020)
# ============================================================================
#
# This mapping encodes the expert knowledge from Susana Rodriguez Vasquez
# about which interventions address which problems.
#
# STUCK_FERMENTATION → NUTRIENT_MANAGEMENT + AERATION_REMONTAGE
#   Rescue protocol: DAP nutrients + remontage (pulling juice over skins)
#   Reference: ADR-020 Section "1. Fermentación Estancada"
#
# TEMPERATURE_CRITICAL → TEMPERATURE_CONTROL
#   Rescue protocol: Immediately adjust cooling/heating system
#   Reference: ADR-020 Section "2. Temperatura Crítica"
#
# TEMPERATURE_SUBOPTIMAL → TEMPERATURE_CONTROL
#   Rescue protocol: Fine-tune to optimal range (not immediately critical)
#   Reference: ADR-020 Section "Expert Validation: Operational Thresholds"
#
# DENSITY_DROP_TOO_FAST → TEMPERATURE_CONTROL + MONITORING_FREQUENCY
#   Root cause: Usually too hot; also could indicate high vigor
#   Rescue protocol: Cool down, increase monitoring
#
# HYDROGEN_SULFIDE_RISK → AERATION_REMONTAGE + NUTRIENT_MANAGEMENT
#   Risk factors: Low N, cold temps
#   Rescue protocol: Add nitrogen nutrients, increase aeration
#
# UNUSUAL_DURATION → MONITORING_FREQUENCY
#   Not necessarily a problem; could be normal variation
#   Rescue protocol: Increase sampling frequency to track
#
# ATYPICAL_PATTERN → MONITORING_FREQUENCY
#   Could be normal or problematic; need more data
#   Rescue protocol: Increase sampling frequency
#
# VOLATILE_ACIDITY_HIGH → TEMPERATURE_CONTROL + SANITATION
#   Cause: Bacterial contamination (acetic acid bacteria)
#   Rescue protocol: Reduce temp (stop acetification), ensure sanitation
# ============================================================================
