"""
Unit tests for ProtocolAdvisoryRepository implementation (ADR-037).

These tests follow the project's unit testing practices:
- Mock only the session manager (not SQLAlchemy internals)
- Mock the RESULTS of database queries (not query builders)
- Focus on the repository CONTRACT, not implementation details
- Use shared ADR-012 testing infrastructure

Following ADR-002: Unit tests verify repository behavior without a database connection.
Following ADR-012: Using shared testing infrastructure for consistent mocking.
Following ADR-037: Protocol↔Analysis Integration repository coverage.
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError

from src.modules.analysis_engine.src.domain.entities.protocol_advisory import ProtocolAdvisory
from src.modules.analysis_engine.src.domain.enums.advisory_type import AdvisoryType
from src.modules.analysis_engine.src.domain.enums.risk_level import RiskLevel
from src.modules.analysis_engine.src.repository_component.repositories.protocol_advisory_repository import (
    ProtocolAdvisoryRepository,
)
from src.shared.infra.repository.base_repository import BaseRepository
from src.shared.testing.unit import (
    MockSessionManagerBuilder,
    create_query_result,
    create_scalar_result,
    create_empty_result,
    create_mock_entity,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FERMENTATION_ID = uuid4()
ANALYSIS_ID = uuid4()
ADVISORY_ID = uuid4()


def make_advisory(
    *,
    id: UUID = None,
    fermentation_id: UUID = None,
    analysis_id: UUID = None,
    advisory_type: str = AdvisoryType.ACCELERATE_STEP.value,
    risk_level: str = RiskLevel.HIGH.value,
    is_acknowledged: bool = False,
    acknowledged_at=None,
) -> ProtocolAdvisory:
    """Create a mock ProtocolAdvisory entity for testing."""
    return create_mock_entity(
        ProtocolAdvisory,
        id=id or uuid4(),
        fermentation_id=fermentation_id or FERMENTATION_ID,
        analysis_id=analysis_id or ANALYSIS_ID,
        execution_id=None,
        advisory_type=advisory_type,
        target_step_type="FERMENTATION",
        risk_level=risk_level,
        suggestion="Test suggestion",
        reasoning="Test reasoning",
        confidence=0.85,
        is_acknowledged=is_acknowledged,
        acknowledged_at=acknowledged_at,
        created_at=datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# TestProtocolAdvisoryRepositoryContract
# ---------------------------------------------------------------------------

class TestProtocolAdvisoryRepositoryContract:
    """Verify the repository honours its BaseRepository + IProtocolAdvisoryRepository contract."""

    @pytest.mark.asyncio
    async def test_inherits_from_base_repository(self):
        """Repository must extend BaseRepository (ADR-012 pattern)."""
        session_manager = MockSessionManagerBuilder().build()
        repo = ProtocolAdvisoryRepository(session_manager)
        assert isinstance(repo, BaseRepository)

    @pytest.mark.asyncio
    async def test_implements_all_interface_methods(self):
        """All IProtocolAdvisoryRepository methods must be present and callable."""
        session_manager = MockSessionManagerBuilder().build()
        repo = ProtocolAdvisoryRepository(session_manager)

        expected_methods = [
            "add", "add_many", "get_by_id", "get_by_fermentation_id",
            "get_by_analysis_id", "get_unacknowledged_by_fermentation_id",
            "acknowledge", "list_by_risk_level", "list_by_advisory_type",
            "count_unacknowledged",
        ]
        for method in expected_methods:
            assert hasattr(repo, method), f"Missing method: {method}"
            assert callable(getattr(repo, method)), f"Not callable: {method}"


# ---------------------------------------------------------------------------
# TestAdd
# ---------------------------------------------------------------------------

class TestAdd:
    """Tests for ProtocolAdvisoryRepository.add()."""

    @pytest.mark.asyncio
    async def test_add_returns_advisory(self):
        """add() should return the advisory that was persisted."""
        advisory = make_advisory(id=ADVISORY_ID)
        session_manager = MockSessionManagerBuilder().build()
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.add(advisory)

        assert result is advisory
        assert result.id == ADVISORY_ID

    @pytest.mark.asyncio
    async def test_add_calls_session_add_and_flush(self):
        """add() must call session.add() + session.flush()."""
        advisory = make_advisory()
        builder = MockSessionManagerBuilder()
        repo = ProtocolAdvisoryRepository(builder.build())

        await repo.add(advisory)

        builder._session.add.assert_called_once_with(advisory)
        builder._session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_propagates_flush_error(self):
        """add() should surface flush errors via execute_with_error_mapping."""
        from src.shared.infra.repository.base_repository import RepositoryError
        advisory = make_advisory()
        session_manager = (
            MockSessionManagerBuilder()
            .with_flush_side_effect(SQLAlchemyError("flush failed"))
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        with pytest.raises((RepositoryError, SQLAlchemyError)):
            await repo.add(advisory)


# ---------------------------------------------------------------------------
# TestAddMany
# ---------------------------------------------------------------------------

class TestAddMany:
    """Tests for ProtocolAdvisoryRepository.add_many()."""

    @pytest.mark.asyncio
    async def test_add_many_returns_empty_list_for_empty_input(self):
        """add_many([]) must return [] without touching the session."""
        session_manager = MockSessionManagerBuilder().build()
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.add_many([])

        assert result == []

    @pytest.mark.asyncio
    async def test_add_many_returns_all_advisories(self):
        """add_many() should return the same list that was passed in."""
        advisories = [make_advisory() for _ in range(3)]
        session_manager = MockSessionManagerBuilder().build()
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.add_many(advisories)

        assert result == advisories
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_add_many_flushes_once(self):
        """add_many() should add all entities then flush exactly once."""
        advisories = [make_advisory(), make_advisory()]
        builder = MockSessionManagerBuilder()
        repo = ProtocolAdvisoryRepository(builder.build())

        await repo.add_many(advisories)

        assert builder._session.add.call_count == 2
        builder._session.flush.assert_called_once()


# ---------------------------------------------------------------------------
# TestGetById
# ---------------------------------------------------------------------------

class TestGetById:
    """Tests for ProtocolAdvisoryRepository.get_by_id()."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_advisory_when_found(self):
        """get_by_id() returns the entity when it exists."""
        advisory = make_advisory(id=ADVISORY_ID)
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_query_result([advisory]))
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.get_by_id(ADVISORY_ID)

        assert result is advisory

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self):
        """get_by_id() returns None when the advisory doesn't exist."""
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_empty_result())
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.get_by_id(uuid4())

        assert result is None


