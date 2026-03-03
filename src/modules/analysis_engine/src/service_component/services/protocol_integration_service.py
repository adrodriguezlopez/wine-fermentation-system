"""
Protocol Analysis Integration Service - Bridge between Protocol Engine and Analysis Engine.

Implements ADR-037: Protocol-Analysis Engine Integration.

Three integration flows:
1. CONFIDENCE BOOST (real-time):
   Protocol compliance score → multiplier → adjusted analysis confidence
   Formula: adjusted = base × (0.5 + compliance_score / 100.0), capped at 1.0

2. PROTOCOL ADVISORY (post-analysis, batch):
   Detected anomalies → ProtocolAdvisory entity
   Maps AnomalyType → StepType suggestion with risk level

3. ANALYSIS RECALIBRATION (event-driven, Phase 4):
   Protocol step changes → recalibrate analysis expectations

Design decisions (ADR-037):
- Stateless service: no session dependency (pure domain logic for boost calculation)
- advisory generation uses the session only for persistence
- No cross-module HTTP calls: compliance_score is passed as a parameter
  (caller is responsible for fetching it from the Protocol module)
- Graceful degradation: if compliance_score is None → base confidence unchanged
"""
from typing import List, Optional
from uuid import UUID

from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.entities.protocol_advisory import ProtocolAdvisory
from src.modules.analysis_engine.src.domain.enums.advisory_type import AdvisoryType
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.risk_level import RiskLevel


# ---------------------------------------------------------------------------
# Mapping: AnomalyType → (StepType category string, AdvisoryType, RiskLevel, suggestion)
# ---------------------------------------------------------------------------
_ANOMALY_TO_ADVISORY: dict[str, tuple[str, AdvisoryType, RiskLevel, str]] = {
    AnomalyType.STUCK_FERMENTATION.value: (
        "ADDITIONS",
        AdvisoryType.ACCELERATE_STEP,
        RiskLevel.HIGH,
        "Fermentación estancada detectada — considerar adelantar adición de nutrientes (DAP)",
    ),
    AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.value: (
        "MONITORING",
        AdvisoryType.ACCELERATE_STEP,
        RiskLevel.CRITICAL,
        "Temperatura fuera de rango crítico — aumentar frecuencia de monitoreo de temperatura",
    ),
    AnomalyType.VOLATILE_ACIDITY_HIGH.value: (
        "QUALITY_CHECK",
        AdvisoryType.ADD_STEP,
        RiskLevel.HIGH,
        "Acidez volátil elevada — se recomienda agregar paso de análisis de calidad urgente",
    ),
    AnomalyType.DENSITY_DROP_TOO_FAST.value: (
        "MONITORING",
        AdvisoryType.ACCELERATE_STEP,
        RiskLevel.MEDIUM,
        "Caída de densidad muy rápida — monitorear densidad con mayor frecuencia",
    ),
    AnomalyType.HYDROGEN_SULFIDE_RISK.value: (
        "CAP_MANAGEMENT",
        AdvisoryType.ACCELERATE_STEP,
        RiskLevel.CRITICAL,
        "Riesgo de H₂S detectado — adelantar aireación o punch-down inmediatamente",
    ),
    AnomalyType.TEMPERATURE_SUBOPTIMAL.value: (
        "MONITORING",
        AdvisoryType.ACCELERATE_STEP,
        RiskLevel.MEDIUM,
        "Temperatura subóptima — monitorear y ajustar control de temperatura",
    ),
    AnomalyType.UNUSUAL_DURATION.value: (
        "MONITORING",
        AdvisoryType.ACCELERATE_STEP,
        RiskLevel.LOW,
        "Duración fuera del rango esperado — revisar progreso de fermentación",
    ),
    AnomalyType.ATYPICAL_PATTERN.value: (
        "MONITORING",
        AdvisoryType.ACCELERATE_STEP,
        RiskLevel.LOW,
        "Patrón atípico de densidad detectado — monitoreo adicional recomendado",
    ),
}


