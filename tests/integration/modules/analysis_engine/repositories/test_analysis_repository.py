"""
Integration tests for AnalysisRepository.
Following the same pattern as fermentation module integration tests.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

# Note: AnalysisRepository is injected via analysis_repository fixture from conftest.py
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus


@pytest.mark.asyncio
class TestAnalysisRepositoryCreate:
    """Tests for creating analysis records."""
    
    async def test_create_analysis_success(self, analysis_repository, db_session):
        """Should create analysis with valid data."""
        fermentation_id = uuid4()
        winery_id = uuid4()
        
        comparison_result_data = {
            "historical_samples_count": 20,
            "similarity_score": 85.5,
            "statistical_metrics": {"mean": 12.5},
            "comparison_criteria": {"varietal": "Malbec"},
            "patterns_used": [1, 2, 3],
            "compared_at": datetime.now(timezone.utc).isoformat()
        }
        
        confidence_level_data = {
            "level": "HIGH",
            "historical_samples_count": 20,
            "similarity_score": 85.5,
            "explanation": "Based on 20 similar fermentations"
        }
        
        analysis = await analysis_repository.create(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            comparison_result=comparison_result_data,
            confidence_level=confidence_level_data
        )
        
        assert analysis.id is not None
        assert analysis.fermentation_id == fermentation_id
        assert analysis.winery_id == winery_id
        assert analysis.status == AnalysisStatus.PENDING.value
        assert analysis.comparison_result == comparison_result_data
        assert analysis.confidence_level == confidence_level_data
    
    async def test_create_analysis_generates_unique_ids(self, analysis_repository, db_session):
        """Should generate unique IDs for each analysis."""
        fermentation_id = uuid4()
        winery_id = uuid4()
        
        data = {
            "comparison_result": {
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "statistical_metrics": {},
                "comparison_criteria": {},
                "patterns_used": [],
                "compared_at": datetime.now(timezone.utc).isoformat()
            },
            "confidence_level": {
                "level": "MEDIUM",
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "explanation": "Test"
            }
        }
        
        analysis1 = await analysis_repository.create(fermentation_id, winery_id, **data)
        analysis2 = await analysis_repository.create(fermentation_id, winery_id, **data)
        
        assert analysis1.id != analysis2.id


@pytest.mark.asyncio
class TestAnalysisRepositoryGetById:
    """Tests for retrieving analysis by ID."""
    
    async def test_get_existing_analysis(self, analysis_repository, db_session):
        """Should retrieve existing analysis."""
        fermentation_id = uuid4()
        winery_id = uuid4()
        
        # Create analysis first
        created = await analysis_repository.create(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            comparison_result={
                "historical_samples_count": 15,
                "similarity_score": 80.0,
                "statistical_metrics": {},
                "comparison_criteria": {},
                "patterns_used": [],
                "compared_at": datetime.now(timezone.utc).isoformat()
            },
            confidence_level={
                "level": "HIGH",
                "historical_samples_count": 15,
                "similarity_score": 80.0,
                "explanation": "Test"
            }
        )
        
        # Retrieve it
        retrieved = await analysis_repository.get_by_id(created.id, winery_id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.fermentation_id == fermentation_id
        assert retrieved.winery_id == winery_id
    
    async def test_get_nonexistent_analysis_returns_none(self, analysis_repository, db_session):
        """Should return None for non-existent analysis."""
        winery_id = uuid4()
        
        result = await analysis_repository.get_by_id(uuid4(), winery_id)
        
        assert result is None
    
    async def test_get_analysis_wrong_winery_returns_none(self, analysis_repository, db_session):
        """Should return None when accessing analysis from different winery (multi-tenancy)."""
        fermentation_id = uuid4()
        winery_id_1 = uuid4()
        winery_id_2 = uuid4()
        
        # Create with winery 1
        created = await analysis_repository.create(
            fermentation_id=fermentation_id,
            winery_id=winery_id_1,
            comparison_result={
                "historical_samples_count": 10,
                "similarity_score": 70.0,
                "statistical_metrics": {},
                "comparison_criteria": {},
                "patterns_used": [],
                "compared_at": datetime.now(timezone.utc).isoformat()
            },
            confidence_level={
                "level": "MEDIUM",
                "historical_samples_count": 10,
                "similarity_score": 70.0,
                "explanation": "Test"
            }
        )
        
        # Try to access with winery 2
        result = await analysis_repository.get_by_id(created.id, winery_id_2)
        
        assert result is None


@pytest.mark.asyncio
class TestAnalysisRepositoryGetByFermentation:
    """Tests for retrieving analyses by fermentation_id."""
    
    async def test_get_by_fermentation_id(self, analysis_repository, db_session):
        """Should retrieve all analyses for a fermentation."""
        fermentation_id = uuid4()
        winery_id = uuid4()
        
        # Create 2 analyses for same fermentation
        data = {
            "comparison_result": {
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "statistical_metrics": {},
                "comparison_criteria": {},
                "patterns_used": [],
                "compared_at": datetime.now(timezone.utc).isoformat()
            },
            "confidence_level": {
                "level": "MEDIUM",
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "explanation": "Test"
            }
        }
        
        await analysis_repository.create(fermentation_id, winery_id, **data)
        await analysis_repository.create(fermentation_id, winery_id, **data)
        
        # Also create one for different fermentation
        await analysis_repository.create(uuid4(), winery_id, **data)
        
        # Retrieve by fermentation_id
        analyses = await analysis_repository.get_by_fermentation_id(fermentation_id, winery_id)
        
        assert len(analyses) == 2
        assert all(a.fermentation_id == fermentation_id for a in analyses)
        assert all(a.winery_id == winery_id for a in analyses)


@pytest.mark.asyncio
class TestAnalysisRepositoryUpdate:
    """Tests for updating analysis status."""
    
    async def test_update_status_to_completed(self, analysis_repository, db_session):
        """Should update analysis status."""
        fermentation_id = uuid4()
        winery_id = uuid4()
        
        # Create analysis
        analysis = await analysis_repository.create(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            comparison_result={
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "statistical_metrics": {},
                "comparison_criteria": {},
                "patterns_used": [],
                "compared_at": datetime.now(timezone.utc).isoformat()
            },
            confidence_level={
                "level": "MEDIUM",
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "explanation": "Test"
            }
        )
        
        assert analysis.status == AnalysisStatus.PENDING.value
        
        # Update status
        updated = await analysis_repository.update_status(
            analysis.id,
            winery_id,
            AnalysisStatus.COMPLETED
        )
        
        assert updated is not None
        assert updated.status == AnalysisStatus.COMPLETED.value
        
        # Verify persistence
        retrieved = await analysis_repository.get_by_id(analysis.id, winery_id)
        assert retrieved.status == AnalysisStatus.COMPLETED.value


@pytest.mark.asyncio
class TestAnalysisRepositoryGetByWinery:
    """Tests for retrieving analyses by winery."""
    
    async def test_get_by_winery(self, analysis_repository, db_session):
        """Should retrieve all analyses for a winery."""
        winery_id = uuid4()
        other_winery_id = uuid4()
        
        data = {
            "comparison_result": {
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "statistical_metrics": {},
                "comparison_criteria": {},
                "patterns_used": [],
                "compared_at": datetime.now(timezone.utc).isoformat()
            },
            "confidence_level": {
                "level": "MEDIUM",
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "explanation": "Test"
            }
        }
        
        # Create 3 analyses for winery_id
        await analysis_repository.create(uuid4(), winery_id, **data)
        await analysis_repository.create(uuid4(), winery_id, **data)
        await analysis_repository.create(uuid4(), winery_id, **data)
        
        # Create 1 for different winery
        await analysis_repository.create(uuid4(), other_winery_id, **data)
        
        # Retrieve by winery
        analyses = await analysis_repository.get_by_winery(winery_id)
        
        assert len(analyses) == 3
        assert all(a.winery_id == winery_id for a in analyses)


@pytest.mark.asyncio
class TestAnalysisRepositoryGetByStatus:
    """Tests for retrieving analyses by status."""
    
    async def test_get_by_status(self, analysis_repository, db_session):
        """Should retrieve analyses filtered by status."""
        winery_id = uuid4()
        
        data = {
            "comparison_result": {
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "statistical_metrics": {},
                "comparison_criteria": {},
                "patterns_used": [],
                "compared_at": datetime.now(timezone.utc).isoformat()
            },
            "confidence_level": {
                "level": "MEDIUM",
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "explanation": "Test"
            }
        }
        
        # Create analyses with different statuses
        analysis1 = await analysis_repository.create(uuid4(), winery_id, **data)
        analysis2 = await analysis_repository.create(uuid4(), winery_id, **data)
        analysis3 = await analysis_repository.create(uuid4(), winery_id, **data)
        
        # Update some to COMPLETED
        await analysis_repository.update_status(analysis1.id, winery_id, AnalysisStatus.COMPLETED)
        await analysis_repository.update_status(analysis2.id, winery_id, AnalysisStatus.COMPLETED)
        
        # Get PENDING analyses
        pending = await analysis_repository.get_by_status(winery_id, AnalysisStatus.PENDING)
        assert len(pending) == 1
        assert pending[0].id == analysis3.id
        
        # Get COMPLETED analyses
        completed = await analysis_repository.get_by_status(winery_id, AnalysisStatus.COMPLETED)
        assert len(completed) == 2
        assert all(a.status == AnalysisStatus.COMPLETED.value for a in completed)


@pytest.mark.asyncio
class TestAnalysisRepositoryGetRecent:
    """Tests for retrieving recent analyses with limit."""
    
    async def test_get_recent_with_limit(self, analysis_repository, db_session):
        """Should retrieve most recent analyses respecting limit."""
        winery_id = uuid4()
        
        data = {
            "comparison_result": {
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "statistical_metrics": {},
                "comparison_criteria": {},
                "patterns_used": [],
                "compared_at": datetime.now(timezone.utc).isoformat()
            },
            "confidence_level": {
                "level": "MEDIUM",
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "explanation": "Test"
            }
        }
        
        # Create 5 analyses
        for _ in range(5):
            await analysis_repository.create(uuid4(), winery_id, **data)
        
        # Get only 3 most recent
        recent = await analysis_repository.get_recent(winery_id, limit=3)
        
        assert len(recent) == 3
        # Should be ordered by analyzed_at DESC (most recent first)
        for i in range(len(recent) - 1):
            assert recent[i].analyzed_at >= recent[i + 1].analyzed_at


@pytest.mark.asyncio
class TestAnalysisRepositoryExists:
    """Tests for checking analysis existence."""
    
    async def test_exists_returns_true_for_existing(self, analysis_repository, db_session):
        """Should return True when analysis exists."""
        winery_id = uuid4()
        
        analysis = await analysis_repository.create(
            fermentation_id=uuid4(),
            winery_id=winery_id,
            comparison_result={
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "statistical_metrics": {},
                "comparison_criteria": {},
                "patterns_used": [],
                "compared_at": datetime.now(timezone.utc).isoformat()
            },
            confidence_level={
                "level": "MEDIUM",
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "explanation": "Test"
            }
        )
        
        exists = await analysis_repository.exists(analysis.id, winery_id)
        
        assert exists is True
    
    async def test_exists_returns_false_for_nonexistent(self, analysis_repository, db_session):
        """Should return False when analysis doesn't exist."""
        winery_id = uuid4()
        
        exists = await analysis_repository.exists(uuid4(), winery_id)
        
        assert exists is False
    
    async def test_exists_respects_winery_isolation(self, analysis_repository, db_session):
        """Should return False when analysis exists but for different winery."""
        winery_id_1 = uuid4()
        winery_id_2 = uuid4()
        
        analysis = await analysis_repository.create(
            fermentation_id=uuid4(),
            winery_id=winery_id_1,
            comparison_result={
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "statistical_metrics": {},
                "comparison_criteria": {},
                "patterns_used": [],
                "compared_at": datetime.now(timezone.utc).isoformat()
            },
            confidence_level={
                "level": "MEDIUM",
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "explanation": "Test"
            }
        )
        
        # Check with correct winery
        assert await analysis_repository.exists(analysis.id, winery_id_1) is True
        
        # Check with different winery
        assert await analysis_repository.exists(analysis.id, winery_id_2) is False


