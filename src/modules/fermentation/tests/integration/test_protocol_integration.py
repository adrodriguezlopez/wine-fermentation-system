"""
Integration Tests for Protocol Engine (ADR-035)

Tests for:
1. Domain entity relationships and constraints
2. Repository CRUD operations
3. Complex queries (get_active_by_winery, get_by_status, etc.)
4. Data loading and seeding
5. Constraint enforcement
6. Real protocol data integrity
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion
from src.modules.fermentation.src.domain.enums.step_type import StepType, ProtocolExecutionStatus, SkipReason
from src.modules.fermentation.src.repository_component.fermentation_protocol_repository import (
    FermentationProtocolRepository
)
from src.modules.fermentation.src.repository_component.protocol_step_repository import (
    ProtocolStepRepository
)
from src.modules.fermentation.src.repository_component.protocol_execution_repository import (
    ProtocolExecutionRepository
)
from src.modules.fermentation.src.repository_component.step_completion_repository import (
    StepCompletionRepository
)


@pytest.fixture
async def db_engine() -> AsyncEngine:
    """Create test database engine with in-memory SQLite"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        from src.shared.domain.entities.base_entity import BaseEntity
        await conn.run_sync(BaseEntity.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def async_session_factory(db_engine: AsyncEngine):
    """Create async session factory"""
    return sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        future=True
    )


@pytest.fixture
async def session(async_session_factory) -> AsyncSession:
    """Create async session for test"""
    async with async_session_factory() as sess:
        yield sess


# ============================================================================
# FERMENTATION PROTOCOL REPOSITORY TESTS
# ============================================================================

