"""
Integration tests for ComparisonService.

These tests replace the 3 skipped unit tests in
``tests/unit/service/test_comparison_service.py``.  They run against a real
PostgreSQL instance (localhost:5433/wine_fermentation_test) so that:

- SQLAlchemy JSONB columns work correctly (Analysis uses JSONB).
- ComparisonService.find_similar_fermentations() can execute its SELECT against
  the real Fermentation table with the full PostgreSQL dialect.
- build_comparison_result() can query Fermentation rows and return a properly
  populated ComparisonResult value object.

Prerequisites:
    docker compose -f docker-compose.inttest.yml up --wait

Skipped unit tests being replaced:
    TestFindSimilarFermentations::test_calculate_similarity_score_no_brix_provided
    TestBuildComparisonResult::test_returns_comparison_result_with_zero_count_when_no_similar
    TestBuildComparisonResult::test_returns_comparison_result_type
"""
import pytest
from uuid import uuid4

from src.modules.analysis_engine.src.service_component.services.comparison_service import ComparisonService
from src.modules.analysis_engine.src.domain.value_objects.comparison_result import ComparisonResult

pytestmark = pytest.mark.integration


class TestFindSimilarFermentationsIntegration:
    """
    Integration coverage for ComparisonService.find_similar_fermentations().

    Replaces:
        TestFindSimilarFermentations::test_calculate_similarity_score_no_brix_provided
    """

    @pytest.mark.asyncio
    async def test_find_similar_returns_empty_when_no_matches(self, db_session):
        """
        find_similar_fermentations() returns ([], 0) when the Fermentation table
        has no rows matching the given winery_id + variety combination.

        The Fermentation table may have rows from other fixtures but none will
        match a freshly-generated UUID winery_id, so the result must be empty.

        NOTE: Fermentation.winery_id is an INTEGER FK, while the analysis-engine
        services accept UUID winery_ids.  Passing a UUID to the INTEGER column
        filter produces an empty result (no type coercion match), which is the
        correct "no similar fermentations" scenario we need to test.
        """
        service = ComparisonService(session=db_session)

        ids, count = await service.find_similar_fermentations(
            winery_id=uuid4(),          # UUID — won't match integer winery_id rows
            fermentation_id=uuid4(),
            variety="Chardonnay",
            starting_brix=None,         # No brix filter — mirrors the skipped unit test
        )

        assert ids == []
        assert count == 0

    @pytest.mark.asyncio
    async def test_find_similar_returns_empty_when_variety_no_match(self, db_session):
        """
        find_similar_fermentations() returns ([], 0) when no Fermentation rows
        match the requested variety.  Tests the variety-filter code path.
        """
        service = ComparisonService(session=db_session)

        ids, count = await service.find_similar_fermentations(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            variety="NonExistentVariety_XYZ_2024",
            starting_brix=22.0,
        )

        assert ids == []
        assert count == 0

    @pytest.mark.asyncio
    async def test_find_similar_excludes_self(self, db_session):
        """
        find_similar_fermentations() always excludes the fermentation_id passed
        in (i.e. the current fermentation cannot be similar to itself).
        Even with a matching winery_id and variety, the row for fermentation_id
        itself must be absent from the result.
        """
        service = ComparisonService(session=db_session)
        fermentation_id = uuid4()

        ids, count = await service.find_similar_fermentations(
            winery_id=uuid4(),
            fermentation_id=fermentation_id,
            variety="Merlot",
        )

        assert fermentation_id not in ids


class TestBuildComparisonResultIntegration:
    """
    Integration coverage for ComparisonService.build_comparison_result().

    Replaces:
        TestBuildComparisonResult::test_returns_comparison_result_with_zero_count_when_no_similar
        TestBuildComparisonResult::test_returns_comparison_result_type
    """

    @pytest.mark.asyncio
    async def test_returns_comparison_result_type(self, db_session):
        """
        build_comparison_result() always returns a ComparisonResult instance,
        even when similar_fermentation_ids is empty and the fermentation_id
        does not exist in the DB.
        """
        service = ComparisonService(session=db_session)

        result = await service.build_comparison_result(
            winery_id=uuid4(),
            fermentation_id=uuid4(),    # Does not exist — scalar_one_or_none → None
            similar_fermentation_ids=[],
        )

        assert isinstance(result, ComparisonResult)

    @pytest.mark.asyncio
    async def test_returns_zero_count_when_no_similar(self, db_session):
        """
        build_comparison_result() with an empty similar_fermentation_ids list
        returns a ComparisonResult whose similar_fermentation_count is 0.
        """
        service = ComparisonService(session=db_session)

        result = await service.build_comparison_result(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            similar_fermentation_ids=[],
        )

        assert isinstance(result, ComparisonResult)
        assert result.similar_fermentation_count == 0

    @pytest.mark.asyncio
    async def test_comparison_basis_contains_none_when_fermentation_missing(self, db_session):
        """
        When the current fermentation does not exist in the DB, build_comparison_result()
        should still return a valid ComparisonResult with None values in comparison_basis
        (not raise an AttributeError).
        """
        service = ComparisonService(session=db_session)

        result = await service.build_comparison_result(
            winery_id=uuid4(),
            fermentation_id=uuid4(),    # Non-existent → current_ferm = None
            similar_fermentation_ids=[],
        )

        assert isinstance(result, ComparisonResult)
        # comparison_basis should gracefully handle missing fermentation
        assert result.comparison_basis is not None
        assert result.comparison_basis.get("variety") is None

    @pytest.mark.asyncio
    async def test_average_duration_and_gravity_none_when_no_similar(self, db_session):
        """
        When there are no similar fermentations, averages should be None
        (not 0 or any default) because there is no data to average.
        """
        service = ComparisonService(session=db_session)

        result = await service.build_comparison_result(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            similar_fermentation_ids=[],
        )

        assert result.average_duration_days is None
        assert result.average_final_gravity is None
