"""
Repository Interface for StepCompletion
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion


class IStepCompletionRepository(ABC):
    """Repository interface for StepCompletion entity"""
    
    @abstractmethod
    async def create(self, completion: StepCompletion) -> StepCompletion:
        """Create and persist a new step completion record"""
        pass
    
    @abstractmethod
    async def get_by_id(self, completion_id: int) -> Optional[StepCompletion]:
        """Get completion by ID"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[StepCompletion]:
        """Get all completions"""
        pass
    
    @abstractmethod
    async def update(self, completion: StepCompletion) -> StepCompletion:
        """Update an existing completion"""
        pass
    
    @abstractmethod
    async def delete(self, completion_id: int) -> bool:
        """Delete a completion"""
        pass
    
    @abstractmethod
    async def get_by_execution(self, execution_id: int) -> List[StepCompletion]:
        """Get all step completions for an execution (ordered by created_at)"""
        pass
    
    @abstractmethod
    async def get_by_step(self, step_id: int) -> List[StepCompletion]:
        """Get all completions for a specific step across all executions"""
        pass
    
    @abstractmethod
    async def get_by_execution_and_step(
        self, execution_id: int, step_id: int
    ) -> List[StepCompletion]:
        """Get all completions for a step in a specific execution"""
        pass
    
    @abstractmethod
    async def record_completion(
        self,
        execution_id: int,
        step_id: int,
        completed_at: datetime,
        notes: Optional[str] = None,
        verified_by_user_id: Optional[int] = None
    ) -> StepCompletion:
        """Record a step completion"""
        pass
    
    @abstractmethod
    async def record_skip(
        self,
        execution_id: int,
        step_id: int,
        skip_reason: str,
        skip_notes: Optional[str] = None,
        verified_by_user_id: Optional[int] = None
    ) -> StepCompletion:
        """Record a skipped step"""
        pass
