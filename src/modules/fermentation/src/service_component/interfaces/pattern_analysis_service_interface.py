"""
IPatternAnalysisService - Interface for pattern extraction from fermentation data.

Defines contract for statistical aggregation and pattern analysis.
Created as part of ADR-034 refactoring to extract unique logic from HistoricalDataService.

Related ADRs:
- ADR-034: Historical Data Service Refactoring
- ADR-032: Historical Data API Layer (original context)
- ADR-025: Multi-Tenancy Architecture
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from datetime import date


class IPatternAnalysisService(ABC):
    """
    Interface for pattern extraction and analysis from fermentation data.
    
    Responsibilities:
    - Extract aggregated patterns from fermentation datasets
    - Compute statistical metrics (averages, success rates)
    - Support filtering by winery, fruit origin, and date range
    - Enable Analysis Engine with historical insights
    
    Design Principles:
    - Single Responsibility: Only pattern aggregation logic
    - Data source agnostic: Works with any fermentation data
    - Multi-tenant: Respects winery_id boundaries
    - Read-only: No data modification
    """
    
    @abstractmethod
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
                
        Raises:
            RepositoryError: If database query fails
        """
        pass
