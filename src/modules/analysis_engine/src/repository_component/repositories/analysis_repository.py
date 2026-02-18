"""
Analysis Repository Implementation.

Concrete implementation of IAnalysisRepository that extends BaseRepository
and provides database operations for fermentation analysis management.

Following project patterns:
- Extends BaseRepository for session management and error handling
- Multi-tenant scoping with winery_id
- Structured logging with LogTimer (ADR-027)
- Returns ORM entities directly (no DTO mapping)
- Async operations with SQLAlchemy
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from src.shared.wine_fermentator_logging import get_logger, LogTimer
from src.modules.analysis_engine.src.domain.repositories.analysis_repository_interface import IAnalysisRepository
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus
from src.shared.infra.repository.base_repository import BaseRepository

logger = get_logger(__name__)


class AnalysisRepository(BaseRepository, IAnalysisRepository):
    """
    Repository for analysis data operations.

    Implements IAnalysisRepository using SQLAlchemy ORM with BaseRepository
    infrastructure for session management, error mapping, and multi-tenant security.
    
    Following project pattern: Works directly with Analysis entity (Entity = ORM Model).
    """

    async def create(
        self,
        fermentation_id: UUID,
        winery_id: UUID,
        comparison_result: Dict[str, Any],
        confidence_level: Dict[str, Any]
    ) -> Analysis:
        """
        Creates a new analysis record.

        Args:
            fermentation_id: ID of the fermentation being analyzed
            winery_id: ID of the winery (for multi-tenancy)
            comparison_result: Historical comparison result data (JSONB)
            confidence_level: Confidence level data (JSONB)

        Returns:
            Analysis: Created analysis entity

        Raises:
            RepositoryError: If creation fails
        """
        async def _create_operation():
            with LogTimer(logger, "create_analysis"):
                logger.info(
                    "creating_analysis",
                    fermentation_id=str(fermentation_id),
                    winery_id=str(winery_id)
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    analysis = Analysis(
                        fermentation_id=fermentation_id,
                        winery_id=winery_id,
                        analyzed_at=datetime.now(timezone.utc),
                        status=AnalysisStatus.PENDING.value,
                        comparison_result=comparison_result,
                        confidence_level=confidence_level,
                        historical_samples_count=confidence_level.get("historical_samples_count", 0)
                    )

                    session.add(analysis)
                    await session.flush()
                    
                    logger.info(
                        "analysis_created",
                        analysis_id=str(analysis.id),
                        fermentation_id=str(fermentation_id),
                        status=analysis.status
                    )
                    
                    return analysis

        return await self.execute_with_error_mapping(_create_operation)

    async def get_by_id(self, analysis_id: UUID, winery_id: UUID) -> Optional[Analysis]:
        """
        Retrieves an analysis by its ID with winery access control.

        Args:
            analysis_id: ID of the analysis to retrieve
            winery_id: Winery ID for access control

        Returns:
            Optional[Analysis]: Analysis entity or None if not found
        """
        async def _get_operation():
            with LogTimer(logger, "get_analysis_by_id"):
                logger.debug(
                    "fetching_analysis",
                    analysis_id=str(analysis_id),
                    winery_id=str(winery_id)
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(Analysis).where(
                        Analysis.id == analysis_id,
                        Analysis.winery_id == winery_id
                    )

                    result = await session.execute(query)
                    analysis = result.scalar_one_or_none()
                    
                    if analysis:
                        logger.debug(
                            "analysis_found",
                            analysis_id=str(analysis_id),
                            status=analysis.status
                        )
                    else:
                        logger.warning(
                            "analysis_not_found",
                            analysis_id=str(analysis_id),
                            winery_id=str(winery_id)
                        )
                    
                    return analysis

        return await self.execute_with_error_mapping(_get_operation)

    async def get_by_fermentation_id(
        self,
        fermentation_id: UUID,
        winery_id: UUID
    ) -> List[Analysis]:
        """
        Retrieves all analyses for a specific fermentation.

        Args:
            fermentation_id: ID of the fermentation
            winery_id: Winery ID for access control

        Returns:
            List[Analysis]: List of analyses (may be empty)
        """
        async def _get_operation():
            with LogTimer(logger, "get_analyses_by_fermentation"):
                logger.debug(
                    "fetching_analyses_by_fermentation",
                    fermentation_id=str(fermentation_id),
                    winery_id=str(winery_id)
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(Analysis).where(
                        Analysis.fermentation_id == fermentation_id,
                        Analysis.winery_id == winery_id
                    ).order_by(Analysis.analyzed_at.desc())

                    result = await session.execute(query)
                    analyses = result.scalars().all()
                    
                    logger.debug(
                        "analyses_retrieved",
                        fermentation_id=str(fermentation_id),
                        count=len(analyses)
                    )
                    
                    return list(analyses)

        return await self.execute_with_error_mapping(_get_operation)

    async def update_status(
        self,
        analysis_id: UUID,
        winery_id: UUID,
        status: AnalysisStatus
    ) -> Optional[Analysis]:
        """
        Updates the status of an analysis.

        Args:
            analysis_id: ID of the analysis to update
            winery_id: Winery ID for access control
            status: New status

        Returns:
            Optional[Analysis]: Updated analysis or None if not found
        """
        async def _update_operation():
            with LogTimer(logger, "update_analysis_status"):
                logger.info(
                    "updating_analysis_status",
                    analysis_id=str(analysis_id),
                    winery_id=str(winery_id),
                    new_status=status.value
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    # Get existing analysis
                    query = select(Analysis).where(
                        Analysis.id == analysis_id,
                        Analysis.winery_id == winery_id
                    )
                    result = await session.execute(query)
                    analysis = result.scalar_one_or_none()
                    
                    if not analysis:
                        logger.warning(
                            "analysis_not_found_for_update",
                            analysis_id=str(analysis_id),
                            winery_id=str(winery_id)
                        )
                        return None
                    
                    # Update status
                    analysis.status = status.value
                    await session.flush()
                    
                    logger.info(
                        "analysis_status_updated",
                        analysis_id=str(analysis_id),
                        old_status=query,
                        new_status=status.value
                    )
                    
                    return analysis

        return await self.execute_with_error_mapping(_update_operation)

    async def list_by_winery(
        self,
        winery_id: UUID,
        status: Optional[AnalysisStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Analysis]:
        """
        Lists all analyses for a winery with pagination.

        Args:
            winery_id: Winery ID for filtering
            status: Optional status filter
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List[Analysis]: List of analyses
        """
        async def _list_operation():
            with LogTimer(logger, "list_analyses_by_winery"):
                logger.debug(
                    "listing_analyses",
                    winery_id=str(winery_id),
                    status=status.value if status else None,
                    limit=limit,
                    offset=offset
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(Analysis).where(
                        Analysis.winery_id == winery_id
                    )
                    
                    # Add status filter if provided
                    if status:
                        query = query.where(Analysis.status == status.value)
                    
                    query = query.order_by(
                        Analysis.analyzed_at.desc()
                    ).limit(limit).offset(offset)

                    result = await session.execute(query)
                    analyses = result.scalars().all()
                    
                    logger.debug(
                        "analyses_listed",
                        winery_id=str(winery_id),
                        count=len(analyses)
                    )
                    
                    return list(analyses)

        return await self.execute_with_error_mapping(_list_operation)

    async def delete(self, analysis_id: UUID, winery_id: UUID) -> bool:
        """
        Deletes an analysis (hard delete).

        Args:
            analysis_id: ID of the analysis to delete
            winery_id: Winery ID for access control

        Returns:
            bool: True if deleted, False if not found
        """
        async def _delete_operation():
            with LogTimer(logger, "delete_analysis"):
                logger.info(
                    "deleting_analysis",
                    analysis_id=str(analysis_id),
                    winery_id=str(winery_id)
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(Analysis).where(
                        Analysis.id == analysis_id,
                        Analysis.winery_id == winery_id
                    )
                    result = await session.execute(query)
                    analysis = result.scalar_one_or_none()
                    
                    if not analysis:
                        logger.warning(
                            "analysis_not_found_for_delete",
                            analysis_id=str(analysis_id),
                            winery_id=str(winery_id)
                        )
                        return False
                    
                    await session.delete(analysis)
                    await session.flush()
                    
                    logger.info(
                        "analysis_deleted",
                        analysis_id=str(analysis_id)
                    )
                    
                    return True

        return await self.execute_with_error_mapping(_delete_operation)

    async def add(self, analysis: Analysis) -> Analysis:
        """
        Add a new analysis to the repository.
        
        Args:
            analysis: The analysis model to persist
            
        Returns:
            The persisted analysis with any generated fields
        """
        async def _add_operation():
            with LogTimer(logger, "add_analysis"):
                logger.info(
                    "adding_analysis",
                    fermentation_id=str(analysis.fermentation_id),
                    winery_id=str(analysis.winery_id)
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    session.add(analysis)
                    await session.flush()
                    
                    logger.info(
                        "analysis_added",
                        analysis_id=str(analysis.id),
                        status=analysis.status
                    )
                    
                    return analysis

        return await self.execute_with_error_mapping(_add_operation)

    async def get_latest_by_fermentation_id(
        self,
        fermentation_id: UUID,
        winery_id: UUID
    ) -> Optional[Analysis]:
        """
        Get the most recent analysis for a fermentation.
        
        Args:
            fermentation_id: The fermentation ID
            winery_id: The winery ID (for multi-tenancy)
            
        Returns:
            The latest analysis if exists, None otherwise
        """
        async def _get_latest_operation():
            with LogTimer(logger, "get_latest_analysis_by_fermentation"):
                logger.debug(
                    "fetching_latest_analysis",
                    fermentation_id=str(fermentation_id),
                    winery_id=str(winery_id)
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(Analysis).where(
                        Analysis.fermentation_id == fermentation_id,
                        Analysis.winery_id == winery_id
                    ).order_by(Analysis.analyzed_at.desc()).limit(1)

                    result = await session.execute(query)
                    analysis = result.scalar_one_or_none()
                    
                    if analysis:
                        logger.debug(
                            "latest_analysis_found",
                            analysis_id=str(analysis.id),
                            analyzed_at=analysis.analyzed_at.isoformat()
                        )
                    else:
                        logger.debug(
                            "no_analysis_found_for_fermentation",
                            fermentation_id=str(fermentation_id)
                        )
                    
                    return analysis

        return await self.execute_with_error_mapping(_get_latest_operation)

    async def list_by_date_range(
        self,
        winery_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """
        List analyses within a date range for a winery.
        
        Args:
            winery_id: The winery ID
            start_date: Start of date range
            end_date: End of date range
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of analyses
        """
        async def _list_by_date_operation():
            with LogTimer(logger, "list_analyses_by_date_range"):
                logger.debug(
                    "listing_analyses_by_date_range",
                    winery_id=str(winery_id),
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    skip=skip,
                    limit=limit
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(Analysis).where(
                        Analysis.winery_id == winery_id,
                        Analysis.analyzed_at >= start_date,
                        Analysis.analyzed_at <= end_date
                    ).order_by(
                        Analysis.analyzed_at.desc()
                    ).offset(skip).limit(limit)

                    result = await session.execute(query)
                    analyses = result.scalars().all()
                    
                    logger.debug(
                        "analyses_listed_by_date_range",
                        winery_id=str(winery_id),
                        count=len(analyses)
                    )
                    
                    return list(analyses)

        return await self.execute_with_error_mapping(_list_by_date_operation)

    async def update(self, analysis: Analysis) -> Analysis:
        """
        Update an existing analysis.
        
        Args:
            analysis: The analysis model with updated data
            
        Returns:
            The updated analysis
        """
        async def _update_operation():
            with LogTimer(logger, "update_analysis"):
                logger.info(
                    "updating_analysis",
                    analysis_id=str(analysis.id),
                    winery_id=str(analysis.winery_id),
                    status=analysis.status
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    # Merge the detached instance into the session
                    merged_analysis = await session.merge(analysis)
                    await session.flush()
                    
                    logger.info(
                        "analysis_updated",
                        analysis_id=str(merged_analysis.id),
                        status=merged_analysis.status
                    )
                    
                    return merged_analysis

        return await self.execute_with_error_mapping(_update_operation)

    async def count_by_winery(
        self,
        winery_id: UUID,
        status: Optional[AnalysisStatus] = None
    ) -> int:
        """
        Count analyses for a winery.
        
        Args:
            winery_id: The winery ID
            status: Optional status filter
            
        Returns:
            Number of analyses
        """
        async def _count_operation():
            with LogTimer(logger, "count_analyses_by_winery"):
                logger.debug(
                    "counting_analyses",
                    winery_id=str(winery_id),
                    status=status.value if status else None
                )
                
                from sqlalchemy import func
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(func.count(Analysis.id)).where(
                        Analysis.winery_id == winery_id
                    )
                    
                    if status:
                        query = query.where(Analysis.status == status.value)

                    result = await session.execute(query)
                    count = result.scalar()
                    
                    logger.debug(
                        "analyses_counted",
                        winery_id=str(winery_id),
                        count=count
                    )
                    
                    return count or 0

        return await self.execute_with_error_mapping(_count_operation)

    async def get_by_winery(self, winery_id: UUID) -> List[Analysis]:
        """
        Get all analyses for a winery (simplified version of list_by_winery).
        
        Args:
            winery_id: The winery ID
            
        Returns:
            List of all analyses for the winery
        """
        return await self.list_by_winery(winery_id, limit=1000)

    async def get_by_status(self, winery_id: UUID, status: AnalysisStatus) -> List[Analysis]:
        """
        Get analyses filtered by status.
        
        Args:
            winery_id: The winery ID
            status: The status to filter by
            
        Returns:
            List of analyses with the specified status
        """
        return await self.list_by_winery(winery_id, status=status, limit=1000)

    async def get_recent(self, winery_id: UUID, limit: int = 10) -> List[Analysis]:
        """
        Get most recent analyses for a winery.
        
        Args:
            winery_id: The winery ID
            limit: Maximum number of analyses to return
            
        Returns:
            List of recent analyses ordered by analyzed_at DESC
        """
        return await self.list_by_winery(winery_id, limit=limit)

    async def exists(self, analysis_id: UUID, winery_id: UUID) -> bool:
        """
        Check if an analysis exists.
        
        Args:
            analysis_id: The analysis ID
            winery_id: The winery ID (for multi-tenancy)
            
        Returns:
            True if exists, False otherwise
        """
        result = await self.get_by_id(analysis_id, winery_id)
        return result is not None

    async def count_by_status(self, winery_id: UUID) -> dict:
        """
        Count analyses grouped by status.
        
        Args:
            winery_id: The winery ID
            
        Returns:
            Dictionary mapping AnalysisStatus to count
        """
        async def _count_by_status_operation():
            with LogTimer(logger, "count_analyses_by_status"):
                logger.debug(
                    "counting_analyses_by_status",
                    winery_id=str(winery_id)
                )
                
                from sqlalchemy import func
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(
                        Analysis.status,
                        func.count(Analysis.id)
                    ).where(
                        Analysis.winery_id == winery_id
                    ).group_by(Analysis.status)

                    result = await session.execute(query)
                    rows = result.all()
                    
                    # Convert to dict with AnalysisStatus keys
                    counts = {}
                    for status_value, count in rows:
                        status = AnalysisStatus(status_value)
                        counts[status] = count
                    
                    logger.debug(
                        "analyses_counted_by_status",
                        winery_id=str(winery_id),
                        counts=counts
                    )
                    
                    return counts

        return await self.execute_with_error_mapping(_count_by_status_operation)
