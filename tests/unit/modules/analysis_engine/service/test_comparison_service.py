"""Tests for Comparison Service."""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root and src to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
src_path = project_root / "src"
for p in [str(project_root), str(src_path)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from src.modules.analysis_engine.src.service_component.services.comparison_service import ComparisonService
from src.modules.analysis_engine.src.domain.value_objects.comparison_result import ComparisonResult


@pytest.fixture
def comparison_service(session: AsyncSession):
    """Create a Comparison Service instance."""
    return ComparisonService(session)


class TestSimilarityScoreCalculation:
    """Tests for similarity score calculation."""
    
    def test_exact_brix_match(self):
        """Similar fermentations should have higher scores."""
        score = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=24.0,
            same_fruit_origin=False
        )
        assert score == 1.0
    
    def test_one_point_difference(self):
        """1 point difference from target."""
        score = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=23.0,
            same_fruit_origin=False
        )
        # (3.0 - 1.0) / 3.0 = 0.667
        assert 0.66 < score < 0.67
    
    def test_three_point_difference(self):
        """3 point difference (at boundary)."""
        score = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=21.0,
            same_fruit_origin=False
        )
        # (3.0 - 3.0) / 3.0 = 0.0
        assert score == 0.0
    
    def test_beyond_threshold(self):
        """Beyond ±3.0 points should be 0."""
        score = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=20.5,
            same_fruit_origin=False
        )
        assert score == 0.0
    
    def test_fruit_origin_bonus(self):
        """Same fruit origin adds 0.1 bonus."""
        score_no_bonus = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=24.0,
            same_fruit_origin=False
        )
        score_with_bonus = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=24.0,
            same_fruit_origin=True
        )
        
        assert score_no_bonus == 1.0  # Capped at 1.0
        assert score_with_bonus == 1.0  # Capped at 1.0
    
    def test_fruit_origin_bonus_non_capped(self):
        """Bonus should be visible when not at 1.0."""
        score_no_bonus = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=23.5,
            same_fruit_origin=False
        )
        score_with_bonus = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=23.5,
            same_fruit_origin=True
        )
        
        assert score_with_bonus > score_no_bonus
        assert abs((score_with_bonus - score_no_bonus) - 0.1) < 0.01


class TestComparisonResultBuilding:
    """Tests for building ComparisonResult value objects."""
    
    @pytest.mark.asyncio
    async def test_empty_similar_list(self, comparison_service: ComparisonService):
        """Building result with no similar fermentations."""
        result = await comparison_service.build_comparison_result(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            similar_fermentation_ids=[]
        )
        
        assert isinstance(result, ComparisonResult)
        assert result.similar_fermentation_count == 0
        assert result.average_duration_days is None
        assert result.average_final_gravity is None
    
    def test_comparison_result_serialization(self):
        """ComparisonResult should serialize to dict."""
        result = ComparisonResult(
            similar_fermentation_count=3,
            average_duration_days=14.5,
            average_final_gravity=0.99,
            similar_fermentation_ids=["id1", "id2", "id3"],
            comparison_basis={
                "variety": "Cabernet Sauvignon",
                "fruit_origin_id": str(uuid4()),
                "starting_brix": 24.0,
            }
        )
        
        result_dict = result.to_dict()
        assert result_dict["similar_fermentation_count"] == 3
        assert result_dict["average_duration_days"] == 14.5
        assert len(result_dict["similar_fermentation_ids"]) == 3


class TestMinSimilarityFiltering:
    """Tests for minimum similarity threshold filtering."""
    
    def test_min_similarity_0_5(self):
        """Items below 0.5 similarity should be filtered."""
        # 0.4 should be filtered at min_similarity=0.5
        score = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=22.0,
            same_fruit_origin=False
        )
        # (3.0 - 2.0) / 3.0 = 0.333
        assert score < 0.5
    
    def test_min_similarity_0_3(self):
        """Items above minimum should pass."""
        score = ComparisonService.calculate_similarity_score(
            target_brix=24.0,
            candidate_brix=22.0,
            same_fruit_origin=False
        )
        # 0.333 > 0.3
        assert score > 0.3
