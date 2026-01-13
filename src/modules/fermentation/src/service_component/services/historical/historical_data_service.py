"""
HistoricalDataService - Service for querying historical fermentation data.

Implements business logic for Historical Data API Layer (ADR-032).
Provides read-only access to imported historical fermentations with pattern extraction.

Implementation Status: 🔨 IN PROGRESS (January 13, 2026)
Following TDD approach - implementing to satisfy 12 unit tests.

Related ADRs:
- ADR-032: Historical Data API Layer
- ADR-019: ETL Pipeline Design
- ADR-029: Data Source Field for Historical Tracking
- ADR-025: Multi-Tenancy Architecture
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime
from statistics import mean

# ADR-027: Structured logging
from src.shared.wine_fermentator_logging import get_logger

from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.service_component.errors import NotFoundError

logger = get_logger(__name__)


class HistoricalDataService:
    """
    Service for querying and aggregating historical fermentation data.
    
    Responsibilities (per ADR-032):
    - Query historical fermentations with multi-tenant filtering
    - Retrieve historical samples for analysis
    - Extract aggregated patterns for Analysis Engine
    - Enforce data_source='HISTORICAL' filtering
    - Respect winery_id boundaries (multi-tenancy)
    
    Design:
    - Read-only operations (no create/update/delete)
    - Depends on abstractions (IFermentationRepository, ISampleRepository)
    - Returns domain entities (Fermentation, BaseSample)
    - All queries filtered by data_source='HISTORICAL'
    - Multi-tenant security enforced on all operations
    """
    
    def __init__(
        self,
        fermentation_repo: IFermentationRepository,
        sample_repo: ISampleRepository
    ):
        """
        Initialize service with repository dependencies.
        
        Args:
            fermentation_repo: Repository for fermentation data access
            sample_repo: Repository for sample data access
        """
        self._fermentation_repo = fermentation_repo
        self._sample_repo = sample_repo
    
    async def get_historical_fermentations(
        self,
        winery_id: int,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0
    ) -> List[Fermentation]:
        """
        Get list of historical fermentations with optional filters.
        
        Filters by data_source='HISTORICAL' automatically (ADR-029).
        Respects multi-tenant boundaries (winery_id scoping).
        
        Args:
            winery_id: Winery ID for multi-tenant filtering (REQUIRED)
            filters: Optional filters (start_date_from, start_date_to, fruit_origin_id, status)
            limit: Maximum number of results (default 100)
            offset: Number of results to skip for pagination (default 0)
            
        Returns:
            List[Fermentation]: List of historical fermentation entities
            
        Raises:
            RepositoryError: If database query fails
            
        Note:
            Current repository interface only supports data_source filtering.
            Additional filters (date_range, fruit_origin, status) will be applied in-memory.
            TODO: Update IFermentationRepository to support advanced filtering.
        """
        logger.info(
            "get_historical_fermentations",
            winery_id=winery_id,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        # Use list_by_data_source which is the correct method
        fermentations = await self._fermentation_repo.list_by_data_source(
            winery_id=winery_id,
            data_source="HISTORICAL",
            include_deleted=False
        )
        
        # Apply additional filters in-memory (TODO: push to repository layer)
        if "start_date_from" in filters:
            start_date_from = filters["start_date_from"]
            # Always compare dates (not datetimes)
            fermentations = [
                f for f in fermentations 
                if f.start_date and (f.start_date.date() if isinstance(f.start_date, datetime) else f.start_date) >= start_date_from
            ]
        
        if "start_date_to" in filters:
            start_date_to = filters["start_date_to"]
            # Always compare dates (not datetimes)
            fermentations = [
                f for f in fermentations 
                if f.start_date and (f.start_date.date() if isinstance(f.start_date, datetime) else f.start_date) <= start_date_to
            ]
        if "fruit_origin_id" in filters:
            fermentations = [f for f in fermentations if f.fruit_origin_id == filters["fruit_origin_id"]]
        if "status" in filters:
            fermentations = [f for f in fermentations if f.status == filters["status"]]
        
        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        fermentations = fermentations[start_idx:end_idx]
        
        logger.info(
            "get_historical_fermentations_result",
            winery_id=winery_id,
            count=len(fermentations)
        )
        
        return fermentations
    
    async def get_historical_fermentation_by_id(
        self,
        fermentation_id: int,
        winery_id: int
    ) -> Fermentation:
        """
        Get single historical fermentation by ID.
        
        Enforces multi-tenant security: fermentation must belong to specified winery.
        
        Args:
            fermentation_id: ID of the fermentation to retrieve
            winery_id: Winery ID for multi-tenant security (REQUIRED)
            
        Returns:
            Fermentation: Historical fermentation entity
            
        Raises:
            NotFoundError: If fermentation not found or belongs to different winery
        """
        logger.info(
            "get_historical_fermentation_by_id",
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        # Repository get_by_id requires winery_id for multi-tenant security
        fermentation = await self._fermentation_repo.get_by_id(fermentation_id, winery_id)
        
        if not fermentation:
            logger.warning(
                "fermentation_not_found",
                fermentation_id=fermentation_id
            )
            raise NotFoundError(f"Fermentation with ID {fermentation_id} not found")
        
        return fermentation
    
    async def get_fermentation_samples(
        self,
        fermentation_id: int,
        winery_id: int
    ) -> List[BaseSample]:
        """
        Get all samples for a historical fermentation.
        
        Verifies fermentation exists and belongs to winery before retrieving samples.
        Filters samples by data_source='HISTORICAL' automatically.
        
        Args:
            fermentation_id: ID of the fermentation
            winery_id: Winery ID for multi-tenant security (REQUIRED)
            
        Returns:
            List[BaseSample]: List of sample entities (all types)
            
        Raises:
            NotFoundError: If fermentation not found or belongs to different winery
        """
        logger.info(
            "get_fermentation_samples",
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        # Verify fermentation exists and belongs to winery
        fermentation = await self.get_historical_fermentation_by_id(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        # Get samples filtered by data_source
        samples = await self._sample_repo.get_samples_by_fermentation_id(
            fermentation_id=fermentation_id
        )
        
        # Filter by data_source (in case repository doesn't support it)
        # TODO: Update repository interface to support data_source parameter
        historical_samples = [s for s in samples if getattr(s, 'data_source', 'HISTORICAL') == 'HISTORICAL']
        
        logger.info(
            "get_fermentation_samples_result",
            fermentation_id=fermentation_id,
            count=len(historical_samples)
        )
        
        return historical_samples
    
    async def extract_patterns(
        self,
        winery_id: int,
        fruit_origin_id: Optional[int] = None,
        date_range: Optional[Tuple[date, date]] = None
    ) -> Dict[str, Any]:
        """
        Extract aggregated patterns from historical fermentations for Analysis Engine.
        
        Computes statistical aggregations across multiple fermentations:
        - Average initial/final density and sugar levels
        - Average fermentation duration
        - Success rate (completed vs stuck/failed)
        - Common patterns and issues
        
        Args:
            winery_id: Winery ID for multi-tenant filtering (REQUIRED)
            fruit_origin_id: Optional filter by fruit origin
            date_range: Optional date range tuple (start_date, end_date)
            
        Returns:
            Dict[str, Any]: Aggregated pattern data with metrics:
                - total_fermentations: int
                - avg_initial_density: float | None
                - avg_final_density: float | None
                - avg_initial_sugar_brix: float | None
                - avg_final_sugar_brix: float | None
                - avg_duration_days: float | None
                - success_rate: float (0.0-1.0)
                - completed_count: int
                - stuck_count: int
        """
        logger.info(
            "extract_patterns",
            winery_id=winery_id,
            fruit_origin_id=fruit_origin_id,
            date_range=date_range
        )
        
        # Build filters
        filters = {}
        if fruit_origin_id:
            filters["fruit_origin_id"] = fruit_origin_id
        if date_range:
            filters["start_date_from"] = date_range[0]
            filters["start_date_to"] = date_range[1]
        
        # Get all historical fermentations matching filters
        fermentations = await self.get_historical_fermentations(
            winery_id=winery_id,
            filters=filters,
            limit=10000,  # Get all for aggregation
            offset=0
        )
        
        # Initialize pattern result
        pattern = {
            "total_fermentations": len(fermentations),
            "avg_initial_density": None,
            "avg_final_density": None,
            "avg_initial_sugar_brix": None,
            "avg_final_sugar_brix": None,
            "avg_duration_days": None,
            "success_rate": 0.0,
            "completed_count": 0,
            "stuck_count": 0
        }
        
        if not fermentations:
            logger.info("extract_patterns_no_data", winery_id=winery_id)
            return pattern
        
        # Collect metrics from fermentations
        initial_densities = []
        final_densities = []
        initial_sugars = []
        final_sugars = []
        durations = []
        completed_count = 0
        stuck_count = 0
        
        for ferm in fermentations:
            # Initial values
            if ferm.initial_density is not None:
                initial_densities.append(ferm.initial_density)
            if ferm.initial_sugar_brix is not None:
                initial_sugars.append(ferm.initial_sugar_brix)
            
            # Status counting
            if ferm.status == "COMPLETED":
                completed_count += 1
            elif ferm.status == "STUCK":
                stuck_count += 1
            
            # Get samples to calculate duration and final values
            samples = await self._sample_repo.get_samples_by_fermentation_id(ferm.id)
            historical_samples = [s for s in samples if getattr(s, 'data_source', 'HISTORICAL') == 'HISTORICAL']
            
            if historical_samples and ferm.start_date:
                # Get latest sample for duration calculation
                latest_sample = max(historical_samples, key=lambda s: s.recorded_at)
                duration_days = (latest_sample.recorded_at - ferm.start_date).days
                if duration_days > 0:
                    durations.append(duration_days)
                
                # Extract final density (from latest sample)
                if hasattr(latest_sample, 'value'):
                    sample_type = getattr(latest_sample, 'sample_type', '')
                    if sample_type == 'density':
                        final_densities.append(latest_sample.value)
                    elif sample_type == 'sugar':
                        final_sugars.append(latest_sample.value)
                
                # Also check other recent samples for density/sugar
                for sample in historical_samples:
                    sample_type = getattr(sample, 'sample_type', '')
                    if sample_type == 'density' and hasattr(sample, 'value'):
                        final_densities.append(sample.value)
                    elif sample_type == 'sugar' and hasattr(sample, 'value'):
                        final_sugars.append(sample.value)
        
        # Calculate averages
        if initial_densities:
            pattern["avg_initial_density"] = mean(initial_densities)
        if final_densities:
            pattern["avg_final_density"] = mean(final_densities)
        if initial_sugars:
            pattern["avg_initial_sugar_brix"] = mean(initial_sugars)
        if final_sugars:
            pattern["avg_final_sugar_brix"] = mean(final_sugars)
        if durations:
            pattern["avg_duration_days"] = mean(durations)
        
        # Calculate success rate
        pattern["completed_count"] = completed_count
        pattern["stuck_count"] = stuck_count
        if len(fermentations) > 0:
            pattern["success_rate"] = completed_count / len(fermentations)
        
        logger.info(
            "extract_patterns_result",
            winery_id=winery_id,
            total=len(fermentations),
            completed=completed_count,
            stuck=stuck_count,
            success_rate=pattern["success_rate"]
        )
        
        return pattern
