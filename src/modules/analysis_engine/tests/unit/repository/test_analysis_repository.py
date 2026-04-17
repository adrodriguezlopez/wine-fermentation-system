"""
Tests for AnalysisRepository.

The AnalysisRepository extends BaseRepository which manages session lifecycles
internally. We test behavior by patching execute_with_error_mapping to directly
invoke the inner operation with a mock session, verifying the repository
constructs and executes the right queries.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from contextlib import asynccontextmanager

from src.modules.analysis_engine.src.repository_component.repositories.analysis_repository import (
    AnalysisRepository,
)
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus


@asynccontextmanager
async def mock_session_cm(session):
    yield session


def make_repo_with_mock_session(mock_session):
    """Create AnalysisRepository whose get_session yields a mock session."""
    repo = AnalysisRepository.__new__(AnalysisRepository)

    async def _execute_with_error_mapping(operation):
        return await operation()

    async def _get_session():
        return mock_session_cm(mock_session)

    repo.execute_with_error_mapping = _execute_with_error_mapping
    repo.get_session = _get_session
    return repo


@pytest.fixture
def mock_session():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    result.scalars.return_value.all.return_value = []
    session.execute.return_value = result
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def repo(mock_session):
    return make_repo_with_mock_session(mock_session)


class TestAnalysisRepositoryCreate:
    @pytest.mark.asyncio
    async def test_create_adds_analysis_to_session(self, repo, mock_session, winery_id, fermentation_id):
        result = await repo.create(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            comparison_result={"similar_fermentation_count": 5},
            confidence_level={"overall_confidence": 0.7},
        )
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_returns_analysis_instance(self, repo, mock_session, winery_id, fermentation_id):
        result = await repo.create(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            comparison_result={},
            confidence_level={},
        )
        assert isinstance(result, Analysis)

    @pytest.mark.asyncio
    async def test_create_sets_pending_status(self, repo, mock_session, winery_id, fermentation_id):
        result = await repo.create(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            comparison_result={},
            confidence_level={},
        )
        assert result.status == AnalysisStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_create_sets_correct_winery_id(self, repo, mock_session, winery_id, fermentation_id):
        result = await repo.create(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            comparison_result={},
            confidence_level={},
        )
        assert result.winery_id == winery_id


class TestAnalysisRepositoryGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self, repo, mock_session, winery_id):
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        result = await repo.get_by_id(uuid4(), winery_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_executes_query(self, repo, mock_session, winery_id):
        await repo.get_by_id(uuid4(), winery_id)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_analysis_when_found(self, repo, mock_session, winery_id):
        analysis = MagicMock(spec=Analysis)
        analysis.status = AnalysisStatus.COMPLETED.value
        mock_session.execute.return_value.scalar_one_or_none.return_value = analysis
        result = await repo.get_by_id(uuid4(), winery_id)
        assert result is analysis


class TestAnalysisRepositoryGetByFermentationId:
    @pytest.mark.asyncio
    async def test_get_by_fermentation_id_returns_empty_list(self, repo, mock_session, winery_id, fermentation_id):
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.get_by_fermentation_id(fermentation_id, winery_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_fermentation_id_executes_query(self, repo, mock_session, winery_id, fermentation_id):
        await repo.get_by_fermentation_id(fermentation_id, winery_id)
        mock_session.execute.assert_called_once()


class TestAnalysisRepositoryTableName:
    def test_analysis_tablename(self):
        assert Analysis.__tablename__ == "analysis"