# ---------------------------------------------------------------------------
# TestGetByFermentationId
# ---------------------------------------------------------------------------

class TestGetByFermentationId:
    """Tests for ProtocolAdvisoryRepository.get_by_fermentation_id()."""

    @pytest.mark.asyncio
    async def test_returns_list_of_advisories(self):
        """Should return all advisories for a fermentation."""
        advisories = [make_advisory(), make_advisory()]
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_query_result(advisories))
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.get_by_fermentation_id(FERMENTATION_ID)

        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_none_found(self):
        """Should return [] when no advisories exist for the fermentation."""
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_empty_result())
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.get_by_fermentation_id(FERMENTATION_ID)

        assert result == []

    @pytest.mark.asyncio
    async def test_accepts_pagination_parameters(self):
        """Pagination (skip/limit) parameters must be accepted without error."""
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_empty_result())
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        # Should not raise
        result = await repo.get_by_fermentation_id(
            FERMENTATION_ID, include_acknowledged=False, skip=10, limit=5
        )
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# TestGetByAnalysisId
# ---------------------------------------------------------------------------

class TestGetByAnalysisId:
    """Tests for ProtocolAdvisoryRepository.get_by_analysis_id()."""

    @pytest.mark.asyncio
    async def test_returns_advisories_for_analysis(self):
        """Should return all advisories tied to a specific analysis run."""
        advisories = [make_advisory(analysis_id=ANALYSIS_ID)]
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_query_result(advisories))
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.get_by_analysis_id(ANALYSIS_ID)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_analysis_has_no_advisories(self):
        """Returns [] when no advisories were generated for the analysis."""
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_empty_result())
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.get_by_analysis_id(uuid4())

        assert result == []


