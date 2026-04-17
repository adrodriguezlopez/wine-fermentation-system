"""
Tests for ComparisonService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.modules.analysis_engine.src.service_component.services.comparison_service import ComparisonService
from src.modules.analysis_engine.src.domain.value_objects.comparison_result import ComparisonResult


@pytest.fixture
def service(mock_async_session):
    return ComparisonService(session=mock_async_session)


class TestCalculateSimilarityScore:
    def test_identical_brix_same_origin_returns_high_score(self):
        score = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=24.0,
            same_fruit_origin=True,
        )
        assert score > 0.9

    def test_brix_diff_greater_than_3_returns_zero(self):
        score = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=28.0,
            same_fruit_origin=False,
        )
        assert score == 0.0

    def test_fruit_origin_bonus_applied(self):
        # When brix_score < 0.9, same_fruit_origin bonus should push score higher
        score_same = ComparisonService.calculate_similarity_score(24.0, 26.0, True)
        score_diff = ComparisonService.calculate_similarity_score(24.0, 26.0, False)
        assert score_same > score_diff

    def test_linear_decay_within_range(self):
        score_close = ComparisonService.calculate_similarity_score(24.0, 24.5, False)
        score_far = ComparisonService.calculate_similarity_score(24.0, 26.5, False)
        assert score_close > score_far

    def test_max_score_capped_at_1(self):
        score = ComparisonService.calculate_similarity_score(24.0, 24.0, True)
        assert score <= 1.0


class TestFindSimilarFermentations:
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="find_similar_fermentations imports cross-module Fermentation ORM model not available in isolated env")
    async def test_calculate_similarity_score_no_brix_provided(self, service, mock_async_session):
        mock_async_session.execute.return_value.scalars.return_value.all.return_value = []
        ids, count = await service.find_similar_fermentations(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            variety="Chardonnay",
            starting_brix=None,
        )
        assert ids == []
        assert count == 0


class TestBuildComparisonResult:
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="build_comparison_result imports cross-module Fermentation ORM model not available in isolated env")
    async def test_returns_comparison_result_with_zero_count_when_no_similar(self, service, mock_async_session):
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value.scalars.return_value.all.return_value = []
        result = await service.build_comparison_result(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            similar_fermentation_ids=[],
        )
        assert isinstance(result, ComparisonResult)
        assert result.similar_fermentation_count == 0

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="build_comparison_result imports cross-module Fermentation ORM model not available in isolated env")
    async def test_returns_comparison_result_type(self, service, mock_async_session):
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_async_session.execute.return_value.scalars.return_value.all.return_value = []
        result = await service.build_comparison_result(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            similar_fermentation_ids=[],
        )
        assert isinstance(result, ComparisonResult)