class ProtocolAnalysisIntegrationService:
    """
    Bridges the Analysis Engine and Protocol Engine (ADR-037).

    This service is intentionally stateless for the confidence boost calculation
    (Flow 1) — pure functions that can be called without a DB session.

    For advisory generation (Flow 2), the caller is responsible for
    persisting the returned ProtocolAdvisory entities.

    Usage:
        service = ProtocolAnalysisIntegrationService()

        # Flow 1 — confidence boost
        result = service.boost_confidence(base=0.75, compliance_score=87.0)
        # → adjusted_confidence = 0.75 × (0.5 + 0.87) = 1.027 → capped at 1.0

        # Flow 2 — advisory generation
        advisory = service.generate_advisory(
            fermentation_id=..., analysis_id=..., anomalies=[anomaly_obj]
        )
        if advisory:
            session.add(advisory)
    """

    # ------------------------------------------------------------------
    # Flow 1: Protocol Compliance Score → Analysis Confidence Boost
    # ------------------------------------------------------------------

    def boost_confidence(
        self,
        base_confidence: float,
        compliance_score: Optional[float],
    ) -> dict:
        """
        Adjust analysis confidence based on protocol compliance score.

        Formula (ADR-037):
            multiplier = 0.5 + (compliance_score / 100.0)
            adjusted   = min(base_confidence × multiplier, 1.0)

        Range examples:
            compliance=100 → multiplier=1.5  (max boost +50%)
            compliance=87  → multiplier=1.37 (boost +37%)
            compliance=50  → multiplier=1.0  (neutral)
            compliance=0   → multiplier=0.5  (penalty -50%)

        Graceful degradation: if compliance_score is None (protocol not assigned),
        returns base confidence unchanged with a descriptive flag.

        Args:
            base_confidence: Confidence from statistical analysis [0.0, 1.0]
            compliance_score: Protocol compliance percentage [0.0, 100.0] or None

        Returns:
            dict with: base_confidence, protocol_compliance_score,
                       compliance_multiplier, adjusted_confidence,
                       confidence_boost_pct, protocol_assigned
        """
        if compliance_score is None:
            return {
                "base_confidence": round(base_confidence, 3),
                "protocol_compliance_score": None,
                "compliance_multiplier": 1.0,
                "adjusted_confidence": round(base_confidence, 3),
                "confidence_boost_pct": 0.0,
                "protocol_assigned": False,
            }

        compliance_pct = float(compliance_score) / 100.0
        multiplier = 0.5 + compliance_pct
        adjusted = min(base_confidence * multiplier, 1.0)
        boost_pct = round((adjusted - base_confidence) * 100, 1)

        return {
            "base_confidence": round(base_confidence, 3),
            "protocol_compliance_score": round(compliance_score, 2),
            "compliance_multiplier": round(multiplier, 3),
            "adjusted_confidence": round(adjusted, 3),
            "confidence_boost_pct": boost_pct,
            "protocol_assigned": True,
        }

    def apply_boost_to_overall_confidence(
        self,
        overall_confidence: float,
        compliance_score: Optional[float],
    ) -> float:
        """
        Convenience method that returns only the adjusted overall confidence float.

        Args:
            overall_confidence: Existing overall confidence [0.0, 1.0]
            compliance_score: Protocol compliance percentage or None

        Returns:
            Adjusted confidence float [0.0, 1.0]
        """
        result = self.boost_confidence(overall_confidence, compliance_score)
        return result["adjusted_confidence"]

    # ------------------------------------------------------------------
    # Flow 2: Analysis Anomalies → Protocol Advisory
    # ------------------------------------------------------------------

    def generate_advisory(
        self,
        fermentation_id: UUID,
        analysis_id: UUID,
        anomalies: List[Anomaly],
        execution_id: Optional[UUID] = None,
    ) -> Optional[ProtocolAdvisory]:
        """
        Generate a protocol advisory for the highest-priority anomaly detected.

        Selects the most critical anomaly that has a known protocol mapping,
        creates and returns a ProtocolAdvisory (unsaved — caller persists it).

        Priority order: CRITICAL > HIGH > MEDIUM > LOW (RiskLevel.priority_score)

        Args:
            fermentation_id: ID of the fermentation being analyzed
            analysis_id: ID of the Analysis triggering this advisory
            anomalies: List of detected Anomaly objects from AnomalyDetectionService
            execution_id: Active ProtocolExecution ID (optional, for traceability)

        Returns:
            ProtocolAdvisory for the top-priority actionable anomaly, or None
            if no anomaly has a protocol mapping (e.g., all INFO with no mapping).
        """
        candidates: list[tuple[int, Anomaly, tuple]] = []

        for anomaly in anomalies:
            mapping = _ANOMALY_TO_ADVISORY.get(anomaly.anomaly_type)
            if mapping is None:
                continue
            step_type, advisory_type, risk_level, suggestion = mapping
            candidates.append((risk_level.priority_score, anomaly, mapping))

        if not candidates:
            return None

        # Pick highest-priority (largest score = most critical)
        candidates.sort(key=lambda x: x[0], reverse=True)
        _, top_anomaly, (step_type, advisory_type, risk_level, suggestion) = candidates[0]

        reasoning = (
            f"Anomalía '{top_anomaly.anomaly_type}' detectada "
            f"(severidad: {top_anomaly.severity}). "
            f"Se recomienda {advisory_type.label_es.lower()} del paso de tipo '{step_type}'."
        )

        return ProtocolAdvisory(
            fermentation_id=fermentation_id,
            analysis_id=analysis_id,
            execution_id=execution_id,
            advisory_type=advisory_type,
            target_step_type=step_type,
            risk_level=risk_level,
            suggestion=suggestion,
            reasoning=reasoning,
            confidence=self._confidence_for_risk(risk_level),
        )

    def generate_all_advisories(
        self,
        fermentation_id: UUID,
        analysis_id: UUID,
        anomalies: List[Anomaly],
        execution_id: Optional[UUID] = None,
    ) -> List[ProtocolAdvisory]:
        """
        Generate one advisory per mappable anomaly (de-duplicated by step_type).

        Use this when you want the full advisory set instead of just the top one.

        Args:
            fermentation_id: Fermentation being analyzed
            analysis_id: Analysis ID
            anomalies: Detected anomalies
            execution_id: Active ProtocolExecution ID (optional)

        Returns:
            List of ProtocolAdvisory objects, sorted by risk level (critical first)
        """
        advisories: list[ProtocolAdvisory] = []
        seen_step_types: set[str] = set()

        # Sort anomalies by priority (highest first)
        sorted_anomalies = sorted(
            anomalies,
            key=lambda a: _ANOMALY_TO_ADVISORY.get(a.anomaly_type, ("", None, RiskLevel.LOW, ""))[2].priority_score  # type: ignore
            if _ANOMALY_TO_ADVISORY.get(a.anomaly_type) else 0,
            reverse=True,
        )

        for anomaly in sorted_anomalies:
            mapping = _ANOMALY_TO_ADVISORY.get(anomaly.anomaly_type)
            if mapping is None:
                continue

            step_type, advisory_type, risk_level, suggestion = mapping
            if step_type in seen_step_types:
                continue  # Deduplicate by step_type
            seen_step_types.add(step_type)

            reasoning = (
                f"Anomalía '{anomaly.anomaly_type}' detectada "
                f"(severidad: {anomaly.severity}). "
                f"Se recomienda {advisory_type.label_es.lower()} del paso de tipo '{step_type}'."
            )

            advisories.append(
                ProtocolAdvisory(
                    fermentation_id=fermentation_id,
                    analysis_id=analysis_id,
                    execution_id=execution_id,
                    advisory_type=advisory_type,
                    target_step_type=step_type,
                    risk_level=risk_level,
                    suggestion=suggestion,
                    reasoning=reasoning,
                    confidence=self._confidence_for_risk(risk_level),
                )
            )

        return advisories

    # ------------------------------------------------------------------
    # Flow 3: Protocol Change → Analysis Recalibration (event-driven)
    # ------------------------------------------------------------------

    def recalibrate_confidence_on_protocol_change(
        self,
        current_confidence: float,
        change_type: str,
    ) -> dict:
        """
        Adjust confidence expectation after a protocol execution change event.

        This is a lightweight recalibration — it modifies the confidence
        multiplier based on the type of protocol change. Full recalibration
        (re-running the comparison pipeline) is out of scope for Phase 1.

        Recalibration logic (ADR-037 Phase 4):
            STEP_SKIPPED      → confidence reduced by 5% (expected trajectory may shift)
            STEP_ACCELERATED  → confidence slightly reduced by 3% (uncertainty increases)
            EXECUTION_PAUSED  → confidence reduced by 10% (significant trajectory change)
            OTHER             → no adjustment

        Args:
            current_confidence: Current overall confidence [0.0, 1.0]
            change_type: One of "STEP_SKIPPED", "STEP_ACCELERATED", "EXECUTION_PAUSED"

        Returns:
            dict with: original_confidence, change_type, adjustment_factor,
                       recalibrated_confidence, reason
        """
        adjustments = {
            "STEP_SKIPPED": (0.95, "Paso omitido: trayectoria esperada puede variar"),
            "STEP_ACCELERATED": (0.97, "Paso adelantado: incertidumbre temporal aumenta"),
            "EXECUTION_PAUSED": (0.90, "Ejecución pausada: estimación de duración inválida"),
        }

        factor, reason = adjustments.get(change_type, (1.0, "Cambio sin efecto en confianza"))
        recalibrated = round(min(max(current_confidence * factor, 0.0), 1.0), 3)

        return {
            "original_confidence": round(current_confidence, 3),
            "change_type": change_type,
            "adjustment_factor": factor,
            "recalibrated_confidence": recalibrated,
            "reason": reason,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _confidence_for_risk(risk_level: RiskLevel) -> float:
        """
        Map risk level to a default advisory confidence score.

        Critical anomalies have strong pattern matching (high confidence),
        low-risk anomalies have weaker pattern support.
        """
        return {
            RiskLevel.CRITICAL: 0.95,
            RiskLevel.HIGH: 0.87,
            RiskLevel.MEDIUM: 0.75,
            RiskLevel.LOW: 0.65,
        }[risk_level]
