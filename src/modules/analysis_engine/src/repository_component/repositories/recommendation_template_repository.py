"""
RecommendationTemplate Repository Implementation.

Implements IRecommendationTemplateRepository using SQLAlchemy ORM.
Manages recommendation template persistence and querying.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select, func, desc, asc

from src.shared.infra.repository.base_repository import BaseRepository
from src.modules.analysis_engine.src.domain.repositories.recommendation_template_repository_interface import IRecommendationTemplateRepository
from src.modules.analysis_engine.src.domain.entities.recommendation_template import RecommendationTemplate
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.recommendation_category import RecommendationCategory


class RecommendationTemplateRepository(BaseRepository, IRecommendationTemplateRepository):
    """
    Repository for recommendation template data operations.

    Implements IRecommendationTemplateRepository using SQLAlchemy ORM with BaseRepository
    infrastructure for session management and error mapping.
    """

    async def add(self, template: RecommendationTemplate) -> RecommendationTemplate:
        """Add a new recommendation template."""
        async def _add_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                session.add(template)
                await session.flush()
                return template
        return await self.execute_with_error_mapping(_add_operation)

    async def get_by_id(self, template_id: UUID) -> Optional[RecommendationTemplate]:
        """Get a template by its ID."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(RecommendationTemplate).where(
                    RecommendationTemplate.id == template_id
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        return await self.execute_with_error_mapping(_get_operation)

    async def get_by_code(self, code: str) -> Optional[RecommendationTemplate]:
        """Get a template by its unique code."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(RecommendationTemplate).where(
                    RecommendationTemplate.code == code
                )
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        return await self.execute_with_error_mapping(_get_operation)

    async def list_by_category(
        self,
        category: RecommendationCategory,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[RecommendationTemplate]:
        """List templates by category."""
        async def _list_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(RecommendationTemplate).where(
                    and_(
                        RecommendationTemplate.category == category.value,
                        RecommendationTemplate.is_active == is_active
                    )
                ).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_list_operation)

    async def list_by_anomaly_type(
        self,
        anomaly_type: AnomalyType,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[RecommendationTemplate]:
        """List templates applicable to a specific anomaly type."""
        async def _list_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                anomaly_value = anomaly_type.value
                # Filter templates where applicable_anomaly_types contains the anomaly
                stmt = select(RecommendationTemplate).where(
                    and_(
                        RecommendationTemplate.applicable_anomaly_types.contains([anomaly_value]),
                        RecommendationTemplate.is_active == is_active
                    )
                ).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_list_operation)

    async def list_active(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[RecommendationTemplate]:
        """List all active templates."""
        async def _list_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(RecommendationTemplate).where(
                    RecommendationTemplate.is_active == True
                ).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_list_operation)

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[RecommendationTemplate]:
        """List all templates (active and inactive)."""
        async def _list_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(RecommendationTemplate).offset(skip).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_list_operation)

    async def update(self, template: RecommendationTemplate) -> RecommendationTemplate:
        """Update an existing template."""
        async def _update_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                await session.merge(template)
                await session.flush()
                return template
        return await self.execute_with_error_mapping(_update_operation)

    async def delete(self, template_id: UUID) -> bool:
        """Delete a template by ID."""
        async def _delete_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(RecommendationTemplate).where(
                    RecommendationTemplate.id == template_id
                )
                result = await session.execute(stmt)
                template = result.scalar_one_or_none()
                if template is None:
                    return False
                await session.delete(template)
                await session.flush()
                return True
        return await self.execute_with_error_mapping(_delete_operation)

    async def count_active(self) -> int:
        """Count active templates."""
        async def _count_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(func.count(RecommendationTemplate.id)).where(
                    RecommendationTemplate.is_active == True
                )
                result = await session.execute(stmt)
                return result.scalar()
        return await self.execute_with_error_mapping(_count_operation)

    async def get_most_used(
        self,
        limit: int = 10
    ) -> List[RecommendationTemplate]:
        """Get the most frequently used templates."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                stmt = select(RecommendationTemplate).order_by(
                    desc(RecommendationTemplate.times_applied)
                ).limit(limit)
                result = await session.execute(stmt)
                return result.scalars().all()
        return await self.execute_with_error_mapping(_get_operation)
