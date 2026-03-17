"""
Tests for ProtocolAnalysisIntegrationService (ADR-037).

Covers all three integration flows:
1. Confidence boost from protocol compliance score
2. Advisory generation from detected anomalies
3. Analysis recalibration on protocol change events
"""
import pytest
import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path (same pattern as other analysis_engine tests)
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
src_path = project_root / "src"
for p in [str(project_root), str(src_path)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Pre-import fermentation entities so SQLAlchemy mapper cascade resolves correctly.
# (Same pattern as tests/unit/modules/analysis_engine/conftest.py)
try:
    import src.modules.fermentation.src.domain.entities.fermentation_note  # noqa: F401
    import src.modules.fermentation.src.domain.entities.fermentation_lot_source  # noqa: F401
    import src.modules.fermentation.src.domain.entities.step_completion  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_step  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_protocol  # noqa: F401
    import src.modules.fermentation.src.domain.entities.protocol_execution  # noqa: F401
    import src.modules.fermentation.src.domain.entities.fermentation  # noqa: F401
except Exception:
    pass  # Not available in all environments; tests degrade gracefully

from src.modules.analysis_engine.src.service_component.services.protocol_integration_service import (
    ProtocolAnalysisIntegrationService,
    _ANOMALY_TO_ADVISORY,
)
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.entities.protocol_advisory import ProtocolAdvisory
from src.modules.analysis_engine.src.domain.enums.advisory_type import AdvisoryType
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.risk_level import RiskLevel
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def service() -> ProtocolAnalysisIntegrationService:
    """Create a stateless ProtocolAnalysisIntegrationService instance."""
    return ProtocolAnalysisIntegrationService()


def make_anomaly(anomaly_type: AnomalyType, severity: SeverityLevel) -> Anomaly:
    """Helper: build an Anomaly domain object for testing."""
    return Anomaly(
        analysis_id=uuid4(),
        sample_id=uuid4(),
        anomaly_type=anomaly_type.value,
        severity=severity.value,
        description=f"Test anomaly: {anomaly_type.value}",
        deviation_score={"magnitude": 2.5, "direction": "above"},
    )


# ===========================================================================
# Flow 1: Protocol Compliance Score → Analysis Confidence Boost
# ===========================================================================


class TestBoostConfidence:
    """Tests for the confidence boost formula (ADR-037 Flow 1)."""

    def test_high_compliance_boosts_confidence(self, service: ProtocolAnalysisIntegrationService):
        """87% compliance → multiplier=1.37, boosts 0.75 → min(1.0275, 1.0)=1.0."""
        result = service.boost_confidence(base_confidence=0.75, compliance_score=87.0)

        assert result["protocol_assigned"] is True
        assert result["base_confidence"] == 0.75
        assert result["protocol_compliance_score"] == 87.0
        assert result["compliance_multiplier"] == pytest.approx(1.37, abs=0.001)
        assert result["adjusted_confidence"] == 1.0  # capped at 1.0
        assert result["confidence_boost_pct"] == pytest.approx(25.0, abs=0.1)

    def test_100_compliance_maximum_multiplier(self, service: ProtocolAnalysisIntegrationService):
        """100% compliance → multiplier=1.5 (maximum boost)."""
        result = service.boost_confidence(base_confidence=0.6, compliance_score=100.0)

        assert result["compliance_multiplier"] == pytest.approx(1.5, abs=0.001)
        assert result["adjusted_confidence"] == pytest.approx(0.9, abs=0.001)

    def test_50_compliance_neutral_multiplier(self, service: ProtocolAnalysisIntegrationService):
        """50% compliance → multiplier=1.0, no boost or penalty."""
        result = service.boost_confidence(base_confidence=0.75, compliance_score=50.0)

        assert result["compliance_multiplier"] == pytest.approx(1.0, abs=0.001)
        assert result["adjusted_confidence"] == pytest.approx(0.75, abs=0.001)
        assert result["confidence_boost_pct"] == pytest.approx(0.0, abs=0.1)

    def test_low_compliance_reduces_confidence(self, service: ProtocolAnalysisIntegrationService):
        """45% compliance → multiplier=0.95, reduces confidence slightly."""
        result = service.boost_confidence(base_confidence=0.75, compliance_score=45.0)

        assert result["compliance_multiplier"] == pytest.approx(0.95, abs=0.001)
        assert result["adjusted_confidence"] == pytest.approx(0.712, abs=0.001)
        assert result["confidence_boost_pct"] < 0  # penalty

    def test_zero_compliance_minimum_multiplier(self, service: ProtocolAnalysisIntegrationService):
        """0% compliance → multiplier=0.5, halves the confidence."""
        result = service.boost_confidence(base_confidence=0.8, compliance_score=0.0)

        assert result["compliance_multiplier"] == pytest.approx(0.5, abs=0.001)
        assert result["adjusted_confidence"] == pytest.approx(0.4, abs=0.001)

    def test_confidence_capped_at_one(self, service: ProtocolAnalysisIntegrationService):
        """High base + high compliance must never exceed 1.0."""
        result = service.boost_confidence(base_confidence=0.9, compliance_score=100.0)

        assert result["adjusted_confidence"] == 1.0

    def test_no_protocol_assigned_returns_base(self, service: ProtocolAnalysisIntegrationService):
        """When compliance_score is None, base confidence is returned unchanged."""
        result = service.boost_confidence(base_confidence=0.72, compliance_score=None)

        assert result["protocol_assigned"] is False
        assert result["adjusted_confidence"] == pytest.approx(0.72, abs=0.001)
        assert result["compliance_multiplier"] == 1.0
        assert result["confidence_boost_pct"] == 0.0
        assert result["protocol_compliance_score"] is None

    def test_apply_boost_returns_float(self, service: ProtocolAnalysisIntegrationService):
        """apply_boost_to_overall_confidence returns a float, not a dict."""
        adjusted = service.apply_boost_to_overall_confidence(0.75, 87.0)

        assert isinstance(adjusted, float)
        assert adjusted == 1.0  # capped

    def test_apply_boost_no_protocol_returns_base(self, service: ProtocolAnalysisIntegrationService):
        """apply_boost_to_overall_confidence with None returns base as float."""
        adjusted = service.apply_boost_to_overall_confidence(0.65, None)

        assert adjusted == pytest.approx(0.65, abs=0.001)


# ===========================================================================
# Flow 2: Analysis Anomalies → Protocol Advisory
# ===========================================================================


class TestGenerateAdvisory:
    """Tests for advisory generation from anomalies (ADR-037 Flow 2)."""

    def test_stuck_fermentation_generates_additions_advisory(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """STUCK_FERMENTATION → ACCELERATE_STEP on ADDITIONS step."""
        anomaly = make_anomaly(AnomalyType.STUCK_FERMENTATION, SeverityLevel.CRITICAL)
        fermentation_id = uuid4()
        analysis_id = uuid4()

        advisory = service.generate_advisory(
            fermentation_id=fermentation_id,
            analysis_id=analysis_id,
            anomalies=[anomaly],
        )

        assert advisory is not None
        assert advisory.target_step_type == "ADDITIONS"
        assert advisory.advisory_type == AdvisoryType.ACCELERATE_STEP.value
        assert advisory.risk_level == RiskLevel.HIGH.value
        assert advisory.fermentation_id == fermentation_id
        assert advisory.analysis_id == analysis_id
        assert advisory.execution_id is None

    def test_hydrogen_sulfide_risk_generates_cap_management_advisory(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """HYDROGEN_SULFIDE_RISK → ACCELERATE_STEP on CAP_MANAGEMENT (CRITICAL)."""
        anomaly = make_anomaly(AnomalyType.HYDROGEN_SULFIDE_RISK, SeverityLevel.CRITICAL)

        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[anomaly],
        )

        assert advisory is not None
        assert advisory.target_step_type == "CAP_MANAGEMENT"
        assert advisory.advisory_type == AdvisoryType.ACCELERATE_STEP.value
        assert advisory.risk_level == RiskLevel.CRITICAL.value
        assert advisory.confidence == pytest.approx(0.95, abs=0.01)

    def test_temperature_critical_generates_monitoring_advisory(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """TEMPERATURE_OUT_OF_RANGE_CRITICAL → ACCELERATE_STEP on MONITORING."""
        anomaly = make_anomaly(
            AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL, SeverityLevel.CRITICAL
        )

        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[anomaly],
        )

        assert advisory is not None
        assert advisory.target_step_type == "MONITORING"
        assert advisory.risk_level == RiskLevel.CRITICAL.value

    def test_volatile_acidity_generates_add_step_advisory(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """VOLATILE_ACIDITY_HIGH → ADD_STEP for QUALITY_CHECK."""
        anomaly = make_anomaly(AnomalyType.VOLATILE_ACIDITY_HIGH, SeverityLevel.WARNING)

        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[anomaly],
        )

        assert advisory is not None
        assert advisory.advisory_type == AdvisoryType.ADD_STEP.value
        assert advisory.target_step_type == "QUALITY_CHECK"

    def test_selects_highest_priority_when_multiple_anomalies(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """With H2S (CRITICAL) + UNUSUAL_DURATION (LOW), advisory should be for H2S."""
        anomalies = [
            make_anomaly(AnomalyType.UNUSUAL_DURATION, SeverityLevel.INFO),
            make_anomaly(AnomalyType.HYDROGEN_SULFIDE_RISK, SeverityLevel.CRITICAL),
            make_anomaly(AnomalyType.TEMPERATURE_SUBOPTIMAL, SeverityLevel.WARNING),
        ]

        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=anomalies,
        )

        assert advisory is not None
        assert advisory.target_step_type == "CAP_MANAGEMENT"  # H2S → CAP_MANAGEMENT
        assert advisory.risk_level == RiskLevel.CRITICAL.value

    def test_no_anomalies_returns_none(self, service: ProtocolAnalysisIntegrationService):
        """No anomalies → no advisory."""
        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[],
        )

        assert advisory is None

    def test_with_execution_id(self, service: ProtocolAnalysisIntegrationService):
        """execution_id should be stored on the advisory for traceability."""
        execution_id = uuid4()
        anomaly = make_anomaly(AnomalyType.STUCK_FERMENTATION, SeverityLevel.CRITICAL)

        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[anomaly],
            execution_id=execution_id,
        )

        assert advisory is not None
        assert advisory.execution_id == execution_id

    def test_advisory_has_non_empty_suggestion(self, service: ProtocolAnalysisIntegrationService):
        """Generated advisory should always have a non-empty suggestion string."""
        anomaly = make_anomaly(AnomalyType.DENSITY_DROP_TOO_FAST, SeverityLevel.WARNING)

        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[anomaly],
        )

        assert advisory is not None
        assert advisory.suggestion
        assert len(advisory.suggestion) > 10

    def test_advisory_has_reasoning(self, service: ProtocolAnalysisIntegrationService):
        """Generated advisory should include a reasoning field."""
        anomaly = make_anomaly(AnomalyType.STUCK_FERMENTATION, SeverityLevel.CRITICAL)

        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[anomaly],
        )

        assert advisory is not None
        assert advisory.reasoning is not None
        assert "STUCK_FERMENTATION" in advisory.reasoning

    def test_advisory_not_acknowledged_by_default(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """New advisories should be unacknowledged by default."""
        anomaly = make_anomaly(AnomalyType.STUCK_FERMENTATION, SeverityLevel.CRITICAL)

        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[anomaly],
        )

        assert advisory is not None
        assert advisory.is_acknowledged is False
        assert advisory.acknowledged_at is None


class TestGenerateAllAdvisories:
    """Tests for generate_all_advisories (all anomalies, not just the top one)."""

    def test_multiple_anomalies_generate_multiple_advisories(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """Each mappable anomaly with a unique step_type should produce one advisory."""
        anomalies = [
            make_anomaly(AnomalyType.STUCK_FERMENTATION, SeverityLevel.CRITICAL),  # → ADDITIONS
            make_anomaly(AnomalyType.HYDROGEN_SULFIDE_RISK, SeverityLevel.CRITICAL),  # → CAP_MANAGEMENT
            make_anomaly(AnomalyType.VOLATILE_ACIDITY_HIGH, SeverityLevel.WARNING),  # → QUALITY_CHECK
        ]

        advisories = service.generate_all_advisories(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=anomalies,
        )

        assert len(advisories) == 3
        step_types = {a.target_step_type for a in advisories}
        assert "ADDITIONS" in step_types
        assert "CAP_MANAGEMENT" in step_types
        assert "QUALITY_CHECK" in step_types

    def test_deduplicates_same_step_type(self, service: ProtocolAnalysisIntegrationService):
        """Two anomalies mapping to the same step_type → only one advisory."""
        anomalies = [
            make_anomaly(AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL, SeverityLevel.CRITICAL),
            make_anomaly(AnomalyType.TEMPERATURE_SUBOPTIMAL, SeverityLevel.WARNING),
        ]
        # Both map to MONITORING

        advisories = service.generate_all_advisories(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=anomalies,
        )

        step_types = [a.target_step_type for a in advisories]
        assert step_types.count("MONITORING") == 1

    def test_empty_anomalies_returns_empty_list(self, service: ProtocolAnalysisIntegrationService):
        """No anomalies → empty list."""
        advisories = service.generate_all_advisories(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[],
        )

        assert advisories == []

    def test_advisories_sorted_critical_first(self, service: ProtocolAnalysisIntegrationService):
        """Advisories should be returned with highest risk first."""
        anomalies = [
            make_anomaly(AnomalyType.UNUSUAL_DURATION, SeverityLevel.INFO),   # LOW
            make_anomaly(AnomalyType.HYDROGEN_SULFIDE_RISK, SeverityLevel.CRITICAL),  # CRITICAL
            make_anomaly(AnomalyType.DENSITY_DROP_TOO_FAST, SeverityLevel.WARNING),   # MEDIUM
        ]

        advisories = service.generate_all_advisories(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=anomalies,
        )

        assert len(advisories) >= 2
        risk_scores = [RiskLevel(a.risk_level).priority_score for a in advisories]
        # Should be descending (most critical first)
        assert risk_scores == sorted(risk_scores, reverse=True)


# ===========================================================================
# Flow 3: Protocol Change → Analysis Recalibration
# ===========================================================================


class TestRecalibrateOnProtocolChange:
    """Tests for recalibration after protocol execution changes (ADR-037 Flow 3)."""

    def test_step_skipped_reduces_confidence_slightly(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """STEP_SKIPPED → 5% confidence reduction."""
        result = service.recalibrate_confidence_on_protocol_change(
            current_confidence=0.80, change_type="STEP_SKIPPED"
        )

        assert result["adjustment_factor"] == 0.95
        assert result["recalibrated_confidence"] == pytest.approx(0.76, abs=0.001)
        assert result["original_confidence"] == 0.8
        assert result["change_type"] == "STEP_SKIPPED"
        assert "omitido" in result["reason"].lower()

    def test_step_accelerated_reduces_confidence_minimally(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """STEP_ACCELERATED → 3% confidence reduction."""
        result = service.recalibrate_confidence_on_protocol_change(
            current_confidence=0.80, change_type="STEP_ACCELERATED"
        )

        assert result["adjustment_factor"] == 0.97
        assert result["recalibrated_confidence"] == pytest.approx(0.776, abs=0.001)

    def test_execution_paused_reduces_confidence_more(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """EXECUTION_PAUSED → 10% confidence reduction."""
        result = service.recalibrate_confidence_on_protocol_change(
            current_confidence=0.80, change_type="EXECUTION_PAUSED"
        )

        assert result["adjustment_factor"] == 0.90
        assert result["recalibrated_confidence"] == pytest.approx(0.72, abs=0.001)

    def test_unknown_change_type_no_adjustment(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """Unknown change_type → no adjustment (factor=1.0)."""
        result = service.recalibrate_confidence_on_protocol_change(
            current_confidence=0.75, change_type="SOMETHING_NEW"
        )

        assert result["adjustment_factor"] == 1.0
        assert result["recalibrated_confidence"] == pytest.approx(0.75, abs=0.001)

    def test_confidence_never_goes_below_zero(
        self, service: ProtocolAnalysisIntegrationService
    ):
        """Even with severe reduction, confidence stays >= 0.0."""
        result = service.recalibrate_confidence_on_protocol_change(
            current_confidence=0.05, change_type="EXECUTION_PAUSED"
        )

        assert result["recalibrated_confidence"] >= 0.0

    def test_confidence_never_exceeds_one(self, service: ProtocolAnalysisIntegrationService):
        """Even with boost factor >1.0 in future, confidence stays <= 1.0."""
        result = service.recalibrate_confidence_on_protocol_change(
            current_confidence=1.0, change_type="STEP_SKIPPED"
        )

        assert result["recalibrated_confidence"] <= 1.0


# ===========================================================================
# ProtocolAdvisory entity unit tests
# ===========================================================================


class TestProtocolAdvisoryEntity:
    """Tests for the ProtocolAdvisory entity itself."""

    def test_advisory_creation_with_enum_instances(self):
        """ProtocolAdvisory should accept enum instances for advisory_type and risk_level."""
        advisory = ProtocolAdvisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            advisory_type=AdvisoryType.ACCELERATE_STEP,
            target_step_type="ADDITIONS",
            risk_level=RiskLevel.HIGH,
            suggestion="Add nutrients now",
            confidence=0.87,
        )

        assert advisory.advisory_type == AdvisoryType.ACCELERATE_STEP.value
        assert advisory.risk_level == RiskLevel.HIGH.value

    def test_advisory_creation_with_string_values(self):
        """ProtocolAdvisory should also accept raw strings."""
        advisory = ProtocolAdvisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            advisory_type="SKIP_STEP",
            target_step_type="MONITORING",
            risk_level="LOW",
            suggestion="Step no longer needed",
            confidence=0.65,
        )

        assert advisory.advisory_type == "SKIP_STEP"
        assert advisory.risk_level == "LOW"

    def test_is_critical_property(self):
        """is_critical returns True only for CRITICAL risk level."""
        critical = ProtocolAdvisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            advisory_type=AdvisoryType.ACCELERATE_STEP,
            target_step_type="CAP_MANAGEMENT",
            risk_level=RiskLevel.CRITICAL,
            suggestion="H2S detected",
            confidence=0.95,
        )
        low = ProtocolAdvisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            advisory_type=AdvisoryType.ACCELERATE_STEP,
            target_step_type="MONITORING",
            risk_level=RiskLevel.LOW,
            suggestion="Unusual pattern",
            confidence=0.65,
        )

        assert critical.is_critical is True
        assert low.is_critical is False

    def test_acknowledge(self):
        """acknowledge() should set is_acknowledged=True and acknowledged_at."""
        advisory = ProtocolAdvisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            advisory_type=AdvisoryType.SKIP_STEP,
            target_step_type="MONITORING",
            risk_level=RiskLevel.LOW,
            suggestion="No longer needed",
            confidence=0.65,
        )

        assert advisory.is_acknowledged is False
        advisory.acknowledge()
        assert advisory.is_acknowledged is True
        assert advisory.acknowledged_at is not None

    def test_to_dict_contains_all_fields(self):
        """to_dict() should serialize all fields."""
        ferm_id = uuid4()
        analysis_id = uuid4()
        advisory = ProtocolAdvisory(
            fermentation_id=ferm_id,
            analysis_id=analysis_id,
            advisory_type=AdvisoryType.ADD_STEP,
            target_step_type="QUALITY_CHECK",
            risk_level=RiskLevel.HIGH,
            suggestion="Add quality check",
            confidence=0.87,
            reasoning="Volatile acidity anomaly detected",
        )

        data = advisory.to_dict()

        assert data["fermentation_id"] == str(ferm_id)
        assert data["analysis_id"] == str(analysis_id)
        assert data["advisory_type"] == "ADD_STEP"
        assert data["target_step_type"] == "QUALITY_CHECK"
        assert data["risk_level"] == "HIGH"
        assert data["suggestion"] == "Add quality check"
        assert data["reasoning"] == "Volatile acidity anomaly detected"
        assert data["confidence"] == 0.87
        assert data["is_acknowledged"] is False

    def test_advisory_type_enum_property(self):
        """advisory_type_enum returns the enum instance."""
        advisory = ProtocolAdvisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            advisory_type=AdvisoryType.ACCELERATE_STEP,
            target_step_type="ADDITIONS",
            risk_level=RiskLevel.HIGH,
            suggestion="Add nutrients",
            confidence=0.87,
        )

        assert advisory.advisory_type_enum == AdvisoryType.ACCELERATE_STEP

    def test_risk_level_enum_property(self):
        """risk_level_enum returns the enum instance."""
        advisory = ProtocolAdvisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            advisory_type=AdvisoryType.ACCELERATE_STEP,
            target_step_type="CAP_MANAGEMENT",
            risk_level=RiskLevel.CRITICAL,
            suggestion="H2S risk",
            confidence=0.95,
        )

        assert advisory.risk_level_enum == RiskLevel.CRITICAL


