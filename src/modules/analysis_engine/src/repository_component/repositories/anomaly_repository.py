"""
Anomaly Repository Implementation.

Implements IAnomalyRepository using SQLAlchemy ORM.
Manages anomaly persistence and querying with multi-tenant security.
"""
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import and_, select, func, desc

from src.shared.infra.repository.base_repository import BaseRepository
from src.modules.analysis_engine.src.domain.repositories.anomaly_repository_interface import IAnomalyRepository
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel


class AnomalyRepository(BaseRepository, IAnomalyRepository):
    """
    Repository for anomaly data operations.

    Implements IAnomalyRepository using SQLAlchemy ORM with BaseRepository
    infrastructure for session management, error mapping, and multi-tenant security.
    """

    async def create(self, anomaly: Anomaly) -> Anomaly:
        """Create a new anomaly record."""
        async def _create_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                session.add(anomaly)
                await session.flush()
                return anomaly
        return await self.execute_with_error_mapping(_create_operation)

    async def get_by_id(self, anomaly_id: UUID, winery_id: UUID) -> Optional[Anomaly]:
        """Get an anomaly by ID with winery scoping."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Anomaly).join(Analysis).where(
                    and_(
                        Anomaly.id == anomaly_id,
                        Analysis.winery_id == winery_id
                    )
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        return await self.execute_with_error_mapping(_get_operation)

    async def get_by_analysis_id(self, analysis_id: UUID) -> List[Anomaly]:
        """Get all anomalies for a specific analysis."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Anomaly).where(
                    Anomaly.analysis_id == analysis_id
                ).order_by(desc(Anomaly.detected_at))
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_get_operation)

    async def get_by_fermentation_id(
        self, 
        fermentation_id: UUID,
        winery_id: UUID
    ) -> List[Anomaly]:
        """Get all anomalies for a specific fermentation across all analyses."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Anomaly).join(Analysis).where(
                    and_(
                        Analysis.fermentation_id == fermentation_id,
                        Analysis.winery_id == winery_id
                    )
                ).order_by(desc(Anomaly.detected_at))
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_get_operation)

    async def list_by_type(
        self,
        winery_id: UUID,
        anomaly_type: AnomalyType,
        skip: int = 0,
        limit: int = 100
    ) -> List[Anomaly]:
        """List anomalies by type for a winery."""
        async def _list_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Anomaly).join(Analysis).where(
                    and_(
                        Anomaly.anomaly_type == anomaly_type.value,
                        Analysis.winery_id == winery_id
                    )
                ).order_by(desc(Anomaly.detected_at)).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_list_operation)

    async def list_by_severity(
        self,
        winery_id: UUID,
        severity: SeverityLevel,
        is_resolved: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Anomaly]:
        """List anomalies by severity level for a winery."""
        async def _list_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                conditions = [
                    Anomaly.severity == severity.value,
                    Analysis.winery_id == winery_id
                ]
                if is_resolved is not None:
                    conditions.append(Anomaly.is_resolved == is_resolved)
                
                stmt = select(Anomaly).join(Analysis).where(
                    and_(*conditions)
                ).order_by(desc(Anomaly.detected_at)).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_list_operation)

    async def list_unresolved(
        self,
        winery_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Anomaly]:
        """List unresolved anomalies for a winery."""
        async def _list_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Anomaly).join(Analysis).where(
                    and_(
                        Anomaly.is_resolved == False,
                        Analysis.winery_id == winery_id
                    )
                ).order_by(desc(Anomaly.detected_at)).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_list_operation)

    async def list_by_date_range(
        self,
        winery_id: UUID,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Anomaly]:
        """List anomalies within a date range for a winery."""
        async def _list_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Anomaly).join(Analysis).where(
                    and_(
                        Anomaly.detected_at >= start_date,
                        Anomaly.detected_at <= end_date,
                        Analysis.winery_id == winery_id
                    )
                ).order_by(desc(Anomaly.detected_at)).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_list_operation)

    async def count_by_type(
        self,
        winery_id: UUID,
        anomaly_type: AnomalyType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count anomalies by type for a winery."""
        async def _count_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                conditions = [
                    Anomaly.anomaly_type == anomaly_type.value,
                    Analysis.winery_id == winery_id
                ]
                if start_date is not None:
                    conditions.append(Anomaly.detected_at >= start_date)
                if end_date is not None:
                    conditions.append(Anomaly.detected_at <= end_date)
                
                stmt = select(func.count(Anomaly.id)).join(Analysis).where(
                    and_(*conditions)
                )
                result = await session.execute(stmt)
                return result.scalar_one() or 0
        return await self.execute_with_error_mapping(_count_operation)

    async def count_by_severity(
        self,
        winery_id: UUID,
        severity: SeverityLevel,
        is_resolved: Optional[bool] = None
    ) -> int:
        """Count anomalies by severity for a winery."""
        async def _count_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                conditions = [
                    Anomaly.severity == severity.value,
                    Analysis.winery_id == winery_id
                ]
                if is_resolved is not None:
                    conditions.append(Anomaly.is_resolved == is_resolved)
                
                stmt = select(func.count(Anomaly.id)).join(Analysis).where(
                    and_(*conditions)
                )
                result = await session.execute(stmt)
                return result.scalar_one() or 0
        return await self.execute_with_error_mapping(_count_operation)

    async def update(self, anomaly: Anomaly) -> Anomaly:
        """Update an existing anomaly."""
        async def _update_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                await session.merge(anomaly)
                await session.flush()
                return anomaly
        return await self.execute_with_error_mapping(_update_operation)

    async def exists(self, anomaly_id: UUID, winery_id: UUID) -> bool:
        """Check if an anomaly exists for a winery."""
        async def _exists_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(func.count(Anomaly.id)).join(Analysis).where(
                    and_(
                        Anomaly.id == anomaly_id,
                        Analysis.winery_id == winery_id
                    )
                )
                result = await session.execute(stmt)
                return (result.scalar_one() or 0) > 0
        return await self.execute_with_error_mapping(_exists_operation)

    async def count_by_type_dict(self, winery_id: UUID) -> Dict[str, int]:
        """Get count of anomalies by type (helper method)."""
        async def _count_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(
                    Anomaly.anomaly_type,
                    func.count(Anomaly.id).label("count")
                ).join(Analysis).where(
                    Analysis.winery_id == winery_id
                ).group_by(Anomaly.anomaly_type)
                result = await session.execute(stmt)
                return {row[0]: row[1] for row in result.all()}
        return await self.execute_with_error_mapping(_count_operation)
