"""
Integration tests for AnomalyRepository.

Tests cover all methods of IAnomalyRepository interface with real database operations.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel


@pytest.mark.integration
class TestAnomalyRepositoryCreate:
    """Test anomaly creation."""

    @pytest.mark.asyncio
    async def test_create_anomaly_success(self, anomaly_repository, db_session, winery_id, fermentation_id):
        """Test creating an anomaly."""
        # Create analysis first
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={"type": "test"},
            confidence_level={"score": 0.95}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        # Create anomaly
        anomaly = Anomaly(
            analysis_id=analysis.id,
            sample_id=uuid4(),
            anomaly_type=AnomalyType.STUCK_FERMENTATION.value,
            severity=SeverityLevel.CRITICAL.value,
            description="Fermentation stuck detected",
            deviation_score={"value": 5.2}
        )
        
        created = await anomaly_repository.create(anomaly)
        
        assert created.id == anomaly.id
        assert created.analysis_id == analysis.id
        assert created.anomaly_type == AnomalyType.STUCK_FERMENTATION.value
        assert created.severity == SeverityLevel.CRITICAL.value


@pytest.mark.integration
class TestAnomalyRepositoryGetById:
    """Test anomaly retrieval by ID."""

    @pytest.mark.asyncio
    async def test_get_existing_anomaly(self, anomaly_repository, db_session, winery_id, fermentation_id):
        """Test getting an existing anomaly."""
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        anomaly = Anomaly(
            analysis_id=analysis.id,
            sample_id=uuid4(),
            anomaly_type=AnomalyType.DENSITY_DROP_TOO_FAST.value,
            severity=SeverityLevel.WARNING.value,
            description="Density drop too fast",
            deviation_score={}
        )
        db_session.add(anomaly)
        await db_session.flush()
        
        retrieved = await anomaly_repository.get_by_id(anomaly.id, winery_id)
        
        assert retrieved is not None
        assert retrieved.id == anomaly.id
        assert retrieved.description == "Density drop too fast"

    @pytest.mark.asyncio
    async def test_get_nonexistent_anomaly_returns_none(self, anomaly_repository, winery_id):
        """Test getting a nonexistent anomaly returns None."""
        result = await anomaly_repository.get_by_id(uuid4(), winery_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_anomaly_wrong_winery_returns_none(self, anomaly_repository, db_session, winery_id, fermentation_id):
        """Test that anomalies are isolated by winery."""
        other_winery_id = uuid4()
        
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        anomaly = Anomaly(
            analysis_id=analysis.id,
            sample_id=uuid4(),
            anomaly_type=AnomalyType.UNUSUAL_DURATION.value,
            severity=SeverityLevel.INFO.value,
            description="Unusual duration",
            deviation_score={}
        )
        db_session.add(anomaly)
        await db_session.flush()
        
        result = await anomaly_repository.get_by_id(anomaly.id, other_winery_id)
        
        assert result is None


@pytest.mark.integration
class TestAnomalyRepositoryGetByAnalysis:
    """Test getting anomalies by analysis."""

    @pytest.mark.asyncio
    async def test_get_by_analysis_id(self, anomaly_repository, db_session, winery_id, fermentation_id):
        """Test getting all anomalies for an analysis."""
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        anomaly1 = Anomaly(
            analysis_id=analysis.id,
            sample_id=uuid4(),
            anomaly_type=AnomalyType.STUCK_FERMENTATION.value,
            severity=SeverityLevel.CRITICAL.value,
            description="Anomaly 1",
            deviation_score={}
        )
        anomaly2 = Anomaly(
            analysis_id=analysis.id,
            sample_id=uuid4(),
            anomaly_type=AnomalyType.DENSITY_DROP_TOO_FAST.value,
            severity=SeverityLevel.WARNING.value,
            description="Anomaly 2",
            deviation_score={}
        )
        db_session.add_all([anomaly1, anomaly2])
        await db_session.flush()
        
        anomalies = await anomaly_repository.get_by_analysis_id(analysis.id)
        
        assert len(anomalies) == 2
        assert any(a.description == "Anomaly 1" for a in anomalies)
        assert any(a.description == "Anomaly 2" for a in anomalies)


@pytest.mark.integration
class TestAnomalyRepositoryListUnresolved:
    """Test listing unresolved anomalies."""

    @pytest.mark.asyncio
    async def test_list_unresolved(self, anomaly_repository, db_session, winery_id, fermentation_id):
        """Test listing unresolved anomalies."""
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        unresolved = Anomaly(
            analysis_id=analysis.id,
            sample_id=uuid4(),
            anomaly_type=AnomalyType.STUCK_FERMENTATION.value,
            severity=SeverityLevel.CRITICAL.value,
            description="Unresolved",
            deviation_score={},
            is_resolved=False
        )
        resolved = Anomaly(
            analysis_id=analysis.id,
            sample_id=uuid4(),
            anomaly_type=AnomalyType.UNUSUAL_DURATION.value,
            severity=SeverityLevel.INFO.value,
            description="Resolved",
            deviation_score={},
            is_resolved=True,
            resolved_at=datetime.now(timezone.utc)
        )
        db_session.add_all([unresolved, resolved])
        await db_session.flush()
        
        anomalies = await anomaly_repository.list_unresolved(winery_id, limit=100)
        
        assert len(anomalies) == 1
        assert anomalies[0].description == "Unresolved"
        assert not anomalies[0].is_resolved


@pytest.mark.integration
class TestAnomalyRepositoryBySeverity:
    """Test filtering anomalies by severity."""

    @pytest.mark.asyncio
    async def test_list_by_severity(self, anomaly_repository, db_session, winery_id, fermentation_id):
        """Test listing anomalies by severity."""
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        critical_severity = Anomaly(
            analysis_id=analysis.id,
            sample_id=uuid4(),
            anomaly_type=AnomalyType.STUCK_FERMENTATION.value,
            severity=SeverityLevel.CRITICAL.value,
            description="Critical severity",
            deviation_score={}
        )
        info_severity = Anomaly(
            analysis_id=analysis.id,
            sample_id=uuid4(),
            anomaly_type=AnomalyType.UNUSUAL_DURATION.value,
            severity=SeverityLevel.INFO.value,
            description="Info severity",
            deviation_score={}
        )
        db_session.add_all([critical_severity, info_severity])
        await db_session.flush()
        
        critical_anomalies = await anomaly_repository.list_by_severity(winery_id, SeverityLevel.CRITICAL, limit=100)
        
        assert len(critical_anomalies) == 1
        assert critical_anomalies[0].severity == SeverityLevel.CRITICAL.value


@pytest.mark.integration
class TestAnomalyRepositoryExists:
    """Test existence checking."""

    @pytest.mark.asyncio
    async def test_exists_returns_true(self, anomaly_repository, db_session, winery_id, fermentation_id):
        """Test exists returns true for existing anomaly."""
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        anomaly = Anomaly(
            analysis_id=analysis.id,
            sample_id=uuid4(),
            anomaly_type=AnomalyType.STUCK_FERMENTATION.value,
            severity=SeverityLevel.CRITICAL.value,
            description="Test",
            deviation_score={}
        )
        db_session.add(anomaly)
        await db_session.flush()
        
        exists = await anomaly_repository.exists(anomaly.id, winery_id)
        
        assert exists is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_nonexistent(self, anomaly_repository, winery_id):
        """Test exists returns false for nonexistent anomaly."""
        exists = await anomaly_repository.exists(uuid4(), winery_id)
        
        assert exists is False
