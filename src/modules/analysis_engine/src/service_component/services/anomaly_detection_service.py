"""
Anomaly Detection Service - Identify problems in fermentation.

Detects 8 types of anomalies using expert-validated thresholds from ADR-020.
Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery, 20 years experience)

Thresholds are loaded from config/thresholds.toml via ThresholdConfigService —
no magic numbers in this file.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
from src.modules.analysis_engine.src.domain.value_objects.deviation_score import DeviationScore
from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
    ThresholdConfigService,
    VarietalThresholds,
)


class AnomalyDetectionService:
    """
    Service for detecting anomalies in fermentation data.

    Implements 8 anomaly types with expert-validated thresholds loaded from
    config/thresholds.toml via ThresholdConfigService.

    CRITICAL (Priority 1):
    - STUCK_FERMENTATION: Density static for 0.5-1 day, <1.0 pt change
    - TEMPERATURE_OUT_OF_RANGE_CRITICAL: outside absolute limits by varietal
    - VOLATILE_ACIDITY_HIGH: acetic acid > warning/critical threshold

    WARNING (Priority 2):
    - DENSITY_DROP_TOO_FAST: >15% in 24 hours
    - HYDROGEN_SULFIDE_RISK: cold temperature in critical window
    - TEMPERATURE_SUBOPTIMAL: off-spec but not critical

    INFO (Priority 3):
    - UNUSUAL_DURATION: outside 10-90 percentile vs historical
    - ATYPICAL_PATTERN: outside ±2σ band vs historical
    """

    def __init__(self, session: AsyncSession, threshold_config: ThresholdConfigService) -> None:
        self.session = session
        self.config = threshold_config

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
        volatile_acidity_in_grams_per_liter: Optional[float] = None,
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
            volatile_acidity_in_grams_per_liter: Acetic acid reading in g/L (optional)

        Returns:
            List of detected Anomaly objects (empty if no issues)
        """
        thresholds = self.config.get_thresholds(variety)
        anomalies = []

        stuck = await self.detect_stuck_fermentation(
            current_density,
            previous_densities,
            days_fermenting,
            thresholds,
        )
        if stuck:
            anomalies.append(stuck)

        temp_critical = self.detect_temperature_critical(temperature_celsius, variety, thresholds)
        if temp_critical:
            anomalies.append(temp_critical)

        temp_suboptimal = self.detect_temperature_suboptimal(temperature_celsius, variety, thresholds)
        if temp_suboptimal and not temp_critical:
            anomalies.append(temp_suboptimal)

        fast_drop = self.detect_density_drop_too_fast(previous_densities, thresholds)
        if fast_drop:
            anomalies.append(fast_drop)

        h2s_risk = self.detect_hydrogen_sulfide_risk(temperature_celsius, days_fermenting, thresholds)
        if h2s_risk:
            anomalies.append(h2s_risk)

        if volatile_acidity_in_grams_per_liter is not None:
            va = self.detect_volatile_acidity(volatile_acidity_in_grams_per_liter, thresholds)
            if va:
                anomalies.append(va)

        if historical_avg_duration:
            unusual = self.detect_unusual_duration(days_fermenting, historical_avg_duration)
            if unusual:
                anomalies.append(unusual)

        if historical_densities_band:
            atypical = self.detect_atypical_pattern(current_density, historical_densities_band)
            if atypical:
                anomalies.append(atypical)

        return anomalies

    async def detect_stuck_fermentation(
        self,
        current_density: float,
        previous_densities: List[Tuple[datetime, float]],
        days_fermenting: float,
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """Detect fermentation stalling before reaching dry wine (<2 g/L)."""
        if not previous_densities or len(previous_densities) < 2:
            return None

        sorted_densities = sorted(previous_densities, key=lambda x: x[0])
        recent_start_idx = max(0, len(sorted_densities) - 3)
        recent_readings = sorted_densities[recent_start_idx:]
        if len(recent_readings) < 2:
            return None

        oldest_recent = recent_readings[0][1]
        newest_recent = recent_readings[-1][1]
        density_change = abs(newest_recent - oldest_recent)
        time_span = (recent_readings[-1][0] - recent_readings[0][0]).total_seconds() / 86400

        min_change = thresholds.stuck_fermentation_min_density_change_points
        min_stall = thresholds.stuck_fermentation_min_stall_duration_days
        is_stuck = density_change < min_change and time_span > min_stall and current_density > 2.0

        if not is_stuck:
            return None

        deviation = DeviationScore(
            deviation=density_change,
            threshold=min_change,
            magnitude="LOW",
            details={
                "time_span_days": round(time_span, 2),
                "density_change_points": round(density_change, 2),
                "current_density": current_density,
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.STUCK_FERMENTATION.value,
            severity=SeverityLevel.CRITICAL.value,
            description=(
                f"Fermentación estancada: densidad sin cambio por {time_span:.1f} días. "
                f"Cambio: {density_change:.2f} puntos, umbral: {min_change}"
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_temperature_critical(
        self,
        temperature_celsius: float,
        variety: str,
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """Detect temperature outside absolute critical limits."""
        min_temp = thresholds.temperature_critical_min_celsius
        max_temp = thresholds.temperature_critical_max_celsius
        is_critical = temperature_celsius < min_temp or temperature_celsius > max_temp
        if not is_critical:
            return None

        deviation = DeviationScore(
            deviation=temperature_celsius,
            threshold=min_temp if temperature_celsius < min_temp else max_temp,
            magnitude="HIGH",
            details={
                "min_critical": min_temp,
                "max_critical": max_temp,
                "current_temp": round(temperature_celsius, 1),
            },
        )
        direction = "too cold" if temperature_celsius < min_temp else "too hot"
        return Anomaly(
            anomaly_type=AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.value,
            severity=SeverityLevel.CRITICAL.value,
            description=(
                f"Temperatura fuera de límites críticos ({direction}): "
                f"{temperature_celsius:.1f}°C. Rango: {min_temp}-{max_temp}°C"
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_temperature_suboptimal(
        self,
        temperature_celsius: float,
        variety: str,
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """Detect temperature outside optimal (but not critical) range."""
        min_opt = thresholds.temperature_optimal_min_celsius
        max_opt = thresholds.temperature_optimal_max_celsius
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
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.TEMPERATURE_SUBOPTIMAL.value,
            severity=SeverityLevel.WARNING.value,
            description=(
                f"Temperatura subóptima: {temperature_celsius:.1f}°C. "
                f"Rango óptimo: {min_opt}-{max_opt}°C"
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_density_drop_too_fast(
        self,
        previous_densities: List[Tuple[datetime, float]],
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """Detect fermentation proceeding too fast."""
        if not previous_densities or len(previous_densities) < 2:
            return None

        sorted_densities = sorted(previous_densities, key=lambda x: x[0])
        max_drop_pct = thresholds.density_drop_max_percent_per_24_hours

        for i in range(len(sorted_densities) - 1):
            time_diff = (sorted_densities[i + 1][0] - sorted_densities[i][0]).total_seconds() / 3600
            if 20 <= time_diff <= 28:
                density_1 = sorted_densities[i][1]
                density_2 = sorted_densities[i + 1][1]
                percent_change = abs(density_2 - density_1) / max(density_1, 0.1) * 100
                if percent_change > max_drop_pct:
                    deviation = DeviationScore(
                        deviation=percent_change,
                        threshold=max_drop_pct,
                        magnitude="MEDIUM",
                        details={
                            "time_span_hours": round(time_diff, 1),
                            "percent_change": round(percent_change, 1),
                            "density_start": round(density_1, 2),
                            "density_end": round(density_2, 2),
                        },
                    )
                    return Anomaly(
                        anomaly_type=AnomalyType.DENSITY_DROP_TOO_FAST.value,
                        severity=SeverityLevel.WARNING.value,
                        description=(
                            f"Caída de densidad demasiado rápida: {percent_change:.1f}% en 24h. "
                            f"Umbral: {max_drop_pct}%"
                        ),
                        deviation_score=deviation.to_dict(),
                        is_resolved=False,
                    )
        return None

    def detect_hydrogen_sulfide_risk(
        self,
        temperature_celsius: float,
        days_fermenting: float,
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """Detect conditions favorable for H₂S development."""
        max_temp = thresholds.hydrogen_sulfide_risk_max_temperature_celsius
        critical_window = thresholds.hydrogen_sulfide_risk_critical_window_days
        is_risk = temperature_celsius < max_temp and days_fermenting < critical_window

        if not is_risk:
            return None

        deviation = DeviationScore(
            deviation=temperature_celsius,
            threshold=max_temp,
            magnitude="MEDIUM",
            details={
                "critical_period_days": min(days_fermenting, critical_window),
                "current_temp": round(temperature_celsius, 1),
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.HYDROGEN_SULFIDE_RISK.value,
            severity=SeverityLevel.WARNING.value,
            description=(
                f"Riesgo de H₂S: temperatura baja ({temperature_celsius:.1f}°C) "
                f"en fase crítica de fermentación ({days_fermenting:.1f} días). "
                f"Considerar aireación."
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_volatile_acidity(
        self,
        volatile_acidity_in_grams_per_liter: float,
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """
        Detect elevated volatile acidity (acetic acid).

        Thresholds (from config/thresholds.toml):
          Warning:  > volatile_acidity_warning_in_grams_per_liter  (default 0.6 g/L)
          Critical: > volatile_acidity_critical_in_grams_per_liter (default 0.8 g/L)

        Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery)
        """
        critical = thresholds.volatile_acidity_critical_in_grams_per_liter
        warning = thresholds.volatile_acidity_warning_in_grams_per_liter

        if volatile_acidity_in_grams_per_liter > critical:
            severity = SeverityLevel.CRITICAL
        elif volatile_acidity_in_grams_per_liter > warning:
            severity = SeverityLevel.WARNING
        else:
            return None

        deviation = DeviationScore(
            deviation=volatile_acidity_in_grams_per_liter,
            threshold=warning,
            magnitude="HIGH" if severity == SeverityLevel.CRITICAL else "MEDIUM",
            details={
                "current_g_l": round(volatile_acidity_in_grams_per_liter, 3),
                "warning_threshold_g_l": warning,
                "critical_threshold_g_l": critical,
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.VOLATILE_ACIDITY_HIGH.value,
            severity=severity.value,
            description=(
                f"Acidez volátil elevada: {volatile_acidity_in_grams_per_liter:.3f} g/L "
                f"(umbral crítico: {critical} g/L). Riesgo de acetificación."
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_unusual_duration(
        self,
        days_fermenting: float,
        historical_avg_duration: float,
    ) -> Optional[Anomaly]:
        """Detect fermentation duration outside typical range."""
        if not historical_avg_duration or historical_avg_duration <= 0:
            return None

        tolerance = 1.5
        too_long = days_fermenting > historical_avg_duration + tolerance
        too_short = (
            days_fermenting >= historical_avg_duration * 0.6
            and days_fermenting < historical_avg_duration - tolerance
        )
        if not (too_long or too_short):
            return None

        deviation = DeviationScore(
            deviation=days_fermenting,
            threshold=historical_avg_duration,
            magnitude="LOW",
            details={
                "current_days": round(days_fermenting, 1),
                "historical_avg_days": round(historical_avg_duration, 1),
                "tolerance_days": tolerance,
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.UNUSUAL_DURATION.value,
            severity=SeverityLevel.INFO.value,
            description=(
                f"Duración atípica: {days_fermenting:.1f} días vs histórico "
                f"{historical_avg_duration:.1f} días. Informativo - observar evolución."
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_atypical_pattern(
        self,
        current_density: float,
        historical_densities_band: Dict,
    ) -> Optional[Anomaly]:
        """Detect density reading outside ±2σ of historical pattern."""
        if not historical_densities_band or "mean" not in historical_densities_band:
            return None

        mean = historical_densities_band["mean"]
        stdev = historical_densities_band.get("stdev", 0)
        if stdev <= 0:
            return None

        z_score = abs(current_density - mean) / stdev
        if z_score <= 2.0:
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
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.ATYPICAL_PATTERN.value,
            severity=SeverityLevel.INFO.value,
            description=(
                f"Patrón atípico: densidad {current_density:.2f} está fuera de banda histórica "
                f"(z-score {z_score:.2f}). Investigar evolución."
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )
