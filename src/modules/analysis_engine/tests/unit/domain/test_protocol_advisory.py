"""
Tests for ProtocolAdvisory entity.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.modules.analysis_engine.src.domain.entities.protocol_advisory import ProtocolAdvisory
from src.modules.analysis_engine.src.domain.enums.advisory_type import AdvisoryType
from src.modules.analysis_engine.src.domain.enums.risk_level import RiskLevel


def make_advisory(**kwargs) -> ProtocolAdvisory:
    """Build a minimal valid ProtocolAdvisory for testing."""
    defaults = dict(
        fermentation_id=uuid4(),
        analysis_id=uuid4(),
        advisory_type=AdvisoryType.ADD_STEP,
        target_step_type="NUTRIENT_ADDITION",
        risk_level=RiskLevel.HIGH,
        suggestion="Add DAP nutrients to restart fermentation",
        confidence=0.85,
    )
    defaults.update(kwargs)
    return ProtocolAdvisory(**defaults)


class TestProtocolAdvisoryInitialization:
    def test_id_is_auto_generated(self):
        advisory = make_advisory()
        assert advisory.id is not None

    def test_explicit_id_is_preserved(self):
        fixed_id = uuid4()
        advisory = make_advisory(id=fixed_id)
        assert advisory.id == fixed_id

    def test_fermentation_and_analysis_ids_stored(self):
        f_id = uuid4()
        a_id = uuid4()
        advisory = make_advisory(fermentation_id=f_id, analysis_id=a_id)
        assert advisory.fermentation_id == f_id
        assert advisory.analysis_id == a_id

    def test_advisory_type_stored_as_string_from_enum(self):
        advisory = make_advisory(advisory_type=AdvisoryType.ACCELERATE_STEP)
        assert advisory.advisory_type == AdvisoryType.ACCELERATE_STEP.value
        assert advisory.advisory_type == "ACCELERATE_STEP"

    def test_risk_level_stored_as_string_from_enum(self):
        advisory = make_advisory(risk_level=RiskLevel.CRITICAL)
        assert advisory.risk_level == RiskLevel.CRITICAL.value
        assert advisory.risk_level == "CRITICAL"

    def test_default_is_acknowledged_is_false(self):
        advisory = make_advisory()
        assert advisory.is_acknowledged is False

    def test_default_acknowledged_at_is_none(self):
        advisory = make_advisory()
        assert advisory.acknowledged_at is None

    def test_created_at_is_set_automatically(self):
        advisory = make_advisory()
        assert advisory.created_at is not None
        assert isinstance(advisory.created_at, datetime)

    def test_execution_id_defaults_to_none(self):
        advisory = make_advisory()
        assert advisory.execution_id is None

    def test_confidence_and_suggestion_stored(self):
        advisory = make_advisory(confidence=0.92, suggestion="Test suggestion")
        assert advisory.confidence == pytest.approx(0.92)
        assert advisory.suggestion == "Test suggestion"

    def test_reasoning_optional_defaults_none(self):
        advisory = make_advisory()
        assert advisory.reasoning is None

    def test_reasoning_stored_when_provided(self):
        advisory = make_advisory(reasoning="Density stalled for 2 days")
        assert advisory.reasoning == "Density stalled for 2 days"


class TestProtocolAdvisoryAcknowledge:
    def test_acknowledge_sets_is_acknowledged_true(self):
        advisory = make_advisory()
        advisory.acknowledge()
        assert advisory.is_acknowledged is True

    def test_acknowledge_sets_acknowledged_at_timestamp(self):
        before = datetime.now(timezone.utc)
        advisory = make_advisory()
        advisory.acknowledge()
        after = datetime.now(timezone.utc)

        assert advisory.acknowledged_at is not None
        assert before <= advisory.acknowledged_at <= after

    def test_acknowledge_twice_overwrites_acknowledged_at(self):
        # acknowledge() is intentionally idempotent — second call refreshes timestamp
        advisory = make_advisory()
        advisory.acknowledge()
        first_ts = advisory.acknowledged_at

        advisory.acknowledge()
        second_ts = advisory.acknowledged_at

        # Second call should succeed (no ValueError) and refresh the timestamp
        assert advisory.is_acknowledged is True
        assert second_ts >= first_ts

    def test_acknowledged_at_is_timezone_aware(self):
        advisory = make_advisory()
        advisory.acknowledge()
        assert advisory.acknowledged_at.tzinfo is not None


class TestProtocolAdvisoryProperties:
    def test_advisory_type_enum_returns_enum(self):
        advisory = make_advisory(advisory_type=AdvisoryType.SKIP_STEP)
        assert advisory.advisory_type_enum == AdvisoryType.SKIP_STEP

    def test_risk_level_enum_returns_enum(self):
        advisory = make_advisory(risk_level=RiskLevel.CRITICAL)
        assert advisory.risk_level_enum == RiskLevel.CRITICAL

    def test_is_critical_true_for_critical_risk(self):
        advisory = make_advisory(risk_level=RiskLevel.CRITICAL)
        assert advisory.is_critical is True

    def test_is_critical_false_for_non_critical_risk(self):
        for level in (RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW):
            advisory = make_advisory(risk_level=level)
            assert advisory.is_critical is False


class TestProtocolAdvisoryToDict:
    def test_to_dict_contains_expected_keys(self):
        advisory = make_advisory()
        result = advisory.to_dict()
        expected_keys = {
            "id", "fermentation_id", "analysis_id", "execution_id",
            "advisory_type", "target_step_type", "risk_level",
            "suggestion", "reasoning", "confidence",
            "is_acknowledged", "acknowledged_at", "created_at",
        }
        assert set(result.keys()) == expected_keys

    def test_to_dict_acknowledged_at_none_before_acknowledge(self):
        advisory = make_advisory()
        result = advisory.to_dict()
        assert result["acknowledged_at"] is None

    def test_to_dict_acknowledged_at_iso_after_acknowledge(self):
        advisory = make_advisory()
        advisory.acknowledge()
        result = advisory.to_dict()
        assert result["acknowledged_at"] is not None
        # Should be an ISO 8601 string
        datetime.fromisoformat(result["acknowledged_at"])
