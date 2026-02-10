"""
Tests for Protocol Domain Entities

Validates entity structure, relationships, and constraints.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, MetaData
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from src.shared.infra.orm.base_entity import BaseEntity
from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion
from src.modules.fermentation.src.domain.enums.step_type import StepType, ProtocolExecutionStatus, SkipReason


# Create minimal mock tables for foreign keys
MockBase = declarative_base()

class MockWinery(MockBase):
    __tablename__ = 'wineries'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

class MockFermentation(MockBase):
    __tablename__ = 'fermentations'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

class MockUser(MockBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))


# Test database setup
@pytest.fixture(scope="session")
def test_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    # Create mock foreign key tables first
    MockBase.metadata.create_all(engine)
    # Then create domain entity tables
    BaseEntity.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create session factory"""
    return sessionmaker(bind=test_engine)


@pytest.fixture
def session(test_session_factory):
    """Create session for each test with rollback for isolation"""
    connection = test_session_factory.kw['bind'].connect()
    transaction = connection.begin()
    session = test_session_factory()
    
    # Create mock data in test session
    winery = MockWinery(id=1, name="Test Winery")
    fermentation = MockFermentation(id=1, name="Test Fermentation")
    user = MockUser(id=1, name="Test User")
    session.add(winery)
    session.add(fermentation)
    session.add(user)
    session.commit()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


# Fixtures for test data
@pytest.fixture
def mock_winery_id():
    """Mock winery ID"""
    return 1


@pytest.fixture
def mock_user_id():
    """Mock user ID"""
    return 1


@pytest.fixture
def mock_fermentation_id():
    """Mock fermentation ID"""
    return 1


@pytest.fixture
def fermentation_protocol(session, mock_winery_id, mock_user_id):
    """Create a test protocol"""
    protocol = FermentationProtocol(
        winery_id=mock_winery_id,
        created_by_user_id=mock_user_id,
        varietal_code="PN",
        varietal_name="Pinot Noir",
        color="RED",
        protocol_name="PN-2021-Standard",
        version="1.0",
        description="Standard Pinot Noir protocol",
        expected_duration_days=20,
        is_active=True,
    )
    session.add(protocol)
    session.commit()
    return protocol


@pytest.fixture
def protocol_step(session, fermentation_protocol):
    """Create a test protocol step"""
    step = ProtocolStep(
        protocol_id=fermentation_protocol.id,
        step_order=1,
        step_type=StepType.YEAST_INOCULATION,
        description="Inoculate with yeast",
        expected_day=0,
        tolerance_hours=2,
        duration_minutes=120,
        is_critical=True,
        criticality_score=100.0,
        can_repeat_daily=False,
    )
    session.add(step)
    session.commit()
    return step


@pytest.fixture
def protocol_execution(session, fermentation_protocol, mock_winery_id):
    """Create a test protocol execution"""
    # Note: fermentation_id would normally link to a Fermentation,
    # but we're testing without the full database
    execution = ProtocolExecution(
        fermentation_id=999,  # Mock ID
        protocol_id=fermentation_protocol.id,
        winery_id=mock_winery_id,
        start_date=datetime.utcnow(),
        status=ProtocolExecutionStatus.ACTIVE,
        compliance_score=0.0,
        completed_steps=0,
        skipped_critical_steps=0,
    )
    session.add(execution)
    session.commit()
    return execution


# Entity Tests
class TestFermentationProtocol:
    """Tests for FermentationProtocol entity"""
    
    def test_create_protocol(self, fermentation_protocol):
        """Test protocol creation"""
        assert fermentation_protocol.id is not None
        assert fermentation_protocol.varietal_code == "PN"
        assert fermentation_protocol.protocol_name == "PN-2021-Standard"
        assert fermentation_protocol.is_active is True
        assert fermentation_protocol.color == "RED"
    
    def test_protocol_unique_constraint(self, session, fermentation_protocol, mock_winery_id, mock_user_id):
        """Test that (winery, varietal, version) is unique"""
        duplicate = FermentationProtocol(
            winery_id=mock_winery_id,
            created_by_user_id=mock_user_id,
            varietal_code="PN",
            varietal_name="Pinot Noir",
            color="RED",
            protocol_name="PN-2021-Alt",
            version="1.0",  # Same version
            expected_duration_days=20,
        )
        session.add(duplicate)
        
        with pytest.raises(Exception):  # IntegrityError
            session.commit()
    
    def test_protocol_timestamps(self, fermentation_protocol):
        """Test created_at and updated_at timestamps"""
        assert fermentation_protocol.created_at is not None
        assert fermentation_protocol.updated_at is not None
        assert isinstance(fermentation_protocol.created_at, datetime)
    
    def test_protocol_expected_duration_positive(self, session, mock_winery_id, mock_user_id):
        """Test expected_duration_days must be positive"""
        invalid = FermentationProtocol(
            winery_id=mock_winery_id,
            created_by_user_id=mock_user_id,
            varietal_code="CS",
            varietal_name="Cabernet",
            color="RED",
            protocol_name="CS-2021",
            version="1.0",
            expected_duration_days=-5,  # Invalid
        )
        session.add(invalid)
        
        with pytest.raises(Exception):  # CheckConstraint violation
            session.commit()