class TestFermentationProtocolRepository:
    """Integration tests for FermentationProtocolRepository"""
    
    async def test_create_protocol(self, session: AsyncSession):
        """Should create a protocol with all required fields"""
        repo = FermentationProtocolRepository(session)
        
        protocol = FermentationProtocol(
            winery_id=1,
            varietal="Pinot Noir",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True,
            description="Test protocol"
        )
        
        created = await repo.create(protocol)
        assert created.id is not None
        assert created.varietal == "Pinot Noir"
        
    async def test_get_protocol_by_id(self, session: AsyncSession):
        """Should retrieve protocol by ID"""
        repo = FermentationProtocolRepository(session)
        
        protocol = FermentationProtocol(
            winery_id=1,
            varietal="Chardonnay",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        created = await repo.create(protocol)
        retrieved = await repo.get_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.varietal == "Chardonnay"
    
    async def test_get_nonexistent_protocol_returns_none(self, session: AsyncSession):
        """Should return None for nonexistent protocol"""
        repo = FermentationProtocolRepository(session)
        result = await repo.get_by_id(9999)
        assert result is None
    
    async def test_get_all_protocols(self, session: AsyncSession):
        """Should retrieve all protocols"""
        repo = FermentationProtocolRepository(session)
        
        for i in range(3):
            protocol = FermentationProtocol(
                winery_id=1,
                varietal=f"Varietal-{i}",
                vintage_year=2021,
                version=1,
                created_by=1,
                created_at=datetime.utcnow(),
                is_active=True
            )
            await repo.create(protocol)
        
        all_protocols = await repo.get_all()
        assert len(all_protocols) == 3
    
    async def test_update_protocol(self, session: AsyncSession):
        """Should update protocol"""
        repo = FermentationProtocolRepository(session)
        
        protocol = FermentationProtocol(
            winery_id=1,
            varietal="Cabernet",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        created = await repo.create(protocol)
        created.is_active = False
        
        updated = await repo.update(created)
        assert updated.is_active is False
    
    async def test_delete_protocol(self, session: AsyncSession):
        """Should delete protocol by ID"""
        repo = FermentationProtocolRepository(session)
        
        protocol = FermentationProtocol(
            winery_id=1,
            varietal="Merlot",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        created = await repo.create(protocol)
        deleted = await repo.delete(created.id)
        
        assert deleted is True
        retrieved = await repo.get_by_id(created.id)
        assert retrieved is None
    
    async def test_get_by_winery_varietal_version(self, session: AsyncSession):
        """Should find protocol by winery, varietal, and version"""
        repo = FermentationProtocolRepository(session)
        
        protocol = FermentationProtocol(
            winery_id=1,
            varietal="Pinot Noir",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        created = await repo.create(protocol)
        retrieved = await repo.get_by_winery_varietal_version(
            winery_id=1,
            varietal="Pinot Noir",
            vintage_year=2021,
            version=1
        )
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    async def test_get_active_by_winery(self, session: AsyncSession):
        """Should get only active protocols for winery"""
        repo = FermentationProtocolRepository(session)
        
        # Create active protocol
        active = FermentationProtocol(
            winery_id=1,
            varietal="Active",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True
        )
        await repo.create(active)
        
        # Create inactive protocol
        inactive = FermentationProtocol(
            winery_id=1,
            varietal="Inactive",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=False
        )
        await repo.create(inactive)
        
        active_protocols = await repo.get_active_by_winery(winery_id=1)
        assert len(active_protocols) == 1
        assert active_protocols[0].varietal == "Active"
    
    async def test_get_by_varietal(self, session: AsyncSession):
        """Should get all versions of a varietal, ordered by version desc"""
        repo = FermentationProtocolRepository(session)
        
        # Create multiple versions
        for version in [1, 2, 3]:
            protocol = FermentationProtocol(
                winery_id=1,
                varietal="Syrah",
                vintage_year=2021,
                version=version,
                created_by=1,
                created_at=datetime.utcnow(),
                is_active=True
            )
            await repo.create(protocol)
        
        versions = await repo.get_by_varietal(winery_id=1, varietal_code="Syrah")
        
        # Should be ordered by version descending
        assert len(versions) == 3
        assert versions[0].version == 3
        assert versions[1].version == 2
        assert versions[2].version == 1


# ============================================================================
# PROTOCOL STEP REPOSITORY TESTS
# ============================================================================

class TestProtocolStepRepository:
    """Integration tests for ProtocolStepRepository"""
    
    async def test_create_step(self, session: AsyncSession):
        """Should create a protocol step"""
        # Create protocol first
        protocol_repo = FermentationProtocolRepository(session)
        protocol = FermentationProtocol(
            winery_id=1,
            varietal="Pinot Noir",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True
        )
        created_protocol = await protocol_repo.create(protocol)
        
        # Create step
        step_repo = ProtocolStepRepository(session)
        step = ProtocolStep(
            protocol_id=created_protocol.id,
            step_order=1,
            step_type=StepType.YEAST_INOCULATION,
            description="Inoculate with yeast",
            is_critical=True,
            can_skip=False,
            created_at=datetime.utcnow()
        )
        
        created_step = await step_repo.create(step)
        assert created_step.id is not None
        assert created_step.step_order == 1
    
    async def test_get_steps_by_protocol(self, session: AsyncSession):
        """Should get all steps for a protocol ordered by step_order"""
        # Create protocol
        protocol_repo = FermentationProtocolRepository(session)
        protocol = FermentationProtocol(
            winery_id=1,
            varietal="Chardonnay",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True
        )
        created_protocol = await protocol_repo.create(protocol)
        
        # Create steps in random order
        step_repo = ProtocolStepRepository(session)
        for order in [3, 1, 2]:
            step = ProtocolStep(
                protocol_id=created_protocol.id,
                step_order=order,
                step_type=StepType.TEMPERATURE_CHECK,
                description=f"Step {order}",
                is_critical=False,
                can_skip=True,
                created_at=datetime.utcnow()
            )
            await step_repo.create(step)
        
        # Retrieve and check ordering
        steps = await step_repo.get_by_protocol(created_protocol.id)
        
        assert len(steps) == 3
        assert steps[0].step_order == 1
        assert steps[1].step_order == 2
        assert steps[2].step_order == 3
    
    async def test_get_step_by_order(self, session: AsyncSession):
        """Should get specific step by order within protocol"""
        # Create protocol
        protocol_repo = FermentationProtocolRepository(session)
        protocol = FermentationProtocol(
            winery_id=1,
            varietal="Merlot",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True
        )
        created_protocol = await protocol_repo.create(protocol)
        
        # Create step
        step_repo = ProtocolStepRepository(session)
        step = ProtocolStep(
            protocol_id=created_protocol.id,
            step_order=5,
            step_type=StepType.BRIX_READING,
            description="Check Brix",
            is_critical=True,
            can_skip=False,
            created_at=datetime.utcnow()
        )
        created_step = await step_repo.create(step)
        
        # Retrieve by order
        retrieved = await step_repo.get_by_order(created_protocol.id, 5)
        
        assert retrieved is not None
        assert retrieved.id == created_step.id
        assert retrieved.step_order == 5


# ============================================================================
# PROTOCOL EXECUTION REPOSITORY TESTS
# ============================================================================

class TestProtocolExecutionRepository:
    """Integration tests for ProtocolExecutionRepository"""
    
    async def test_create_execution(self, session: AsyncSession):
        """Should create a protocol execution"""
        exec_repo = ProtocolExecutionRepository(session)
        
        execution = ProtocolExecution(
            fermentation_id=1,
            protocol_id=1,
            winery_id=1,
            status=ProtocolExecutionStatus.NOT_STARTED,
            total_steps=20,
            created_at=datetime.utcnow()
        )
        
        created = await exec_repo.create(execution)
        assert created.id is not None
        assert created.status == ProtocolExecutionStatus.NOT_STARTED
    
    async def test_get_execution_by_fermentation(self, session: AsyncSession):
        """Should get execution for fermentation (unique relationship)"""
        exec_repo = ProtocolExecutionRepository(session)
        
        execution = ProtocolExecution(
            fermentation_id=42,
            protocol_id=1,
            winery_id=1,
            status=ProtocolExecutionStatus.ACTIVE,
            total_steps=20,
            created_at=datetime.utcnow()
        )
        
        created = await exec_repo.create(execution)
        retrieved = await exec_repo.get_by_fermentation(fermentation_id=42)
        
        assert retrieved is not None
        assert retrieved.id == created.id
    
    async def test_get_executions_by_status(self, session: AsyncSession):
        """Should get all executions with specific status"""
        exec_repo = ProtocolExecutionRepository(session)
        
        # Create executions with different statuses
        for i, status in enumerate([ProtocolExecutionStatus.ACTIVE, ProtocolExecutionStatus.PAUSED]):
            execution = ProtocolExecution(
                fermentation_id=i + 1,
                protocol_id=1,
                winery_id=1,
                status=status,
                total_steps=20,
                created_at=datetime.utcnow()
            )
            await exec_repo.create(execution)
        
        # Get active executions
        active = await exec_repo.get_by_status(ProtocolExecutionStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].status == ProtocolExecutionStatus.ACTIVE
    
    async def test_get_active_executions_by_winery(self, session: AsyncSession):
        """Should get only active and paused executions for winery"""
        exec_repo = ProtocolExecutionRepository(session)
        
        # Create various executions
        statuses = [
            ProtocolExecutionStatus.ACTIVE,
            ProtocolExecutionStatus.PAUSED,
            ProtocolExecutionStatus.COMPLETED,
            ProtocolExecutionStatus.NOT_STARTED
        ]
        
        for i, status in enumerate(statuses):
            execution = ProtocolExecution(
                fermentation_id=i + 1,
                protocol_id=1,
                winery_id=1,
                status=status,
                total_steps=20,
                created_at=datetime.utcnow()
            )
            await exec_repo.create(execution)
        
        # Get active executions for winery
        active = await exec_repo.get_active_by_winery(winery_id=1)
        
        # Should only return ACTIVE and PAUSED
        assert len(active) == 2
        assert all(e.status in [ProtocolExecutionStatus.ACTIVE, ProtocolExecutionStatus.PAUSED] 
                  for e in active)


# ============================================================================
# STEP COMPLETION REPOSITORY TESTS
# ============================================================================

class TestStepCompletionRepository:
    """Integration tests for StepCompletionRepository"""
    
    async def test_record_completion(self, session: AsyncSession):
        """Should record a step completion"""
        comp_repo = StepCompletionRepository(session)
        
        completion = await comp_repo.record_completion(
            execution_id=1,
            step_id=1,
            completed_by=1,
            notes="Step completed successfully"
        )
        
        assert completion.id is not None
        assert completion.is_skipped is False
        assert completion.skip_reason is None
    
    async def test_record_skip(self, session: AsyncSession):
        """Should record a step skip"""
        comp_repo = StepCompletionRepository(session)
        
        completion = await comp_repo.record_skip(
            execution_id=1,
            step_id=1,
            reason=SkipReason.EQUIPMENT_FAILURE,
            skipped_by=1,
            notes="Equipment broken"
        )
        
        assert completion.is_skipped is True
        assert completion.skip_reason == SkipReason.EQUIPMENT_FAILURE
    
    async def test_get_completions_by_execution(self, session: AsyncSession):
        """Should get all completions for an execution"""
        comp_repo = StepCompletionRepository(session)
        
        # Record completions
        for step_id in [1, 2, 3]:
            await comp_repo.record_completion(
                execution_id=1,
                step_id=step_id,
                completed_by=1
            )
        
        completions = await comp_repo.get_by_execution(execution_id=1)
        assert len(completions) == 3
    
    async def test_get_completions_by_step(self, session: AsyncSession):
        """Should get all completions across executions for a step"""
        comp_repo = StepCompletionRepository(session)
        
        # Record completions for step 1 across multiple executions
        for exec_id in [1, 2, 3]:
            await comp_repo.record_completion(
                execution_id=exec_id,
                step_id=1,
                completed_by=1
            )
        
        completions = await comp_repo.get_by_step(step_id=1)
        assert len(completions) == 3
    
    async def test_unique_execution_step_constraint(self, session: AsyncSession):
        """Should enforce unique constraint on execution_id + step_id"""
        comp_repo = StepCompletionRepository(session)
        
        # Record completion
        await comp_repo.record_completion(
            execution_id=1,
            step_id=1,
            completed_by=1
        )
        
        # Try to create duplicate (should fail)
        with pytest.raises(IntegrityError):
            await comp_repo.create(StepCompletion(
                execution_id=1,
                step_id=1,
                completed_by=1,
                is_skipped=False,
                created_at=datetime.utcnow()
            ))
            await session.flush()


# ============================================================================
# COMPLEX WORKFLOW TESTS
# ============================================================================

class TestComplexWorkflows:
    """Integration tests for complete workflows"""
    
    async def test_full_protocol_execution_workflow(self, session: AsyncSession):
        """Test complete workflow: create protocol -> add steps -> execute -> record completions"""
        
        # Step 1: Create protocol
        protocol_repo = FermentationProtocolRepository(session)
        protocol = FermentationProtocol(
            winery_id=1,
            varietal="Pinot Noir",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True,
            description="Test workflow"
        )
        created_protocol = await protocol_repo.create(protocol)
        
        # Step 2: Add steps to protocol
        step_repo = ProtocolStepRepository(session)
        for i in range(1, 6):
            step = ProtocolStep(
                protocol_id=created_protocol.id,
                step_order=i,
                step_type=StepType.TEMPERATURE_CHECK,
                description=f"Step {i}",
                is_critical=(i % 2 == 0),
                can_skip=(i % 2 == 1),
                created_at=datetime.utcnow()
            )
            await step_repo.create(step)
        
        # Step 3: Create execution
        exec_repo = ProtocolExecutionRepository(session)
        execution = ProtocolExecution(
            fermentation_id=100,
            protocol_id=created_protocol.id,
            winery_id=1,
            status=ProtocolExecutionStatus.ACTIVE,
            total_steps=5,
            created_at=datetime.utcnow()
        )
        created_execution = await exec_repo.create(execution)
        
        # Step 4: Record step completions
        comp_repo = StepCompletionRepository(session)
        for i in range(1, 4):
            await comp_repo.record_completion(
                execution_id=created_execution.id,
                step_id=i,
                completed_by=1
            )
        
        # Step 5: Record a skip
        await comp_repo.record_skip(
            execution_id=created_execution.id,
            step_id=4,
            reason=SkipReason.WEATHER_CONDITIONS,
            skipped_by=1
        )
        
        # Verify final state
        completions = await comp_repo.get_by_execution(created_execution.id)
        assert len(completions) == 4
        
        skipped = [c for c in completions if c.is_skipped]
        assert len(skipped) == 1
        assert skipped[0].skip_reason == SkipReason.WEATHER_CONDITIONS


# ============================================================================
# CONSTRAINT AND VALIDATION TESTS
# ============================================================================

class TestConstraints:
    """Test database constraints and validations"""
    
    async def test_protocol_unique_constraint(self, session: AsyncSession):
        """Should enforce unique constraint on winery + varietal + vintage + version"""
        repo = FermentationProtocolRepository(session)
        
        # Create first protocol
        protocol1 = FermentationProtocol(
            winery_id=1,
            varietal="Pinot Noir",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True
        )
        await repo.create(protocol1)
        
        # Try to create duplicate
        protocol2 = FermentationProtocol(
            winery_id=1,
            varietal="Pinot Noir",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        with pytest.raises(IntegrityError):
            await repo.create(protocol2)
            await session.flush()
    
    async def test_step_unique_constraint(self, session: AsyncSession):
        """Should enforce unique constraint on protocol_id + step_order"""
        # Create protocol
        protocol_repo = FermentationProtocolRepository(session)
        protocol = FermentationProtocol(
            winery_id=1,
            varietal="Chardonnay",
            vintage_year=2021,
            version=1,
            created_by=1,
            created_at=datetime.utcnow(),
            is_active=True
        )
        created_protocol = await protocol_repo.create(protocol)
        
        # Create first step
        step_repo = ProtocolStepRepository(session)
        step1 = ProtocolStep(
            protocol_id=created_protocol.id,
            step_order=1,
            step_type=StepType.YEAST_INOCULATION,
            description="Step 1",
            is_critical=True,
            can_skip=False,
            created_at=datetime.utcnow()
        )
        await step_repo.create(step1)
        
        # Try to create duplicate order
        step2 = ProtocolStep(
            protocol_id=created_protocol.id,
            step_order=1,
            step_type=StepType.TEMPERATURE_CHECK,
            description="Step 1 duplicate",
            is_critical=False,
            can_skip=True,
            created_at=datetime.utcnow()
        )
        
        with pytest.raises(IntegrityError):
            await step_repo.create(step2)
            await session.flush()