# ---------------------------------------------------------------------------
# TestGetUnacknowledgedByFermentationId
# ---------------------------------------------------------------------------

class TestGetUnacknowledgedByFermentationId:
    """Tests for ProtocolAdvisoryRepository.get_unacknowledged_by_fermentation_id()."""

    @pytest.mark.asyncio
    async def test_returns_only_unacknowledged(self):
        """Should return all unacknowledged advisories."""
        unacked = [make_advisory(is_acknowledged=False) for _ in range(2)]
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_query_result(unacked))
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.get_unacknowledged_by_fermentation_id(FERMENTATION_ID)

        assert len(result) == 2
        assert all(not a.is_acknowledged for a in result)

    @pytest.mark.asyncio
    async def test_sorts_critical_first(self):
        """Result must be sorted by risk priority (CRITICAL before LOW)."""
        low = make_advisory(risk_level=RiskLevel.LOW.value, is_acknowledged=False)
        critical = make_advisory(risk_level=RiskLevel.CRITICAL.value, is_acknowledged=False)
        medium = make_advisory(risk_level=RiskLevel.MEDIUM.value, is_acknowledged=False)

        # DB returns them in arbitrary order (newest-first from DB)
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_query_result([low, critical, medium]))
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.get_unacknowledged_by_fermentation_id(FERMENTATION_ID)

        assert result[0].risk_level == RiskLevel.CRITICAL.value
        assert result[1].risk_level == RiskLevel.MEDIUM.value
        assert result[2].risk_level == RiskLevel.LOW.value

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_acknowledged(self):
        """Returns [] when no pending advisories exist."""
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_empty_result())
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.get_unacknowledged_by_fermentation_id(FERMENTATION_ID)

        assert result == []


# ---------------------------------------------------------------------------
# TestAcknowledge
# ---------------------------------------------------------------------------

class TestAcknowledge:
    """Tests for ProtocolAdvisoryRepository.acknowledge()."""

    @pytest.mark.asyncio
    async def test_acknowledge_returns_updated_advisory(self):
        """acknowledge() returns the advisory after calling .acknowledge() on it."""
        ack_time = datetime(2026, 3, 2, 10, 0, 0, tzinfo=timezone.utc)
        advisory = make_advisory(id=ADVISORY_ID, is_acknowledged=False)
        # Simulate the real entity.acknowledge() that sets acknowledged_at
        advisory.acknowledge = lambda: setattr(advisory, "acknowledged_at", ack_time)

        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_query_result([advisory]))
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.acknowledge(ADVISORY_ID)

        assert result is advisory

    @pytest.mark.asyncio
    async def test_acknowledge_returns_none_when_not_found(self):
        """acknowledge() returns None when advisory ID doesn't exist."""
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_empty_result())
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.acknowledge(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_acknowledge_calls_entity_acknowledge_method(self):
        """The entity's own .acknowledge() method must be called once."""
        from unittest.mock import MagicMock
        ack_time = datetime(2026, 3, 2, 10, 0, 0, tzinfo=timezone.utc)
        advisory = make_advisory(id=ADVISORY_ID, is_acknowledged=False)
        # Mock acknowledge but also set acknowledged_at so the log line doesn't crash
        def _acknowledge():
            advisory.acknowledged_at = ack_time
        advisory.acknowledge = MagicMock(side_effect=_acknowledge)

        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_query_result([advisory]))
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        await repo.acknowledge(ADVISORY_ID)

        advisory.acknowledge.assert_called_once()

    @pytest.mark.asyncio
    async def test_acknowledge_flushes_after_mutation(self):
        """acknowledge() must flush the session after mutating the entity."""
        ack_time = datetime(2026, 3, 2, 10, 0, 0, tzinfo=timezone.utc)
        advisory = make_advisory(id=ADVISORY_ID)
        advisory.acknowledge = lambda: setattr(advisory, "acknowledged_at", ack_time)

        builder = MockSessionManagerBuilder().with_execute_result(create_query_result([advisory]))
        repo = ProtocolAdvisoryRepository(builder.build())

        await repo.acknowledge(ADVISORY_ID)

        builder._session.flush.assert_called_once()