class TestProtocolStep:
    """Tests for ProtocolStep entity"""
    
    def test_create_step(self, protocol_step):
        """Test step creation"""
        assert protocol_step.id is not None
        assert protocol_step.step_order == 1
        assert protocol_step.step_type == StepType.YEAST_INOCULATION
        assert protocol_step.expected_day == 0
        assert protocol_step.is_critical is True
        assert protocol_step.criticality_score == 100.0
    
    def test_step_unique_order_per_protocol(self, session, fermentation_protocol, protocol_step):
        """Test (protocol_id, step_order) is unique"""
        duplicate = ProtocolStep(
            protocol_id=fermentation_protocol.id,
            step_order=1,  # Same order
            step_type=StepType.H2S_CHECK,
            description="H2S check",
            expected_day=1,
            tolerance_hours=6,
            is_critical=True,
        )
        session.add(duplicate)
        
        with pytest.raises(Exception):
            session.commit()
    
    def test_step_criticality_score_range(self, session, fermentation_protocol):
        """Test criticality_score must be 0-100"""
        invalid_high = ProtocolStep(
            protocol_id=fermentation_protocol.id,
            step_order=2,
            step_type=StepType.BRIX_READING,
            description="Brix",
            expected_day=1,
            criticality_score=150,  # Invalid
        )
        session.add(invalid_high)
        
        with pytest.raises(Exception):
            session.commit()
    
    def test_step_can_repeat_daily(self, session, fermentation_protocol):
        """Test can_repeat_daily flag"""
        repeatable = ProtocolStep(
            protocol_id=fermentation_protocol.id,
            step_order=2,
            step_type=StepType.TEMPERATURE_CHECK,
            description="Temperature check",
            expected_day=1,
            can_repeat_daily=True,  # Can do 2x/day
            is_critical=False,
        )
        session.add(repeatable)
        session.commit()
        
        assert repeatable.can_repeat_daily is True


class TestProtocolExecution:
    """Tests for ProtocolExecution entity"""
    
    def test_create_execution(self, protocol_execution):
        """Test execution creation"""
        assert protocol_execution.id is not None
        assert protocol_execution.status == ProtocolExecutionStatus.ACTIVE
        assert protocol_execution.compliance_score == 0.0
        assert protocol_execution.completed_steps == 0
    
    def test_execution_compliance_score_range(self, session, fermentation_protocol, mock_winery_id):
        """Test compliance_score must be 0-100"""
        invalid = ProtocolExecution(
            fermentation_id=888,
            protocol_id=fermentation_protocol.id,
            winery_id=mock_winery_id,
            start_date=datetime.utcnow(),
            status=ProtocolExecutionStatus.ACTIVE,
            compliance_score=150,  # Invalid
        )
        session.add(invalid)
        
        with pytest.raises(Exception):
            session.commit()
    
    def test_execution_status_values(self, session, fermentation_protocol, mock_winery_id):
        """Test all valid execution statuses"""
        for status in ProtocolExecutionStatus:
            exec = ProtocolExecution(
                fermentation_id=777,
                protocol_id=fermentation_protocol.id,
                winery_id=mock_winery_id,
                start_date=datetime.utcnow(),
                status=status,
            )
            session.add(exec)
        
        session.commit()
        # Should complete without error


