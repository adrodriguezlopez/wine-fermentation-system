"""
FermentationProtocol Repository Implementation

Async repository for FermentationProtocol entity persistence.
Uses SQLAlchemy async session for database operations.
"""

from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
from src.modules.fermentation.src.domain.repositories.fermentation_protocol_repository_interface import (
    IFermentationProtocolRepository
)


class FermentationProtocolRepository(IFermentationProtocolRepository):
    """Repository for FermentationProtocol persistence operations"""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with async session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
    
    async def create(self, protocol: FermentationProtocol) -> FermentationProtocol:
        """
        Create and persist a new protocol.
        
        Args:
            protocol: FermentationProtocol entity to create
            
        Returns:
            Created protocol with ID assigned
            
        Raises:
            IntegrityError: If unique constraint violated (winery, varietal, version)
        """
        self.session.add(protocol)
        await self.session.flush()
        return protocol
    
    async def get_by_id(self, protocol_id: int) -> Optional[FermentationProtocol]:
        """
        Get protocol by ID.
        
        Args:
            protocol_id: ID of protocol to retrieve
            
        Returns:
            Protocol if found, None otherwise
        """
        stmt = select(FermentationProtocol).where(FermentationProtocol.id == protocol_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all(self) -> List[FermentationProtocol]:
        """
        Get all protocols.
        
        Returns:
            List of all FermentationProtocol entities
        """
        stmt = select(FermentationProtocol).order_by(FermentationProtocol.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update(self, protocol: FermentationProtocol) -> FermentationProtocol:
        """
        Update an existing protocol.
        
        Args:
            protocol: FermentationProtocol entity with updated values
            
        Returns:
            Updated protocol
            
        Raises:
            IntegrityError: If unique constraint violated
        """
        await self.session.merge(protocol)
        await self.session.flush()
        return protocol
    
    async def delete(self, protocol_id: int) -> bool:
        """
        Delete a protocol by ID.
        
        Args:
            protocol_id: ID of protocol to delete
            
        Returns:
            True if deleted, False if not found
        """
        protocol = await self.get_by_id(protocol_id)
        if protocol is None:
            return False
        
        await self.session.delete(protocol)
        await self.session.flush()
        return True
    
    async def get_by_winery_varietal_version(
        self,
        winery_id: int,
        varietal_code: str,
        version: str
    ) -> Optional[FermentationProtocol]:
        """
        Get protocol by unique constraint (winery, varietal, version).
        
        Args:
            winery_id: Winery ID
            varietal_code: Varietal code (e.g., "PN" for Pinot Noir)
            version: Protocol version (e.g., "1.0")
            
        Returns:
            Protocol if found, None otherwise
        """
        stmt = select(FermentationProtocol).where(
            (FermentationProtocol.winery_id == winery_id) &
            (FermentationProtocol.varietal_code == varietal_code) &
            (FermentationProtocol.version == version)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_active_by_winery(self, winery_id: int) -> List[FermentationProtocol]:
        """
        Get all active protocols for a winery.
        
        Args:
            winery_id: Winery ID
            
        Returns:
            List of active FermentationProtocol entities for winery
        """
        stmt = select(FermentationProtocol).where(
            (FermentationProtocol.winery_id == winery_id) &
            (FermentationProtocol.is_active is True)
        ).order_by(FermentationProtocol.varietal_name)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_varietal(
        self,
        winery_id: int,
        varietal_code: str
    ) -> List[FermentationProtocol]:
        """
        Get all protocol versions for a varietal.
        
        Args:
            winery_id: Winery ID
            varietal_code: Varietal code (e.g., "PN")
            
        Returns:
            List of all protocol versions for this varietal
        """
        stmt = select(FermentationProtocol).where(
            (FermentationProtocol.winery_id == winery_id) &
            (FermentationProtocol.varietal_code == varietal_code)
        ).order_by(FermentationProtocol.version.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def list_by_winery_paginated(
        self, winery_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[FermentationProtocol], int]:
        """
        Get protocols for a winery with pagination.
        
        Args:
            winery_id: Winery ID
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Tuple of (protocols list, total count)
        """
        # Get total count
        count_stmt = select(func.count(FermentationProtocol.id)).where(
            FermentationProtocol.winery_id == winery_id
        )
        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalars().first() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        stmt = select(FermentationProtocol).where(
            FermentationProtocol.winery_id == winery_id
        ).order_by(
            FermentationProtocol.varietal_name,
            FermentationProtocol.version.desc()
        ).offset(offset).limit(page_size)
        
        result = await self.session.execute(stmt)
        protocols = result.scalars().all()
        
        return protocols, total_count
    
    async def list_active_by_winery_paginated(
        self, winery_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[FermentationProtocol], int]:
        """
        Get active protocols for a winery with pagination.
        
        Args:
            winery_id: Winery ID
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Tuple of (protocols list, total count)
        """
        # Get total count
        count_stmt = select(func.count(FermentationProtocol.id)).where(
            (FermentationProtocol.winery_id == winery_id) &
            (FermentationProtocol.is_active is True)
        )
        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalars().first() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        stmt = select(FermentationProtocol).where(
            (FermentationProtocol.winery_id == winery_id) &
            (FermentationProtocol.is_active is True)
        ).order_by(
            FermentationProtocol.varietal_name
        ).offset(offset).limit(page_size)
        
        result = await self.session.execute(stmt)
        protocols = result.scalars().all()
        
        return protocols, total_count
