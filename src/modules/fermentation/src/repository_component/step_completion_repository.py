"""
StepCompletion Repository Implementation

Async repository for StepCompletion entity persistence.
Uses SQLAlchemy async session for database operations.
Handles audit log entries for protocol step execution.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion
from src.modules.fermentation.src.domain.enums.step_type import SkipReason
from src.modules.fermentation.src.domain.repositories.step_completion_repository_interface import (
    IStepCompletionRepository
)


class StepCompletionRepository(IStepCompletionRepository):
    """Repository for StepCompletion persistence operations"""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with async session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
    
    async def create(self, completion: StepCompletion) -> StepCompletion:
        """
        Create and persist a new step completion record.
        
        Args:
            completion: StepCompletion entity to create
            
        Returns:
            Created completion with ID assigned
        """
        self.session.add(completion)
        await self.session.flush()
        return completion
    
    async def get_by_id(self, completion_id: int) -> Optional[StepCompletion]:
        """
        Get completion record by ID.
        
        Args:
            completion_id: ID of completion to retrieve
            
        Returns:
            Completion if found, None otherwise
        """
        stmt = select(StepCompletion).where(StepCompletion.id == completion_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all(self) -> List[StepCompletion]:
        """
        Get all step completion records.
        
        Returns:
            List of all StepCompletion entities
        """
        stmt = select(StepCompletion).order_by(StepCompletion.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update(self, completion: StepCompletion) -> StepCompletion:
        """
        Update an existing step completion record.
        
        Args:
            completion: StepCompletion entity with updated values
            
        Returns:
            Updated completion
        """
        await self.session.merge(completion)
        await self.session.flush()
        return completion
    
    async def delete(self, completion_id: int) -> bool:
        """
        Delete a step completion record by ID.
        
        Args:
            completion_id: ID of completion to delete
            
        Returns:
            True if deleted, False if not found
        """
        completion = await self.get_by_id(completion_id)
        if completion is None:
            return False
        
        await self.session.delete(completion)
        await self.session.flush()
        return True
    
    async def get_by_execution(self, execution_id: int) -> List[StepCompletion]:
        """
        Get all completion records for a protocol execution.
        
        Args:
            execution_id: ID of protocol execution
            
        Returns:
            List of StepCompletion entities for execution, ordered by created_at
        """
        stmt = select(StepCompletion).where(
            StepCompletion.execution_id == execution_id
        ).order_by(StepCompletion.created_at)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_step(self, step_id: int) -> List[StepCompletion]:
        """
        Get all completion records for a protocol step.
        
        Retrieves all instances where this step was executed across all executions.
        
        Args:
            step_id: ID of protocol step
            
        Returns:
            List of StepCompletion entities for step, ordered by created_at desc
        """
        stmt = select(StepCompletion).where(
            StepCompletion.step_id == step_id
        ).order_by(StepCompletion.created_at.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_execution_and_step(
        self,
        execution_id: int,
        step_id: int
    ) -> Optional[StepCompletion]:
        """
        Get completion record for a specific step in a specific execution.
        
        Args:
            execution_id: ID of protocol execution
            step_id: ID of protocol step
            
        Returns:
            Completion if found, None otherwise (typically should be at most one)
        """
        stmt = select(StepCompletion).where(
            and_(
                StepCompletion.execution_id == execution_id,
                StepCompletion.step_id == step_id
            )
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def record_completion(
        self,
        execution_id: int,
        step_id: int,
        completed_by: int,
        notes: Optional[str] = None
    ) -> StepCompletion:
        """
        Record a step completion.
        
        Creates a new completion record with completed status.
        
        Args:
            execution_id: ID of protocol execution
            step_id: ID of protocol step
            completed_by: ID of user who completed step
            notes: Optional completion notes/observations
            
        Returns:
            Created StepCompletion record
        """
        completion = StepCompletion(
            execution_id=execution_id,
            step_id=step_id,
            completed_by=completed_by,
            is_skipped=False,
            skip_reason=None,
            notes=notes,
            created_at=datetime.utcnow()
        )
        
        return await self.create(completion)
    
    async def record_skip(
        self,
        execution_id: int,
        step_id: int,
        reason: SkipReason,
        skipped_by: int,
        notes: Optional[str] = None
    ) -> StepCompletion:
        """
        Record a step skip.
        
        Creates a new completion record with skipped status.
        
        Args:
            execution_id: ID of protocol execution
            step_id: ID of protocol step
            reason: SkipReason enum explaining why step was skipped
            skipped_by: ID of user who skipped step
            notes: Optional skip notes/explanation
            
        Returns:
            Created StepCompletion record with is_skipped=True
        """
        completion = StepCompletion(
            execution_id=execution_id,
            step_id=step_id,
            completed_by=skipped_by,
            is_skipped=True,
            skip_reason=reason,
            notes=notes,
            created_at=datetime.utcnow()
        )
        
        return await self.create(completion)