class TestStepCompletion:
    """Tests for StepCompletion entity"""
    
    def test_create_completion(self, session, protocol_execution, protocol_step, mock_user_id):
        """Test step completion creation"""
        completion = StepCompletion(
            execution_id=protocol_execution.id,
            step_id=protocol_step.id,
            completed_at=datetime.utcnow(),
            notes="Completed on time",
            is_on_schedule=True,
            days_late=0,
            verified_by_user_id=mock_user_id,
        )
        session.add(completion)
        session.commit()
        
        assert completion.id is not None
        assert completion.was_skipped is False
    
    def test_create_skip(self, session, protocol_execution, protocol_step, mock_user_id):
        """Test step skip creation"""
        skip = StepCompletion(
            execution_id=protocol_execution.id,
            step_id=protocol_step.id,
            was_skipped=True,
            skip_reason=SkipReason.EQUIPMENT_FAILURE,
            skip_notes="Equipment down for maintenance",
            verified_by_user_id=mock_user_id,
        )
        session.add(skip)
        session.commit()
        
        assert skip.was_skipped is True
        assert skip.skip_reason == SkipReason.EQUIPMENT_FAILURE
        assert skip.completed_at is None
    
    def test_completion_xor_skip_constraint(self, session, protocol_execution, protocol_step):
        """Test that completion and skip are mutually exclusive"""
        # Both completed AND skipped - should fail
        invalid = StepCompletion(
            execution_id=protocol_execution.id,
            step_id=protocol_step.id,
            completed_at=datetime.utcnow(),
            was_skipped=True,
            skip_reason=SkipReason.OTHER,
        )
        session.add(invalid)
        
        with pytest.raises(Exception):
            session.commit()
    
    def test_skip_requires_reason(self, session, protocol_execution, protocol_step):
        """Test that skipped steps must have a reason"""
        invalid = StepCompletion(
            execution_id=protocol_execution.id,
            step_id=protocol_step.id,
            was_skipped=True,
            skip_reason=None,  # Missing reason
        )
        session.add(invalid)
        
        with pytest.raises(Exception):
            session.commit()


# Enum Tests
class TestEnums:
    """Tests for Protocol enums"""
    
    def test_step_type_enum_values(self):
        """Test all StepType values are defined"""
        expected_types = {
            "YEAST_INOCULATION", "COLD_SOAK", "TEMPERATURE_CHECK", "H2S_CHECK",
            "BRIX_READING", "VISUAL_INSPECTION", "DAP_ADDITION", "NUTRIENT_ADDITION",
            "SO2_ADDITION", "MLF_INOCULATION", "PUNCH_DOWN", "PUMP_OVER",
            "PRESSING", "EXTENDED_MACERATION", "SETTLING", "RACKING",
            "FILTERING", "CLARIFICATION", "CATA_TASTING"
        }
        actual_types = {member.value for member in StepType}
        assert expected_types == actual_types
    
    def test_execution_status_enum_values(self):
        """Test all ProtocolExecutionStatus values"""
        expected = {"NOT_STARTED", "ACTIVE", "PAUSED", "COMPLETED", "ABANDONED"}
        actual = {member.value for member in ProtocolExecutionStatus}
        assert expected == actual
    
    def test_skip_reason_enum_values(self):
        """Test all SkipReason values"""
        expected = {
            "EQUIPMENT_FAILURE", "CONDITION_NOT_MET", "FERMENTATION_ENDED",
            "FERMENTATION_FAILED", "WINEMAKER_DECISION", "REPLACED_BY_ALTERNATIVE", "OTHER"
        }
        actual = {member.value for member in SkipReason}
        assert expected == actual


# Relationship Tests
class TestRelationships:
    """Tests for entity relationships"""
    
    def test_protocol_has_steps(self, session, fermentation_protocol):
        """Test protocol can have multiple steps"""
        step1 = ProtocolStep(
            protocol_id=fermentation_protocol.id,
            step_order=1,
            step_type=StepType.YEAST_INOCULATION,
            description="Inoculate",
            expected_day=0,
        )
        step2 = ProtocolStep(
            protocol_id=fermentation_protocol.id,
            step_order=2,
            step_type=StepType.BRIX_READING,
            description="Check brix",
            expected_day=1,
        )
        session.add_all([step1, step2])
        session.commit()
        
        # Refresh to get relationships
        session.refresh(fermentation_protocol)
        assert len(fermentation_protocol.steps) == 2 + 1  # +1 from earlier fixture
    
    def test_execution_has_completions(self, session, protocol_execution, protocol_step):
        """Test execution can have multiple completions"""
        completion1 = StepCompletion(
            execution_id=protocol_execution.id,
            step_id=protocol_step.id,
            completed_at=datetime.utcnow(),
            is_on_schedule=True,
        )
        completion2 = StepCompletion(
            execution_id=protocol_execution.id,
            step_id=protocol_step.id,
            completed_at=datetime.utcnow(),
            is_on_schedule=True,
        )
        session.add_all([completion1, completion2])
        session.commit()
        
        session.refresh(protocol_execution)
        assert len(protocol_execution.completions) == 2