# ---------------------------------------------------------------------------
# TestListByRiskLevel
# ---------------------------------------------------------------------------

class TestListByRiskLevel:
    """Tests for ProtocolAdvisoryRepository.list_by_risk_level()."""

    @pytest.mark.asyncio
    async def test_returns_advisories_matching_risk_level(self):
        """Should return only advisories with the specified risk level."""
        critical_advisories = [
            make_advisory(risk_level=RiskLevel.CRITICAL.value),
            make_advisory(risk_level=RiskLevel.CRITICAL.value),
        ]
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_query_result(critical_advisories))
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.list_by_risk_level(FERMENTATION_ID, RiskLevel.CRITICAL)

        assert len(result) == 2
        assert all(a.risk_level == RiskLevel.CRITICAL.value for a in result)

    @pytest.mark.asyncio
    async def test_returns_empty_for_unknown_risk_level_combo(self):
        """Returns [] when no advisories match the risk level filter."""
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_empty_result())
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.list_by_risk_level(FERMENTATION_ID, RiskLevel.LOW)

        assert result == []

    @pytest.mark.asyncio
    async def test_accepts_pagination(self):
        """list_by_risk_level() must accept skip and limit without error."""
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_empty_result())
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.list_by_risk_level(
            FERMENTATION_ID, RiskLevel.HIGH, skip=5, limit=10
        )
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# TestListByAdvisoryType
# ---------------------------------------------------------------------------

class TestListByAdvisoryType:
    """Tests for ProtocolAdvisoryRepository.list_by_advisory_type()."""

    @pytest.mark.asyncio
    async def test_returns_advisories_matching_type(self):
        """Should return only advisories with the specified advisory type."""
        advisories = [
            make_advisory(advisory_type=AdvisoryType.SKIP_STEP.value),
            make_advisory(advisory_type=AdvisoryType.SKIP_STEP.value),
        ]
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_query_result(advisories))
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.list_by_advisory_type(FERMENTATION_ID, AdvisoryType.SKIP_STEP)

        assert len(result) == 2
        assert all(a.advisory_type == AdvisoryType.SKIP_STEP.value for a in result)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_match(self):
        """Returns [] when no advisories have the given type."""
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_empty_result())
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.list_by_advisory_type(FERMENTATION_ID, AdvisoryType.ADD_STEP)

        assert result == []

    @pytest.mark.asyncio
    async def test_accepts_pagination(self):
        """list_by_advisory_type() must accept skip and limit without error."""
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(create_empty_result())
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.list_by_advisory_type(
            FERMENTATION_ID, AdvisoryType.ACCELERATE_STEP, skip=0, limit=20
        )
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# TestCountUnacknowledged
# ---------------------------------------------------------------------------

class TestCountUnacknowledged:
    """Tests for ProtocolAdvisoryRepository.count_unacknowledged()."""

    @pytest.mark.asyncio
    async def test_returns_integer_count(self):
        """count_unacknowledged() must return an int."""
        scalar_result = create_scalar_result(3)
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(scalar_result)
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.count_unacknowledged(FERMENTATION_ID)

        assert result == 3

    @pytest.mark.asyncio
    async def test_returns_zero_when_none_pending(self):
        """count_unacknowledged() returns 0 when all advisories are acknowledged."""
        scalar_result = create_scalar_result(0)
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(scalar_result)
            .build()
        )
        repo = ProtocolAdvisoryRepository(session_manager)

        result = await repo.count_unacknowledged(FERMENTATION_ID)

        assert result == 0
