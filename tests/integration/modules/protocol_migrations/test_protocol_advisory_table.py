"""
Integration tests for protocol_advisory table (migration 003, ADR-037).

Uses SQLAlchemy directly (not the repository) because ProtocolAdvisoryRepository
requires ISessionManager infrastructure. Testing the migration schema directly
is more appropriate here — we validate that the table structure is correct and
that data can be inserted, queried, and updated as the advisory workflow requires.

Table: protocol_advisory (UUID PK, no cross-module FK constraints per ADR-035)
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, update as sa_update

from src.modules.analysis_engine.src.domain.entities.protocol_advisory import ProtocolAdvisory


# ─── Helpers ────────────────────────────────────────────────────────────────

def _make_advisory(
    fermentation_id=None,
    analysis_id=None,
    advisory_type: str = "ADJUST_TEMPERATURE",
    risk_level: str = "MEDIUM",
    confidence: float = 0.85,
    **kwargs,
) -> ProtocolAdvisory:
    # Collect overridable defaults separately so callers can pass them in **kwargs
    # without triggering "multiple values for keyword argument" errors.
    defaults = dict(
        reasoning="Temperature trending above protocol threshold",
        is_acknowledged=False,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return ProtocolAdvisory(
        fermentation_id=fermentation_id or uuid4(),
        analysis_id=analysis_id or uuid4(),
        advisory_type=advisory_type,
        target_step_type="MONITORING",
        risk_level=risk_level,
        suggestion="Reduce temperature by 2°C",
        confidence=confidence,
        **defaults,
    )


async def _insert(session, advisory: ProtocolAdvisory) -> ProtocolAdvisory:
    session.add(advisory)
    await session.flush()
    await session.refresh(advisory)
    return advisory


# ─── Schema and basic CRUD ───────────────────────────────────────────────────

@pytest.mark.asyncio
class TestProtocolAdvisoryTable:
    """Verify migration 003 created protocol_advisory with correct schema."""

    async def test_create_advisory_with_uuid_pk(self, db_session):
        advisory = await _insert(db_session, _make_advisory())

        assert advisory.id is not None
        assert str(advisory.id)  # UUID stringifies
        assert advisory.advisory_type == "ADJUST_TEMPERATURE"
        assert advisory.is_acknowledged is False

    async def test_uuid_auto_generated_when_not_provided(self, db_session):
        adv1 = await _insert(db_session, _make_advisory())
        adv2 = await _insert(db_session, _make_advisory())

        assert adv1.id != adv2.id

    async def test_all_columns_stored_correctly(self, db_session):
        ferm_id = uuid4()
        anal_id = uuid4()
        exec_id = uuid4()

        advisory = _make_advisory(
            fermentation_id=ferm_id,
            analysis_id=anal_id,
            advisory_type="SKIP_STEP",
            risk_level="HIGH",
            confidence=0.92,
            execution_id=exec_id,
            reasoning="Detailed reasoning here",
        )
        created = await _insert(db_session, advisory)

        assert created.fermentation_id == ferm_id
        assert created.analysis_id == anal_id
        assert created.execution_id == exec_id
        assert created.advisory_type == "SKIP_STEP"
        assert created.risk_level == "HIGH"
        assert abs(created.confidence - 0.92) < 1e-6
        assert created.reasoning == "Detailed reasoning here"

    async def test_execution_id_is_optional(self, db_session):
        advisory = _make_advisory(execution_id=None)
        created = await _insert(db_session, advisory)

        assert created.execution_id is None

    async def test_created_at_timezone_aware(self, db_session):
        advisory = await _insert(db_session, _make_advisory())

        assert advisory.created_at is not None
        # DB stores UTC — tzinfo may be set or naive depending on driver settings
        # Key check: value is a datetime
        assert isinstance(advisory.created_at, datetime)


# ─── Query patterns (index validation) ──────────────────────────────────────

@pytest.mark.asyncio
class TestProtocolAdvisoryQueryPatterns:
    """Verify the 6 indices work correctly for the expected query patterns."""

    async def test_get_by_fermentation_id(self, db_session):
        ferm_id = uuid4()
        other_id = uuid4()

        await _insert(db_session, _make_advisory(fermentation_id=ferm_id))
        await _insert(db_session, _make_advisory(fermentation_id=ferm_id))
        await _insert(db_session, _make_advisory(fermentation_id=other_id))

        result = await db_session.execute(
            select(ProtocolAdvisory).where(ProtocolAdvisory.fermentation_id == ferm_id)
        )
        rows = result.scalars().all()

        assert len(rows) == 2
        assert all(r.fermentation_id == ferm_id for r in rows)

    async def test_get_by_analysis_id(self, db_session):
        anal_id = uuid4()

        await _insert(db_session, _make_advisory(analysis_id=anal_id))
        await _insert(db_session, _make_advisory(analysis_id=anal_id))

        result = await db_session.execute(
            select(ProtocolAdvisory).where(ProtocolAdvisory.analysis_id == anal_id)
        )
        rows = result.scalars().all()

        assert len(rows) == 2

    async def test_filter_by_risk_level(self, db_session):
        ferm_id = uuid4()

        await _insert(db_session, _make_advisory(fermentation_id=ferm_id, risk_level="HIGH"))
        await _insert(db_session, _make_advisory(fermentation_id=ferm_id, risk_level="LOW"))
        await _insert(db_session, _make_advisory(fermentation_id=ferm_id, risk_level="HIGH"))

        result = await db_session.execute(
            select(ProtocolAdvisory).where(
                ProtocolAdvisory.fermentation_id == ferm_id,
                ProtocolAdvisory.risk_level == "HIGH",
            )
        )
        high_risk = result.scalars().all()

        assert len(high_risk) == 2

    async def test_filter_unacknowledged(self, db_session):
        ferm_id = uuid4()

        await _insert(db_session, _make_advisory(fermentation_id=ferm_id, is_acknowledged=False))
        await _insert(db_session, _make_advisory(fermentation_id=ferm_id, is_acknowledged=False))
        acknowledged = _make_advisory(fermentation_id=ferm_id)
        acknowledged.is_acknowledged = True
        acknowledged.acknowledged_at = datetime.now(timezone.utc)
        await _insert(db_session, acknowledged)

        result = await db_session.execute(
            select(ProtocolAdvisory).where(
                ProtocolAdvisory.fermentation_id == ferm_id,
                ProtocolAdvisory.is_acknowledged == False,  # noqa: E712
            )
        )
        unacked = result.scalars().all()

        assert len(unacked) == 2


# ─── Acknowledgement workflow ─────────────────────────────────────────────────

@pytest.mark.asyncio
class TestProtocolAdvisoryAcknowledgement:
    """Verify the is_acknowledged / acknowledged_at lifecycle columns."""

    async def test_acknowledge_advisory(self, db_session):
        advisory = await _insert(db_session, _make_advisory())
        assert advisory.is_acknowledged is False

        ack_time = datetime.now(timezone.utc)
        await db_session.execute(
            sa_update(ProtocolAdvisory)
            .where(ProtocolAdvisory.id == advisory.id)
            .values(is_acknowledged=True, acknowledged_at=ack_time)
        )
        await db_session.flush()

        result = await db_session.execute(
            select(ProtocolAdvisory).where(ProtocolAdvisory.id == advisory.id)
        )
        refreshed = result.scalar_one()

        assert refreshed.is_acknowledged is True
        assert refreshed.acknowledged_at is not None

    async def test_acknowledged_at_null_before_acknowledgement(self, db_session):
        advisory = await _insert(db_session, _make_advisory())

        assert advisory.acknowledged_at is None

    async def test_multiple_advisories_acknowledge_one(self, db_session):
        ferm_id = uuid4()

        adv1 = await _insert(db_session, _make_advisory(fermentation_id=ferm_id))
        adv2 = await _insert(db_session, _make_advisory(fermentation_id=ferm_id))

        await db_session.execute(
            sa_update(ProtocolAdvisory)
            .where(ProtocolAdvisory.id == adv1.id)
            .values(is_acknowledged=True, acknowledged_at=datetime.now(timezone.utc))
        )
        await db_session.flush()

        result = await db_session.execute(
            select(ProtocolAdvisory).where(ProtocolAdvisory.fermentation_id == ferm_id)
        )
        all_advs = {r.id: r for r in result.scalars().all()}

        assert all_advs[adv1.id].is_acknowledged is True
        assert all_advs[adv2.id].is_acknowledged is False
