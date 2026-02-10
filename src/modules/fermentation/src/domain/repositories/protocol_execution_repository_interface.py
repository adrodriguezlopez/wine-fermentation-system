"""
Repository Interface for ProtocolExecution
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution


class IProtocolExecutionRepository(ABC):
    """Repository interface for ProtocolExecution entity"""
    
    @abstractmethod
    async def create(self, execution: ProtocolExecution) -> ProtocolExecution:
        """Create and persist a new execution"""
        pass
    
    @abstractmethod
    async def get_by_id(self, execution_id: int) -> Optional[ProtocolExecution]:
        """Get execution by ID"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[ProtocolExecution]:
        """Get all executions"""
        pass
    
    @abstractmethod
    async def update(self, execution: ProtocolExecution) -> ProtocolExecution:
        """Update an existing execution"""
        pass
    
    @abstractmethod
    async def delete(self, execution_id: int) -> bool:
        """Delete an execution"""
        pass
    
    @abstractmethod
    async def get_by_fermentation(self, fermentation_id: int) -> Optional[ProtocolExecution]:
        """Get execution for a fermentation (1:1 relationship)"""
        pass
    
    @abstractmethod
    async def get_by_status(self, winery_id: int, status: str) -> List[ProtocolExecution]:
        """Get all executions with a specific status for a winery"""
        pass
    
    @abstractmethod
    async def get_active_by_winery(self, winery_id: int) -> List[ProtocolExecution]:
        """Get all active protocol executions for a winery"""
        pass
