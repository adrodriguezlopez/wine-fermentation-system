"""
Integration tests for protocol migration tables (ADR-035, ADR-040).

Verifies that migrations 001 and 002 created the correct schema and that
repositories can perform CRUD operations against the live DB.

Tables tested:
- fermentation_protocols  (migration 001)
- protocol_steps          (migration 001)
- protocol_executions     (migration 001)
- protocol_alerts         (migration 002)
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
from src.modules.fermentation.src.domain.entities.protocol_alert import ProtocolAlert
from src.modules.fermentation.src.repository_component.fermentation_protocol_repository import (
    FermentationProtocolRepository,
)
from src.modules.fermentation.src.repository_component.protocol_step_repository import (
    ProtocolStepRepository,
)
from src.modules.fermentation.src.repository_component.protocol_execution_repository import (
    ProtocolExecutionRepository,
)
from src.modules.fermentation.src.repository_component.protocol_alert_repository import (
    ProtocolAlertRepository,
)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _make_protocol(winery_id: int = 1, varietal_code: str = "PN", version: str = "1.0"):
    return FermentationProtocol(
        winery_id=winery_id,
        varietal_code=varietal_code,
        varietal_name="Pinot Noir",
        color="RED",
        version=version,
        protocol_name=f"Test Protocol {varietal_code} {version}",
        description="Integration test protocol",
        expected_duration_days=28,
        is_active=False,
        created_by_user_id=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def _make_step(protocol_id: int, step_order: int = 1):
    return ProtocolStep(
        protocol_id=protocol_id,
        step_order=step_order,
        step_type="MONITORING",
        description=f"Test step {step_order}",
        expected_day=step_order - 1,
        tolerance_hours=12,
        duration_minutes=30,
        is_critical=False,
        criticality_score=1.0,
        can_repeat_daily=False,
        created_at=datetime.utcnow(),
    )


def _make_execution(
    protocol_id: int,
    fermentation_id: int = 99001,  # fake – cross-module FK removed from DB
    winery_id: int = 99001,        # fake – cross-module FK removed from DB
):
    return ProtocolExecution(
        fermentation_id=fermentation_id,
        protocol_id=protocol_id,
        winery_id=winery_id,
        start_date=datetime.utcnow(),
        status="NOT_STARTED",
        compliance_score=0.0,
        completed_steps=0,
        skipped_critical_steps=0,
        created_at=datetime.utcnow(),
    )


# ─── fermentation_protocols table ───────────────────────────────────────────

@pytest.mark.asyncio
class TestFermentationProtocolsTable:
    """Verify migration 001 created fermentation_protocols correctly."""

    async def test_create_and_retrieve_protocol(self, db_session):
        repo = FermentationProtocolRepository(db_session)
        protocol = _make_protocol(winery_id=1, varietal_code="PN", version="1.0")

        created = await repo.create(protocol)

        assert created.id is not None
        assert created.winery_id == 1
        assert created.varietal_code == "PN"
        assert created.version == "1.0"
        assert created.is_active is False

    async def test_get_by_id(self, db_session):
        repo = FermentationProtocolRepository(db_session)
        protocol = await repo.create(_make_protocol(varietal_code="CS", version="2.0"))

        fetched = await repo.get_by_id(protocol.id)

        assert fetched is not None
        assert fetched.id == protocol.id
        assert fetched.varietal_code == "CS"

    async def test_get_by_winery_varietal_version(self, db_session):
        repo = FermentationProtocolRepository(db_session)
        await repo.create(_make_protocol(winery_id=5, varietal_code="CH", version="3.1"))

        found = await repo.get_by_winery_varietal_version(5, "CH", "3.1")

        assert found is not None
        assert found.winery_id == 5

    async def test_unique_constraint_winery_varietal_version(self, db_session):
        repo = FermentationProtocolRepository(db_session)
        await repo.create(_make_protocol(winery_id=2, varietal_code="MB", version="1.0"))

        with pytest.raises(IntegrityError):
            await repo.create(_make_protocol(winery_id=2, varietal_code="MB", version="1.0"))

    async def test_winery_id_stored_without_fk_constraint(self, db_session):
        """winery_id has no DB-level FK — non-existent winery IDs are accepted."""
        repo = FermentationProtocolRepository(db_session)
        # winery 99999 does not exist in any wineries table — should succeed
        created = await repo.create(
            _make_protocol(winery_id=99999, varietal_code="PN", version="9.9")
        )

        assert created.id is not None
        assert created.winery_id == 99999


# ─── protocol_steps table ────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestProtocolStepsTable:
    """Verify migration 001 created protocol_steps correctly."""

    async def test_create_step(self, db_session):
        proto_repo = FermentationProtocolRepository(db_session)
        step_repo = ProtocolStepRepository(db_session)

        protocol = await proto_repo.create(_make_protocol(varietal_code="GR", version="1.0"))
        step = await step_repo.create(_make_step(protocol.id, step_order=1))

        assert step.id is not None
        assert step.protocol_id == protocol.id
        assert step.step_order == 1

    async def test_get_steps_by_protocol(self, db_session):
        proto_repo = FermentationProtocolRepository(db_session)
        step_repo = ProtocolStepRepository(db_session)

        protocol = await proto_repo.create(_make_protocol(varietal_code="SB", version="1.0"))
        await step_repo.create(_make_step(protocol.id, 1))
        await step_repo.create(_make_step(protocol.id, 2))
        await step_repo.create(_make_step(protocol.id, 3))

        steps = await step_repo.get_by_protocol(protocol.id)

        assert len(steps) == 3
        orders = sorted(s.step_order for s in steps)
        assert orders == [1, 2, 3]

    async def test_step_order_unique_per_protocol(self, db_session):
        proto_repo = FermentationProtocolRepository(db_session)
        step_repo = ProtocolStepRepository(db_session)

        protocol = await proto_repo.create(_make_protocol(varietal_code="ZI", version="1.0"))
        await step_repo.create(_make_step(protocol.id, 1))

        with pytest.raises(IntegrityError):
            await step_repo.create(_make_step(protocol.id, 1))  # duplicate step_order


# ─── protocol_executions table ───────────────────────────────────────────────

@pytest.mark.asyncio
class TestProtocolExecutionsTable:
    """Verify migration 001 created protocol_executions correctly."""

    async def test_create_execution(self, db_session):
        proto_repo = FermentationProtocolRepository(db_session)
        exec_repo = ProtocolExecutionRepository(db_session)

        protocol = await proto_repo.create(_make_protocol(varietal_code="EX", version="1.0"))
        execution = await exec_repo.create(_make_execution(protocol.id))

        assert execution.id is not None
        assert execution.protocol_id == protocol.id
        assert execution.status == "NOT_STARTED"

    async def test_fermentation_id_without_fk_constraint(self, db_session):
        """fermentation_id has no DB-level FK — non-existent fermentation IDs accepted."""
        proto_repo = FermentationProtocolRepository(db_session)
        exec_repo = ProtocolExecutionRepository(db_session)

        protocol = await proto_repo.create(_make_protocol(varietal_code="EX2", version="1.0"))
        execution = await exec_repo.create(
            _make_execution(protocol.id, fermentation_id=88888)
        )

        assert execution.fermentation_id == 88888

    async def test_one_execution_per_fermentation(self, db_session):
        """uq_protocol_executions__fermentation: one execution per fermentation."""
        proto_repo = FermentationProtocolRepository(db_session)
        exec_repo = ProtocolExecutionRepository(db_session)

        protocol = await proto_repo.create(_make_protocol(varietal_code="EX3", version="1.0"))
        await exec_repo.create(_make_execution(protocol.id, fermentation_id=77001))

        with pytest.raises(IntegrityError):
            # same fermentation_id — violates unique constraint
            await exec_repo.create(_make_execution(protocol.id, fermentation_id=77001))


# ─── protocol_alerts table ───────────────────────────────────────────────────

@pytest.mark.asyncio
class TestProtocolAlertsTable:
    """Verify migration 002 created protocol_alerts correctly."""

    async def _setup(self, db_session):
        """Create protocol + execution needed by the alert FK constraints."""
        proto_repo = FermentationProtocolRepository(db_session)
        exec_repo = ProtocolExecutionRepository(db_session)

        protocol = await proto_repo.create(_make_protocol(varietal_code="AL", version="1.0"))
        execution = await exec_repo.create(_make_execution(protocol.id))
        return protocol, execution

    async def test_create_alert(self, db_session):
        alert_repo = ProtocolAlertRepository(db_session)
        protocol, execution = await self._setup(db_session)

        alert = ProtocolAlert(
            execution_id=execution.id,
            protocol_id=protocol.id,
            winery_id=99001,            # no DB FK — any value accepted
            alert_type="STEP_OVERDUE",
            severity="WARNING",
            status="PENDING",
            message="Step is overdue",
            created_at=datetime.utcnow(),
        )
        created = await alert_repo.create(alert)

        assert created.id is not None
        assert created.alert_type == "STEP_OVERDUE"
        assert created.status == "PENDING"

    async def test_get_alerts_by_execution(self, db_session):
        alert_repo = ProtocolAlertRepository(db_session)
        protocol, execution = await self._setup(db_session)

        for i in range(3):
            await alert_repo.create(ProtocolAlert(
                execution_id=execution.id,
                protocol_id=protocol.id,
                winery_id=1,
                alert_type="STEP_OVERDUE",
                severity="WARNING",
                status="PENDING",
                message=f"Alert {i}",
                created_at=datetime.utcnow(),
            ))

        alerts = await alert_repo.get_by_execution(execution.id)
        assert len(alerts) == 3

    async def test_winery_id_without_fk_constraint(self, db_session):
        """winery_id on alerts has no DB-level FK — any value accepted."""
        alert_repo = ProtocolAlertRepository(db_session)
        protocol, execution = await self._setup(db_session)

        alert = ProtocolAlert(
            execution_id=execution.id,
            protocol_id=protocol.id,
            winery_id=55555,            # non-existent winery — OK
            alert_type="CRITICAL_DEVIATION",
            severity="CRITICAL",
            status="PENDING",
            message="Critical deviation detected",
            created_at=datetime.utcnow(),
        )
        created = await alert_repo.create(alert)
        assert created.winery_id == 55555
