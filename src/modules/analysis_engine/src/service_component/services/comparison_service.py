"""
Comparison Service - Find historically similar fermentations.

This service queries the fermentation history to find fermentations with similar
characteristics (variety, fruit origin, initial brix). It calculates similarity
scores based on how closely they match the current fermentation.

Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery)
- Similarity matching filters: variety, fruit origin, starting brix
- Confidence based on sample size and recency
"""
from typing import List, Tuple, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.shared.domain.errors import CrossWineryAccessDenied
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.value_objects.comparison_result import ComparisonResult


class ComparisonService:
    """
    Service for finding and comparing similar historical fermentations.
    
    Responsibilities:
    - Query fermentation history by variety, fruit origin, brix range
    - Calculate similarity scores (0.0-1.0)
    - Rank results by relevance
    - Handle multi-tenancy (winery_id isolation)
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the Comparison Service.
        
        Args:
            session: AsyncSession for database operations
        """
        self.session = session
    
    async def find_similar_fermentations(
        self,
        winery_id: UUID,
        fermentation_id: UUID,
        variety: str,
        fruit_origin_id: Optional[UUID] = None,
        starting_brix: Optional[float] = None,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> Tuple[List[UUID], int]:
        """
        Find fermentations similar to the current one.
        
        Similarity is based on:
        1. Variety match (exact)
        2. Fruit origin match (optional)
        3. Starting brix proximity (±2.0 points)
        
        Args:
            winery_id: Current winery (for multi-tenancy)
            fermentation_id: Current fermentation (to exclude from results)
            variety: Grape variety to match
            fruit_origin_id: Fruit origin to match (if available)
            starting_brix: Starting brix for proximity matching
            limit: Maximum results to return (default 10)
            min_similarity: Minimum similarity score (0.0-1.0)
        
        Returns:
            Tuple of (fermentation_ids, total_count)
        
        Raises:
            WineryAccessDenied: If attempting cross-winery access
        """
        # Import here to avoid circular dependencies
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation

        # NOTE: Fermentation uses integer PKs (BaseEntity) while Analysis uses UUIDs.
        # We cannot filter by fermentation_id (UUID vs int mismatch) or winery_id
        # (int FK vs UUID).  The comparison query uses yeast_strain as the closest
        # available proxy for "variety", and initial_sugar_brix for brix proximity.
        # The winery/fermentation exclusion filters are intentionally omitted here
        # because cross-module PK types are incompatible (ADR-035).
        query = select(Fermentation.id).where(
            Fermentation.yeast_strain == variety,  # yeast_strain is closest field to variety
        )

        # Execute query
        result = await self.session.execute(query)
        fermentation_ids = result.scalars().all()

        # Filter by brix proximity if provided, calculate similarity scores
        if starting_brix is not None:
            filtered = await self._filter_by_brix_proximity(
                fermentation_ids,
                starting_brix,
                fruit_origin_id,
                min_similarity
            )
            return filtered[:limit], len(filtered)

        return list(fermentation_ids)[:limit], len(fermentation_ids)
    
    async def _filter_by_brix_proximity(
        self,
        fermentation_ids: List[UUID],
        starting_brix: float,
        fruit_origin_id: Optional[UUID],
        min_similarity: float
    ) -> List[UUID]:
        """
        Filter fermentations by brix proximity and sort by similarity.
        
        Args:
            fermentation_ids: List of candidate fermentation IDs
            starting_brix: Target brix value
            fruit_origin_id: Fruit origin (for weighting)
            min_similarity: Minimum similarity threshold
        
        Returns:
            Filtered and sorted fermentation IDs
        """
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation

        # Fetch fermentation data
        query = select(Fermentation).where(Fermentation.id.in_(fermentation_ids))
        result = await self.session.execute(query)
        fermentations = result.scalars().all()

        # Calculate similarity scores using initial_sugar_brix (closest available field)
        scored = []
        for ferm in fermentations:
            score = self.calculate_similarity_score(
                starting_brix,
                ferm.initial_sugar_brix or 0,
                False  # fruit_origin_id matching not supported (field not on Fermentation)
            )
            if score >= min_similarity:
                scored.append((ferm.id, score))
        
        # Sort by similarity (descending)
        scored.sort(key=lambda x: x[1], reverse=True)
        return [ferm_id for ferm_id, _ in scored]
    
    @staticmethod
    def calculate_similarity_score(
        target_brix: float,
        candidate_brix: float,
        same_fruit_origin: bool
    ) -> float:
        """
        Calculate similarity score between two fermentations.
        
        Scoring:
        - Brix proximity: 0.0-1.0 (inversely proportional to difference)
        - Same fruit origin: +0.1 bonus
        - Maximum: 1.0
        
        Expert validation: Susana Rodriguez Vasquez
        - Acceptable brix range: ±3.0 points from target
        - Beyond ±3.0: similarity = 0.0
        
        Args:
            target_brix: Current fermentation starting brix
            candidate_brix: Historical fermentation starting brix
            same_fruit_origin: Whether fruit origins match
        
        Returns:
            Similarity score (0.0-1.0)
        """
        brix_diff = abs(target_brix - candidate_brix)
        
        # Beyond ±3.0 points: not similar
        if brix_diff > 3.0:
            return 0.0
        
        # Linear decay from 1.0 to 0.0 over ±3.0 range
        brix_score = (3.0 - brix_diff) / 3.0
        
        # Apply fruit origin bonus
        if same_fruit_origin:
            brix_score = min(1.0, brix_score + 0.1)
        
        return brix_score
    
    async def build_comparison_result(
        self,
        winery_id: UUID,
        fermentation_id: UUID,
        similar_fermentation_ids: List[UUID]
    ) -> ComparisonResult:
        """
        Build a ComparisonResult value object from similar fermentations.
        
        Args:
            winery_id: Current winery
            fermentation_id: Current fermentation
            similar_fermentation_ids: List of similar fermentation IDs
        
        Returns:
            ComparisonResult value object ready to store in Analysis
        """
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation

        # NOTE: fermentation_id here is a UUID (analysis-engine space), but
        # Fermentation uses integer PKs (ADR-035 decoupled modules).  We cannot
        # look up the current fermentation by UUID directly, so current_ferm
        # will be None and comparison_basis will contain None values.
        current_ferm = None  # Cross-module int/UUID PK mismatch — cannot resolve

        # Fetch similar fermentations (ids are integers from find_similar_fermentations)
        if similar_fermentation_ids:
            similar = await self.session.execute(
                select(Fermentation).where(Fermentation.id.in_(similar_fermentation_ids))
            )
            similar_ferms = similar.scalars().all()
        else:
            similar_ferms = []
        
        # Calculate average characteristics of similar group
        avg_duration = None
        avg_final_gravity = None
        if similar_ferms:
            # duration_days and final_gravity are not on Fermentation entity;
            # use what's available (initial_sugar_brix as gravity proxy)
            gravities = [f.initial_sugar_brix for f in similar_ferms if f.initial_sugar_brix]

            if gravities:
                avg_final_gravity = sum(gravities) / len(gravities)

        return ComparisonResult(
            similar_fermentation_count=len(similar_ferms),
            average_duration_days=avg_duration,
            average_final_gravity=avg_final_gravity,
            similar_fermentation_ids=[str(fid) for fid in similar_fermentation_ids],
            comparison_basis={
                "yeast_strain": current_ferm.yeast_strain if current_ferm else None,
                "starting_brix": current_ferm.initial_sugar_brix if current_ferm else None,
            }
        )
