"""
Repository interface for Anomaly entity.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..entities.anomaly import Anomaly
from ..enums.anomaly_type import AnomalyType
from ..enums.severity_level import SeverityLevel


class IAnomalyRepository(ABC):
    """
    Repository interface for Anomaly entity.
    
    Note: Anomalies are typically managed through the Analysis aggregate,
    but this repository provides direct access for queries and reporting.
    """
    
    @abstractmethod
    async def get_by_id(self, anomaly_id: UUID) -> Optional[Anomaly]:
        """
        Get an anomaly by its ID.
        
        Args:
            anomaly_id: The anomaly ID
            
        Returns:
            The anomaly if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_analysis_id(self, analysis_id: UUID) -> List[Anomaly]:
        """
        Get all anomalies for a specific analysis.
        
        Args:
            analysis_id: The analysis ID
            
        Returns:
            List of anomalies for the analysis
        """
        pass
    
    @abstractmethod
    async def get_by_fermentation_id(
        self, 
        fermentation_id: UUID,
        winery_id: UUID
    ) -> List[Anomaly]:
        """
        Get all anomalies for a specific fermentation across all analyses.
        
        Args:
            fermentation_id: The fermentation ID
            winery_id: The winery ID (for multi-tenancy)
            
        Returns:
            List of anomalies for the fermentation
        """
        pass
    
    @abstractmethod
    async def list_by_type(
        self,
        winery_id: UUID,
        anomaly_type: AnomalyType,
        skip: int = 0,
        limit: int = 100
    ) -> List[Anomaly]:
        """
        List anomalies by type for a winery.
        
        Args:
            winery_id: The winery ID
            anomaly_type: The type of anomaly to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of anomalies
        """
        pass
    
    @abstractmethod
    async def list_by_severity(
        self,
        winery_id: UUID,
        severity: SeverityLevel,
        is_resolved: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Anomaly]:
        """
        List anomalies by severity level for a winery.
        
        Args:
            winery_id: The winery ID
            severity: The severity level to filter by
            is_resolved: Optional filter for resolved status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of anomalies
        """
        pass
    
    @abstractmethod
    async def list_unresolved(
        self,
        winery_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Anomaly]:
        """
        List unresolved anomalies for a winery.
        
        Args:
            winery_id: The winery ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of unresolved anomalies
        """
        pass
    
    @abstractmethod
    async def list_by_date_range(
        self,
        winery_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Anomaly]:
        """
        List anomalies within a date range for a winery.
        
        Args:
            winery_id: The winery ID
            start_date: Start of date range
            end_date: End of date range
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of anomalies
        """
        pass
    
    @abstractmethod
    async def count_by_type(
        self,
        winery_id: UUID,
        anomaly_type: AnomalyType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Count anomalies by type for a winery.
        
        Args:
            winery_id: The winery ID
            anomaly_type: The anomaly type
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            Number of anomalies
        """
        pass
    
    @abstractmethod
    async def count_by_severity(
        self,
        winery_id: UUID,
        severity: SeverityLevel,
        is_resolved: Optional[bool] = None
    ) -> int:
        """
        Count anomalies by severity for a winery.
        
        Args:
            winery_id: The winery ID
            severity: The severity level
            is_resolved: Optional filter for resolved status
            
        Returns:
            Number of anomalies
        """
        pass
