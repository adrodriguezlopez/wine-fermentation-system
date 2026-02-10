"""
Recommendation Repository Implementation.

Implements IRecommendationRepository using SQLAlchemy ORM.
Manages recommendation persistence and querying with multi-tenant security.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select, func, desc

from src.shared.infra.repository.base_repository import BaseRepository
from src.modules.analysis_engine.src.domain.repositories.recommendation_repository_interface import IRecommendationRepository
from src.modules.analysis_engine.src.domain.entities.recommendation import Recommendation
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly


class RecommendationRepository(BaseRepository, IRecommendationRepository):
    """
    Repository for recommendation data operations.

    Implements IRecommendationRepository using SQLAlchemy ORM with BaseRepository
    infrastructure for session management, error mapping, and multi-tenant security.
    """

    async def get_by_id(self, recommendation_id: UUID) -> Optional[Recommendation]:
        """Get a recommendation by its ID."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Recommendation).where(
                    Recommendation.id == recommendation_id
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        return await self.execute_with_error_mapping(_get_operation)

    async def get_by_analysis_id(self, analysis_id: UUID) -> List[Recommendation]:
        """Get all recommendations for a specific analysis."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Recommendation).where(
                    Recommendation.analysis_id == analysis_id
                ).order_by(desc(Recommendation.priority))
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_get_operation)

    async def get_by_anomaly_id(self, anomaly_id: UUID) -> List[Recommendation]:
        """Get all recommendations addressing a specific anomaly."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Recommendation).where(
                    Recommendation.anomaly_id == anomaly_id
                ).order_by(desc(Recommendation.priority))
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_get_operation)

    async def get_by_fermentation_id(
        self, 
        fermentation_id: UUID,
        winery_id: UUID
    ) -> List[Recommendation]:
        """Get all recommendations for a specific fermentation."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Recommendation).join(Analysis).where(
                    and_(
                        Analysis.fermentation_id == fermentation_id,
                        Analysis.winery_id == winery_id
                    )
                ).order_by(desc(Recommendation.priority))
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_get_operation)

    async def list_by_template(
        self,
        winery_id: UUID,
        template_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Recommendation]:
        """List recommendations by template for a winery."""
        async def _list_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Recommendation).join(Analysis).where(
                    and_(
                        Recommendation.recommendation_template_id == template_id,
                        Analysis.winery_id == winery_id
                    )
                ).order_by(desc(Recommendation.priority)).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_list_operation)

    async def list_by_priority(
        self,
        winery_id: UUID,
        min_priority: int = 1,
        max_priority: Optional[int] = None,
        is_applied: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Recommendation]:
        """List recommendations by priority range for a winery."""
        async def _list_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                conditions = [
                    Recommendation.priority >= min_priority,
                    Analysis.winery_id == winery_id
                ]
                if max_priority is not None:
                    conditions.append(Recommendation.priority <= max_priority)
                if is_applied is not None:
                    conditions.append(Recommendation.is_applied == is_applied)
                
                stmt = select(Recommendation).join(Analysis).where(
                    and_(*conditions)
                ).order_by(Recommendation.priority).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_list_operation)

    async def list_unapplied(
        self,
        winery_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Recommendation]:
        """List unapplied recommendations for a winery."""
        async def _list_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(Recommendation).join(Analysis).where(
                    and_(
                        Recommendation.is_applied == False,
                        Analysis.winery_id == winery_id
                    )
                ).order_by(Recommendation.priority).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_list_operation)

    async def count_by_template(
        self,
        winery_id: UUID,
        template_id: UUID,
        is_applied: Optional[bool] = None
    ) -> int:
        """Count recommendations by template for a winery."""
        async def _count_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                conditions = [
                    Recommendation.recommendation_template_id == template_id,
                    Analysis.winery_id == winery_id
                ]
                if is_applied is not None:
                    conditions.append(Recommendation.is_applied == is_applied)
                
                stmt = select(func.count(Recommendation.id)).join(Analysis).where(
                    and_(*conditions)
                )
                result = await session.execute(stmt)
                return result.scalar_one() or 0
        return await self.execute_with_error_mapping(_count_operation)

    async def get_application_rate_by_template(
        self,
        winery_id: UUID,
        template_id: UUID
    ) -> float:
        """Calculate the application rate for a template."""
        async def _rate_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Count total recommendations for template
                total_stmt = select(func.count(Recommendation.id)).join(Analysis).where(
                    and_(
                        Recommendation.recommendation_template_id == template_id,
                        Analysis.winery_id == winery_id
                    )
                )
                total_result = await session.execute(total_stmt)
                total_count = total_result.scalar_one() or 0
                
                if total_count == 0:
                    return 0.0
                
                # Count applied recommendations for template
                applied_stmt = select(func.count(Recommendation.id)).join(Analysis).where(
                    and_(
                        Recommendation.recommendation_template_id == template_id,
                        Recommendation.is_applied == True,
                        Analysis.winery_id == winery_id
                    )
                )
                applied_result = await session.execute(applied_stmt)
                applied_count = applied_result.scalar_one() or 0
                
                return float(applied_count) / float(total_count)
        return await self.execute_with_error_mapping(_rate_operation)
