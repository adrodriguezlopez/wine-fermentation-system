"""
Anomaly Detection Service - Identify problems in fermentation.

Detects 8 types of anomalies using expert-validated thresholds from ADR-020.
Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery, 20 years experience)

This service combines:
- Statistical analysis (density trends, volatility)
- Expert thresholds (temperature ranges, duration percentiles)
- Historical comparison (deviation from ±2σ band)
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
from src.modules.analysis_engine.src.domain.value_objects.deviation_score import DeviationScore


class AnomalyDetectionService:
    """
    Service for detecting anomalies in fermentation data.
    
    Implements 8 anomaly types with expert-validated thresholds:
    
    CRITICAL (Priority 1):
    - STUCK_FERMENTATION: Density static for 0.5-1 day, <1.0 pt change
    - TEMPERATURE_OUT_OF_RANGE_CRITICAL: <15°C or >32°C
    - VOLATILE_ACIDITY_HIGH: Acetification detected
    
    WARNING (Priority 2):
    - DENSITY_DROP_TOO_FAST: >15% in 24 hours
    - HYDROGEN_SULFIDE_RISK: Low N, cold temps
    - TEMPERATURE_SUBOPTIMAL: Off-spec but not critical
    
    INFO (Priority 3):
    - UNUSUAL_DURATION: Outside 10-90 percentile
    - ATYPICAL_PATTERN: Outside ±2σ band vs historical
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the Anomaly Detection Service.
        
        Args:
            session: AsyncSession for database operations
        """
        self.session = session
    
    async def detect_all_anomalies(
        self,
        fermentation_id: UUID,
        current_density: float,
        temperature_celsius: float,
        variety: str,
        days_fermenting: float,
        previous_densities: List[Tuple[datetime, float]],
        historical_avg_duration: Optional[float] = None,
        historical_densities_band: Optional[Dict] = None,
    ) -> List[Anomaly]:
        """
        Run all anomaly detection algorithms.
        
        Args:
            fermentation_id: Current fermentation ID
            current_density: Current density reading (g/L)
            temperature_celsius: Current temperature
            variety: Grape variety (determines temperature thresholds)
            days_fermenting: Days since fermentation start
            previous_densities: List of (timestamp, density) tuples
            historical_avg_duration: Average duration from similar fermentations
            historical_densities_band: Statistical band (mean, stdev)
        
        Returns:
            List of detected Anomaly objects (empty if no issues)
        """
        anomalies = []
        
        # Run each detection algorithm
        stuck = await self.detect_stuck_fermentation(
            current_density,
            previous_densities,
            days_fermenting
        )
        if stuck:
            anomalies.append(stuck)
        
        temp_critical = self.detect_temperature_critical(temperature_celsius, variety)
        if temp_critical:
            anomalies.append(temp_critical)
        
        temp_suboptimal = self.detect_temperature_suboptimal(temperature_celsius, variety)
        if temp_suboptimal and not temp_critical:  # Don't double-report
            anomalies.append(temp_suboptimal)
        
        fast_drop = self.detect_density_drop_too_fast(previous_densities)
        if fast_drop:
            anomalies.append(fast_drop)
        
        h2s_risk = self.detect_hydrogen_sulfide_risk(temperature_celsius, days_fermenting)
        if h2s_risk:
            anomalies.append(h2s_risk)
        
        # TODO: volatile_acidity detection requires chemical data not yet in schema
        
        if historical_avg_duration:
            unusual = self.detect_unusual_duration(days_fermenting, historical_avg_duration)
            if unusual:
                anomalies.append(unusual)
        
        if historical_densities_band:
            atypical = self.detect_atypical_pattern(
                current_density,
                historical_densities_band
            )
            if atypical:
                anomalies.append(atypical)
        
        return anomalies
    
    async def detect_stuck_fermentation(
        self,
        current_density: float,
        previous_densities: List[Tuple[datetime, float]],
        days_fermenting: float
    ) -> Optional[Anomaly]:
        """
        Detect fermentation stalling before reaching dry wine (<2 g/L).
        
        Expert validation (Susana Rodriguez Vasquez):
        - Reds: 0.5 days without significant density change
        - Whites: 1.0 day without significant density change
        - Threshold: Change < 1.0 density points
        - Terminal condition: Density < 2.0 g/L = fermentation stalled
        
        Args:
            current_density: Current density reading
            previous_densities: Historical density readings with timestamps
            days_fermenting: Days since fermentation start
        
        Returns:
            Anomaly object if stuck detected, None otherwise
        """
        if not previous_densities or len(previous_densities) < 2:
            return None
        
        # Sort by timestamp ascending
        sorted_densities = sorted(previous_densities, key=lambda x: x[0])
        recent_start_idx = max(0, len(sorted_densities) - 3)  # Last 2-3 readings
        
        recent_readings = sorted_densities[recent_start_idx:]
        if len(recent_readings) < 2:
            return None
        
        # Calculate change over recent period
        oldest_recent = recent_readings[0][1]
        newest_recent = recent_readings[-1][1]
        density_change = abs(newest_recent - oldest_recent)
        time_span = (recent_readings[-1][0] - recent_readings[0][0]).total_seconds() / 86400
        
        # Check if stuck: minimal change over significant time
        is_stuck = density_change < 1.0 and time_span > 0.5 and current_density > 2.0
        
        if not is_stuck:
            return None
        
        deviation = DeviationScore(
            deviation=density_change,
            threshold=1.0,
            magnitude="LOW",
            details={
                "time_span_days": round(time_span, 2),
                "density_change_points": round(density_change, 2),
                "current_density": current_density,
            }
        )
        
        return Anomaly(
            anomaly_type=AnomalyType.STUCK_FERMENTATION.value,
            severity=SeverityLevel.CRITICAL.value,
            description=f"Fermentación estancada: densidad sin cambio por {time_span:.1f} días. "
                       f"Cambio: {density_change:.2f} puntos, umbral: 1.0",
            deviation_score=deviation.to_dict(),
            is_resolved=False
        )
    
    def detect_temperature_critical(
        self,
        temperature_celsius: float,
        variety: str
    ) -> Optional[Anomaly]:
        """
        Detect temperature outside absolute critical limits.
        
        Expert validation (Susana Rodriguez Vasquez):
        - Reds: 23.9-32.2°C (75-90°F) - CRITICAL boundaries
        - Whites: 11.7-16.7°C (53-62°F) - CRITICAL boundaries
        - Rosés: 11.7-16.7°C (53-62°F) - CRITICAL boundaries
        
        Outside these ranges: Yeast death, severe off-flavors
        
        Args:
            temperature_celsius: Current temperature
            variety: Grape variety to determine thresholds
        
        Returns:
            Anomaly object if critical temp detected, None otherwise
        """
        # Determine critical limits by variety
        if variety.upper() in ("CABERNET SAUVIGNON", "MERLOT", "PINOT NOIR", "ZINFANDEL"):
            min_temp = 23.9  # 75°F
            max_temp = 32.2  # 90°F
            variety_type = "red"
        else:
            # Default: whites and rosés
            min_temp = 11.7  # 53°F
            max_temp = 16.7  # 62°F
            variety_type = "white/rosé"
        
        is_critical = temperature_celsius < min_temp or temperature_celsius > max_temp
        if not is_critical:
            return None
        
        deviation = DeviationScore(
            deviation=temperature_celsius,
            threshold=min_temp if temperature_celsius < min_temp else max_temp,
            magnitude="HIGH",
            details={
                "variety_type": variety_type,
                "min_critical": min_temp,
                "max_critical": max_temp,
                "current_temp": round(temperature_celsius, 1),
            }
        )
        
        direction = "too cold" if temperature_celsius < min_temp else "too hot"
        return Anomaly(
            anomaly_type=AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.value,
            severity=SeverityLevel.CRITICAL.value,
            description=f"Temperatura fuera de límites críticos ({direction}): "
                       f"{temperature_celsius:.1f}°C. Rango: {min_temp}-{max_temp}°C",
            deviation_score=deviation.to_dict(),
            is_resolved=False
        )
    
    def detect_temperature_suboptimal(
        self,
        temperature_celsius: float,
        variety: str
    ) -> Optional[Anomaly]:
        """
        Detect temperature outside optimal (but not critical) range.
        
        Expert validation (Susana Rodriguez Vasquez):
        - Reds: 24-30°C optimal (not ideal if <24 or >30)
        - Whites: 12-16°C optimal (not ideal if <12 or >16)
        - Still allows yeast to function but affects flavor profile
        
        Args:
            temperature_celsius: Current temperature
            variety: Grape variety to determine thresholds
        
        Returns:
            Anomaly object if suboptimal, None otherwise
        """
        # Determine optimal ranges
        if variety.upper() in ("CABERNET SAUVIGNON", "MERLOT", "PINOT NOIR", "ZINFANDEL"):
            min_opt = 24.0
            max_opt = 30.0
        else:
            min_opt = 12.0
            max_opt = 16.0
        
        is_suboptimal = temperature_celsius < min_opt or temperature_celsius > max_opt
        if not is_suboptimal:
            return None
        
        deviation = DeviationScore(
            deviation=temperature_celsius,
            threshold=(min_opt + max_opt) / 2,
            magnitude="MEDIUM",
            details={
                "min_optimal": min_opt,
                "max_optimal": max_opt,
                "current_temp": round(temperature_celsius, 1),
            }
        )
        
        return Anomaly(
            anomaly_type=AnomalyType.TEMPERATURE_SUBOPTIMAL.value,
            severity=SeverityLevel.WARNING.value,
            description=f"Temperatura subóptima: {temperature_celsius:.1f}°C. "
                       f"Rango óptimo: {min_opt}-{max_opt}°C",
            deviation_score=deviation.to_dict(),
            is_resolved=False
        )
    
    def detect_density_drop_too_fast(
        self,
        previous_densities: List[Tuple[datetime, float]]
    ) -> Optional[Anomaly]:
        """
        Detect fermentation proceeding too fast (>15% density drop in 24h).
        
        Expert validation (Susana Rodriguez Vasquez):
        - Excessive vigor causes:
          * Aroma loss (volatile compounds escape)
          * Temperature spike (exothermic)
          * Incomplete fermentation (yeast dies)
        
        Threshold: >15% change in 24 hours
        
        Args:
            previous_densities: List of (timestamp, density) readings
        
        Returns:
            Anomaly object if too fast, None otherwise
        """
        if not previous_densities or len(previous_densities) < 2:
            return None
        
        sorted_densities = sorted(previous_densities, key=lambda x: x[0])
        
        # Find readings ~24 hours apart
        for i in range(len(sorted_densities) - 1):
            time_diff = (sorted_densities[i + 1][0] - sorted_densities[i][0]).total_seconds() / 3600
            
            if 20 <= time_diff <= 28:  # ~24 hours
                density_1 = sorted_densities[i][1]
                density_2 = sorted_densities[i + 1][1]
                
                percent_change = abs(density_2 - density_1) / max(density_1, 0.1) * 100
                
                if percent_change > 15.0:
                    deviation = DeviationScore(
                        deviation=percent_change,
                        threshold=15.0,
                        magnitude="MEDIUM",
                        details={
                            "time_span_hours": round(time_diff, 1),
                            "percent_change": round(percent_change, 1),
                            "density_start": round(density_1, 2),
                            "density_end": round(density_2, 2),
                        }
                    )
                    
                    return Anomaly(
                        anomaly_type=AnomalyType.DENSITY_DROP_TOO_FAST.value,
                        severity=SeverityLevel.WARNING.value,
                        description=f"Caída de densidad demasiado rápida: {percent_change:.1f}% en 24h. "
                                   f"Umbral: 15%",
                        deviation_score=deviation.to_dict(),
                        is_resolved=False
                    )
        
        return None
    
    def detect_hydrogen_sulfide_risk(
        self,
        temperature_celsius: float,
        days_fermenting: float
    ) -> Optional[Anomaly]:
        """
        Detect conditions favorable for H₂S (hydrogen sulfide) development.
        
        Expert validation (Susana Rodriguez Vasquez):
        - H2S causes: Rotten egg smell, metallic taste
        - Risk factors: Low nitrogen + cold temperature
        - Detection: Temperature <18°C in first 10 days (without chemical data)
        
        Args:
            temperature_celsius: Current temperature
            days_fermenting: Days since fermentation start
        
        Returns:
            Anomaly object if risk detected, None otherwise
        """
        # H2S risk: cold fermentation early on
        is_risk = temperature_celsius < 18.0 and days_fermenting < 10.0
        
        if not is_risk:
            return None
        
        deviation = DeviationScore(
            deviation=temperature_celsius,
            threshold=18.0,
            magnitude="MEDIUM",
            details={
                "critical_period_days": min(days_fermenting, 10),
                "current_temp": round(temperature_celsius, 1),
            }
        )
        
        return Anomaly(
            anomaly_type=AnomalyType.HYDROGEN_SULFIDE_RISK.value,
            severity=SeverityLevel.WARNING.value,
            description=f"Riesgo de H₂S: temperatura baja ({temperature_celsius:.1f}°C) "
                       f"en fase crítica de fermentación ({days_fermenting:.1f} días). "
                       f"Considerar aireación.",
            deviation_score=deviation.to_dict(),
            is_resolved=False
        )
    
    def detect_unusual_duration(
        self,
        days_fermenting: float,
        historical_avg_duration: float
    ) -> Optional[Anomaly]:
        """
        Detect fermentation duration outside typical range (10-90 percentile).
        
        Approximation: Use ±1.5 days from average as proxy for 10-90 percentile
        
        Args:
            days_fermenting: Current duration in days
            historical_avg_duration: Average from historical similar fermentations
        
        Returns:
            Anomaly object if unusual, None otherwise
        """
        if not historical_avg_duration or historical_avg_duration <= 0:
            return None

        tolerance = 1.5  # Approximation for 10-90 percentile
        too_long = days_fermenting > historical_avg_duration + tolerance
        # Only flag "too short" when fermentation has lasted long enough to be considered
        # potentially complete (at least 60% of the expected average duration)
        too_short = (
            days_fermenting >= historical_avg_duration * 0.6 and
            days_fermenting < historical_avg_duration - tolerance
        )
        is_unusual = too_long or too_short
        
        if not is_unusual:
            return None
        
        deviation = DeviationScore(
            deviation=days_fermenting,
            threshold=historical_avg_duration,
            magnitude="LOW",
            details={
                "current_days": round(days_fermenting, 1),
                "historical_avg_days": round(historical_avg_duration, 1),
                "tolerance_days": tolerance,
            }
        )
        
        return Anomaly(
            anomaly_type=AnomalyType.UNUSUAL_DURATION.value,
            severity=SeverityLevel.INFO.value,
            description=f"Duración atípica: {days_fermenting:.1f} días vs histórico {historical_avg_duration:.1f} días. "
                       f"Informativo - observar evolución.",
            deviation_score=deviation.to_dict(),
            is_resolved=False
        )
    
    def detect_atypical_pattern(
        self,
        current_density: float,
        historical_densities_band: Dict
    ) -> Optional[Anomaly]:
        """
        Detect density reading outside ±2σ of historical pattern.
        
        Args:
            current_density: Current density reading
            historical_densities_band: Dict with 'mean' and 'stdev' keys
        
        Returns:
            Anomaly object if outside band, None otherwise
        """
        if not historical_densities_band or "mean" not in historical_densities_band:
            return None
        
        mean = historical_densities_band["mean"]
        stdev = historical_densities_band.get("stdev", 0)
        
        if stdev <= 0:
            return None
        
        # Calculate z-score
        z_score = abs(current_density - mean) / stdev
        is_atypical = z_score > 2.0
        
        if not is_atypical:
            return None
        
        deviation = DeviationScore(
            deviation=current_density,
            threshold=mean,
            magnitude="MEDIUM",
            details={
                "z_score": round(z_score, 2),
                "current_density": round(current_density, 2),
                "historical_mean": round(mean, 2),
                "standard_deviations": round(stdev, 2),
            }
        )
        
        return Anomaly(
            anomaly_type=AnomalyType.ATYPICAL_PATTERN.value,
            severity=SeverityLevel.INFO.value,
            description=f"Patrón atípico: densidad {current_density:.2f} está fuera de banda histórica "
                       f"(z-score {z_score:.2f}). Investigar evolución.",
            deviation_score=deviation.to_dict(),
            is_resolved=False
        )
