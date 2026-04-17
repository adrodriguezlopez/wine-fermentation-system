"""
Tests for ProtocolAdvisoryRepository.

Uses the same mock-session pattern as test_analysis_repository.py.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from contextlib import asynccontextmanager

from src.modules.analysis_engine.src.repository_component.repositories.protocol_advisory_repository import (
    ProtocolAdvisoryRepository,
)
from src.modules.analysis_engine.src.domain.entities.protocol_advisory import ProtocolAdvisory
from src.modules.analysis_engine.src.domain.enums.advisory_type import AdvisoryType
from src.modules.analysis_engine.src.domain.enums.risk_level import RiskLevel


@asynccontextmanager
async def mock_session_cm(session):
    yield session


def make_repo(mock_session):
    repo = ProtocolAdvisoryRepository.__new__(ProtocolAdvisoryRepository)

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
    result.scalar_one.return_value = 0
    session.execute.return_value = result
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def repo(mock_session):
    return make_repo(mock_session)


def make_advisory(fermentation_id=None, analysis_id=None, risk_level=RiskLevel.MEDIUM):
    return ProtocolAdvisory(
        fermentation_id=fermentation_id or uuid4(),
        analysis_id=analysis_id or uuid4(),
        advisory_type=AdvisoryType.ACCELERATE_STEP,
        target_step_type="MONITORING",
        risk_level=risk_level,
        suggestion="Test suggestion",
        confidence=0.8,
    )


class TestProtocolAdvisoryRepositoryAdd:
    @pytest.mark.asyncio
    async def test_add_calls_session_add_and_flush(self, repo, mock_session):
        advisory = make_advisory()
        result = await repo.add(advisory)
        mock_session.add.assert_called_once_with(advisory)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_returns_advisory(self, repo, mock_session):
        advisory = make_advisory()
        result = await repo.add(advisory)
        assert result is advisory


class TestProtocolAdvisoryRepositoryAddMany:
    @pytest.mark.asyncio
    async def test_add_many_empty_list_returns_empty(self, repo):
        result = await repo.add_many([])
        assert result == []

    @pytest.mark.asyncio
    async def test_add_many_calls_add_for_each(self, repo, mock_session):
        advisories = [make_advisory(), make_advisory()]
        await repo.add_many(advisories)
        assert mock_session.add.call_count == 2
        mock_session.flush.assert_called_once()


class TestProtocolAdvisoryRepositoryGetById:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self, repo, mock_session):
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        result = await repo.get_by_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_executes_query(self, repo, mock_session):
        await repo.get_by_id(uuid4())
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_advisory_when_found(self, repo, mock_session):
        advisory = make_advisory()
        mock_session.execute.return_value.scalar_one_or_none.return_value = advisory
        result = await repo.get_by_id(uuid4())
        assert result is advisory


class TestProtocolAdvisoryRepositoryGetByFermentationId:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_none(self, repo, mock_session):
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        result = await repo.get_by_fermentation_id(uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_executes_query(self, repo, mock_session):
        await repo.get_by_fermentation_id(uuid4())
        mock_session.execute.assert_called_once()


class TestProtocolAdvisoryRepositoryAcknowledge:
    @pytest.mark.asyncio
    async def test_acknowledge_returns_none_when_not_found(self, repo, mock_session):
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        result = await repo.acknowledge(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_acknowledge_calls_advisory_acknowledge(self, repo, mock_session):
        advisory = make_advisory()
        assert advisory.is_acknowledged is False
        mock_session.execute.return_value.scalar_one_or_none.return_value = advisory
        result = await repo.acknowledge(advisory.id)
        assert result.is_acknowledged is True


class TestProtocolAdvisoryRepositoryCountUnacknowledged:
    @pytest.mark.asyncio
    async def test_count_returns_integer(self, repo, mock_session):
        mock_session.execute.return_value.scalar_one.return_value = 3
        result = await repo.count_unacknowledged(uuid4())
        assert result == 3

    @pytest.mark.asyncio
    async def test_count_zero_when_none(self, repo, mock_session):
        mock_session.execute.return_value.scalar_one.return_value = 0
        result = await repo.count_unacknowledged(uuid4())
        assert result == 0


class TestProtocolAdvisoryTableName:
    def test_protocol_advisory_tablename(self):
        assert ProtocolAdvisory.__tablename__ == "protocol_advisory"