@pytest.mark.asyncio
class TestAnalysisRepositoryCountByStatus:
    """Tests for counting analyses by status."""
    
    async def test_count_by_status(self, analysis_repository, db_session):
        """Should count analyses grouped by status."""
        winery_id = uuid4()
        
        data = {
            "comparison_result": {
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "statistical_metrics": {},
                "comparison_criteria": {},
                "patterns_used": [],
                "compared_at": datetime.now(timezone.utc).isoformat()
            },
            "confidence_level": {
                "level": "MEDIUM",
                "historical_samples_count": 10,
                "similarity_score": 75.0,
                "explanation": "Test"
            }
        }
        
        # Create analyses with different statuses
        # 3 PENDING
        a1 = await analysis_repository.create(uuid4(), winery_id, **data)
        a2 = await analysis_repository.create(uuid4(), winery_id, **data)
        a3 = await analysis_repository.create(uuid4(), winery_id, **data)
        
        # 2 COMPLETED
        a4 = await analysis_repository.create(uuid4(), winery_id, **data)
        a5 = await analysis_repository.create(uuid4(), winery_id, **data)
        await analysis_repository.update_status(a4.id, winery_id, AnalysisStatus.COMPLETED)
        await analysis_repository.update_status(a5.id, winery_id, AnalysisStatus.COMPLETED)
        
        # 1 FAILED
        a6 = await analysis_repository.create(uuid4(), winery_id, **data)
        await analysis_repository.update_status(a6.id, winery_id, AnalysisStatus.FAILED)
        
        # Count by status
        counts = await analysis_repository.count_by_status(winery_id)
        
        assert counts[AnalysisStatus.PENDING] == 3
        assert counts[AnalysisStatus.COMPLETED] == 2
        assert counts[AnalysisStatus.FAILED] == 1
        assert counts.get(AnalysisStatus.IN_PROGRESS, 0) == 0
