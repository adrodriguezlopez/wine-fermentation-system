"""
PatternAnalysisService - Service for extracting patterns from fermentation data.

Implements statistical aggregation and pattern analysis for Analysis Engine.
Created as part of ADR-034 refactoring - extracted from HistoricalDataService.

Implementation Status: ✅ IMPLEMENTED (January 15, 2026)
Part of ADR-034 refactoring to eliminate redundancy.

Related ADRs:
- ADR-034: Historical Data Service Refactoring
- ADR-032: Historical Data API Layer (original context)
- ADR-025: Multi-Tenancy Architecture
- ADR-027: Structured Logging
"""

from typing import Dict, Any, Optional, Tuple
from datetime import date
from statistics import mean

# ADR-027: Structured logging
from src.shared.wine_fermentator_logging import get_logger

from src.modules.fermentation.src.service_component.interfaces.pattern_analysis_service_interface import (
    IPatternAnalysisService,
)
from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository

logger = get_logger(__name__)


class PatternAnalysisService(IPatternAnalysisService):
    """
    Service for pattern extraction and statistical analysis of fermentation data.
    
    Responsibilities:
    - Aggregate metrics from fermentation datasets
    - Calculate statistical patterns (averages, success rates)
    - Support filtering by winery, data source, fruit origin, date range
    - Provide insights for Analysis Engine
    
    Design:
    - Single Responsibility: Only pattern aggregation (no CRUD)
    - Data source agnostic: Works with any fermentation data
    - Depends on abstractions (IFermentationRepository, ISampleRepository)
    - Returns structured pattern dictionaries
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
    
    async def extract_patterns(
        self,
        winery_id: int,
        data_source: Optional[str] = None,
        fruit_origin_id: Optional[int] = None,
        date_range: Optional[Tuple[date, date]] = None
    ) -> Dict[str, Any]:
        """
        Extract aggregated patterns from fermentation data.
        
        Computes statistical aggregations across multiple fermentations:
        - Average initial/final density and sugar levels
        - Average fermentation duration
        - Success rate (completed vs stuck/failed)
        - Common patterns and issues
        
        Args:
            winery_id: Winery ID for multi-tenant filtering (REQUIRED)
            data_source: Optional filter by data source (SYSTEM, HISTORICAL, MIGRATED)
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
            data_source=data_source,
            fruit_origin_id=fruit_origin_id,
            date_range=date_range
        )
        
        # Get fermentations with filters
        if data_source:
            fermentations = await self._fermentation_repo.list_by_data_source(
                winery_id=winery_id,
                data_source=data_source,
                include_deleted=False
            )
        else:
            # Get all fermentations for winery
            fermentations = await self._fermentation_repo.list_by_winery(
                winery_id=winery_id,
                include_deleted=False
            )
        
        # Apply additional filters in-memory (TODO: push to repository layer)
        if fruit_origin_id:
            fermentations = [f for f in fermentations if f.fruit_origin_id == fruit_origin_id]
        
        if date_range:
            from datetime import datetime
            start_date_filter = date_range[0]
            end_date_filter = date_range[1]
            fermentations = [
                f for f in fermentations 
                if f.start_date and (
                    f.start_date.date() if isinstance(f.start_date, datetime) else f.start_date
                ) >= start_date_filter and (
                    f.start_date.date() if isinstance(f.start_date, datetime) else f.start_date
                ) <= end_date_filter
            ]
        
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
            
            # Filter by data_source if specified
            if data_source:
                samples = [s for s in samples if getattr(s, 'data_source', None) == data_source]
            
            if samples and ferm.start_date:
                # Get latest sample for duration calculation
                latest_sample = max(samples, key=lambda s: s.recorded_at)
                from datetime import datetime
                start_date = ferm.start_date if isinstance(ferm.start_date, datetime) else datetime.combine(ferm.start_date, datetime.min.time())
                duration_days = (latest_sample.recorded_at - start_date).days
                if duration_days > 0:
                    durations.append(duration_days)
                
                # Extract final density/sugar (from latest sample)
                if hasattr(latest_sample, 'value'):
                    sample_type = getattr(latest_sample, 'sample_type', '')
                    if sample_type == 'density':
                        final_densities.append(latest_sample.value)
                    elif sample_type == 'sugar':
                        final_sugars.append(latest_sample.value)
                
                # Also check other recent samples for density/sugar
                for sample in samples:
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
            data_source=data_source,
            total=len(fermentations),
            completed=completed_count,
            stuck=stuck_count,
            success_rate=pattern["success_rate"]
        )
        
        return pattern
