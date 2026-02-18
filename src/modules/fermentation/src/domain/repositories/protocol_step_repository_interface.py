"""
Repository Interface for ProtocolStep
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep


class IProtocolStepRepository(ABC):
    """Repository interface for ProtocolStep entity"""
    
    @abstractmethod
    async def create(self, step: ProtocolStep) -> ProtocolStep:
        """Create and persist a new step"""
        pass
    
    @abstractmethod
    async def get_by_id(self, step_id: int) -> Optional[ProtocolStep]:
        """Get step by ID"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[ProtocolStep]:
        """Get all steps"""
        pass
    
    @abstractmethod
    async def update(self, step: ProtocolStep) -> ProtocolStep:
        """Update an existing step"""
        pass
    
    @abstractmethod
    async def delete(self, step_id: int) -> bool:
        """Delete a step"""
        pass
    
    @abstractmethod
    async def get_by_protocol(self, protocol_id: int) -> List[ProtocolStep]:
        """Get all steps for a protocol (ordered by step_order)"""
        pass
    
    @abstractmethod
    async def get_by_order(self, protocol_id: int, step_order: int) -> Optional[ProtocolStep]:
        """Get step by protocol and order"""
        pass
    
    @abstractmethod
    async def list_by_protocol_paginated(
        self, protocol_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[ProtocolStep], int]:
        """
        Get steps for a protocol with pagination.
        
        Returns:
            Tuple of (steps list, total count)
        """
        pass