# ===========================================================================
# Enum unit tests
# ===========================================================================


class TestAdvisoryTypeEnum:
    """Tests for AdvisoryType enum."""

    def test_all_values_defined(self):
        """All three advisory types exist."""
        assert AdvisoryType.ACCELERATE_STEP.value == "ACCELERATE_STEP"
        assert AdvisoryType.SKIP_STEP.value == "SKIP_STEP"
        assert AdvisoryType.ADD_STEP.value == "ADD_STEP"

    def test_label_es(self):
        """label_es returns Spanish strings."""
        assert AdvisoryType.ACCELERATE_STEP.label_es == "Acelerar Paso"
        assert AdvisoryType.SKIP_STEP.label_es == "Omitir Paso"
        assert AdvisoryType.ADD_STEP.label_es == "Agregar Paso"

    def test_is_str_enum(self):
        """AdvisoryType is a str-based enum (compatible with JSON serialization)."""
        assert AdvisoryType.ACCELERATE_STEP == "ACCELERATE_STEP"


class TestRiskLevelEnum:
    """Tests for RiskLevel enum."""

    def test_priority_ordering(self):
        """CRITICAL > HIGH > MEDIUM > LOW by priority_score."""
        assert RiskLevel.CRITICAL.priority_score > RiskLevel.HIGH.priority_score
        assert RiskLevel.HIGH.priority_score > RiskLevel.MEDIUM.priority_score
        assert RiskLevel.MEDIUM.priority_score > RiskLevel.LOW.priority_score

    def test_label_es(self):
        """label_es returns Spanish strings."""
        assert RiskLevel.CRITICAL.label_es == "Crítico"
        assert RiskLevel.LOW.label_es == "Bajo"

    def test_action_timeframe_es(self):
        """action_timeframe_es provides actionable time windows."""
        assert "horas" in RiskLevel.CRITICAL.action_timeframe_es.lower()
        assert "rutinaria" in RiskLevel.LOW.action_timeframe_es.lower()

    def test_is_str_enum(self):
        """RiskLevel is a str-based enum."""
        assert RiskLevel.HIGH == "HIGH"


