"""
ProtocolStep Repository Implementation

Async repository for ProtocolStep entity persistence.
Uses SQLAlchemy async session for database operations.
"""

from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
from src.modules.fermentation.src.domain.repositories.protocol_step_repository_interface import (
    IProtocolStepRepository
)


class ProtocolStepRepository(IProtocolStepRepository):
    """Repository for ProtocolStep persistence operations"""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with async session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
    
    async def create(self, step: ProtocolStep) -> ProtocolStep:
        """
        Create and persist a new protocol step.
        
        Args:
            step: ProtocolStep entity to create
            
        Returns:
            Created step with ID assigned
            
        Raises:
            IntegrityError: If unique constraint violated (protocol_id, step_order)
        """
        self.session.add(step)
        await self.session.flush()
        return step
    
    async def get_by_id(self, step_id: int) -> Optional[ProtocolStep]:
        """
        Get step by ID.
        
        Args:
            step_id: ID of step to retrieve
            
        Returns:
            Step if found, None otherwise
        """
        stmt = select(ProtocolStep).where(ProtocolStep.id == step_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all(self) -> List[ProtocolStep]:
        """
        Get all protocol steps.
        
        Returns:
            List of all ProtocolStep entities
        """
        stmt = select(ProtocolStep).order_by(
            ProtocolStep.protocol_id,
            ProtocolStep.step_order
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update(self, step: ProtocolStep) -> ProtocolStep:
        """
        Update an existing protocol step.
        
        Args:
            step: ProtocolStep entity with updated values
            
        Returns:
            Updated step
        """
        await self.session.merge(step)
        await self.session.flush()
        return step
    
    async def delete(self, step_id: int) -> bool:
        """
        Delete a protocol step by ID.
        
        Args:
            step_id: ID of step to delete
            
        Returns:
            True if deleted, False if not found
        """
        step = await self.get_by_id(step_id)
        if step is None:
            return False
        
        await self.session.delete(step)
        await self.session.flush()
        return True
    
    async def get_by_protocol(self, protocol_id: int) -> List[ProtocolStep]:
        """
        Get all steps for a protocol, ordered by step_order.
        
        Args:
            protocol_id: ID of protocol
            
        Returns:
            List of ProtocolStep entities for this protocol, ordered by step_order
        """
        stmt = select(ProtocolStep).where(
            ProtocolStep.protocol_id == protocol_id
        ).order_by(ProtocolStep.step_order)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_order(
        self,
        protocol_id: int,
        step_order: int
    ) -> Optional[ProtocolStep]:
        """
        Get a specific step by protocol and order.
        
        Args:
            protocol_id: ID of protocol
            step_order: Order number of step within protocol
            
        Returns:
            Step if found, None otherwise
        """
        stmt = select(ProtocolStep).where(
            (ProtocolStep.protocol_id == protocol_id) &
            (ProtocolStep.step_order == step_order)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def list_by_protocol_paginated(
        self, protocol_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[ProtocolStep], int]:
        """
        Get steps for a protocol with pagination.
        
        Args:
            protocol_id: Protocol ID
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Tuple of (steps list, total count)
        """
        # Get total count
        count_stmt = select(func.count(ProtocolStep.id)).where(
            ProtocolStep.protocol_id == protocol_id
        )
        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalars().first() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        stmt = select(ProtocolStep).where(
            ProtocolStep.protocol_id == protocol_id
        ).order_by(ProtocolStep.step_order).offset(offset).limit(page_size)
        
        result = await self.session.execute(stmt)
        steps = result.scalars().all()
        
        return steps, total_count
