"""
Repository Interfaces for Protocol Domain

Defines contracts for protocol data access.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol


class IFermentationProtocolRepository(ABC):
    """Repository interface for FermentationProtocol entity"""
    
    @abstractmethod
    async def create(self, protocol: FermentationProtocol) -> FermentationProtocol:
        """Create and persist a new protocol"""
        pass
    
    @abstractmethod
    async def get_by_id(self, protocol_id: int) -> Optional[FermentationProtocol]:
        """Get protocol by ID"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[FermentationProtocol]:
        """Get all protocols"""
        pass
    
    @abstractmethod
    async def update(self, protocol: FermentationProtocol) -> FermentationProtocol:
        """Update an existing protocol"""
        pass
    
    @abstractmethod
    async def delete(self, protocol_id: int) -> bool:
        """Delete a protocol"""
        pass
    
    @abstractmethod
    async def get_by_winery_varietal_version(
        self, winery_id: int, varietal_code: str, version: str
    ) -> Optional[FermentationProtocol]:
        """Get protocol by unique constraint (winery, varietal, version)"""
        pass
    
    @abstractmethod
    async def get_active_by_winery(self, winery_id: int) -> List[FermentationProtocol]:
        """Get all active protocols for a winery"""
        pass
    
    @abstractmethod
    async def get_by_varietal(self, winery_id: int, varietal_code: str) -> List[FermentationProtocol]:
        """Get all protocol versions for a varietal"""
        pass