# ===========================================================================
# Anomaly mapping coverage test
# ===========================================================================


class TestAnomalyMappingCoverage:
    """Ensure every AnomalyType has an advisory mapping (completeness check)."""

    def test_all_anomaly_types_are_mapped(self):
        """Every AnomalyType value should have an entry in _ANOMALY_TO_ADVISORY."""
        unmapped = [
            t.value for t in AnomalyType if t.value not in _ANOMALY_TO_ADVISORY
        ]
        assert unmapped == [], f"AnomalyTypes without advisory mapping: {unmapped}"

    def test_all_mappings_use_valid_advisory_type(self):
        """Every mapping must use a valid AdvisoryType enum value."""
        valid_advisory_types = {t.value for t in AdvisoryType}
        for anomaly_val, (step, advisory_type, risk, suggestion) in _ANOMALY_TO_ADVISORY.items():
            assert advisory_type.value in valid_advisory_types, (
                f"{anomaly_val} maps to invalid advisory_type: {advisory_type}"
            )

    def test_all_mappings_use_valid_risk_level(self):
        """Every mapping must use a valid RiskLevel enum value."""
        valid_risk_levels = {t.value for t in RiskLevel}
        for anomaly_val, (step, advisory_type, risk, suggestion) in _ANOMALY_TO_ADVISORY.items():
            assert risk.value in valid_risk_levels, (
                f"{anomaly_val} maps to invalid risk_level: {risk}"
            )

    def test_all_mappings_have_non_empty_suggestion(self):
        """Every advisory mapping must have a non-empty suggestion string."""
        for anomaly_val, (step, advisory_type, risk, suggestion) in _ANOMALY_TO_ADVISORY.items():
            assert suggestion and len(suggestion) > 10, (
                f"{anomaly_val} has an empty or too-short suggestion"
            )
