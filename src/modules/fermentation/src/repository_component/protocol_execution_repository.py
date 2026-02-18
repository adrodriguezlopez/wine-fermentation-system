"""
ProtocolExecution Repository Implementation

Async repository for ProtocolExecution entity persistence.
Uses SQLAlchemy async session for database operations.
"""

from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
from src.modules.fermentation.src.domain.enums.step_type import ProtocolExecutionStatus
from src.modules.fermentation.src.domain.repositories.protocol_execution_repository_interface import (
    IProtocolExecutionRepository
)


class ProtocolExecutionRepository(IProtocolExecutionRepository):
    """Repository for ProtocolExecution persistence operations"""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with async session.
        
        Args:
            session: SQLAlchemy async session for database operations
        """
        self.session = session
    
    async def create(self, execution: ProtocolExecution) -> ProtocolExecution:
        """
        Create and persist a new protocol execution.
        
        Args:
            execution: ProtocolExecution entity to create
            
        Returns:
            Created execution with ID assigned
            
        Raises:
            IntegrityError: If unique constraint violated (fermentation_id)
        """
        self.session.add(execution)
        await self.session.flush()
        return execution
    
    async def get_by_id(self, execution_id: int) -> Optional[ProtocolExecution]:
        """
        Get execution by ID.
        
        Args:
            execution_id: ID of execution to retrieve
            
        Returns:
            Execution if found, None otherwise
        """
        stmt = select(ProtocolExecution).where(ProtocolExecution.id == execution_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_all(self) -> List[ProtocolExecution]:
        """
        Get all protocol executions.
        
        Returns:
            List of all ProtocolExecution entities
        """
        stmt = select(ProtocolExecution).order_by(ProtocolExecution.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update(self, execution: ProtocolExecution) -> ProtocolExecution:
        """
        Update an existing protocol execution.
        
        Args:
            execution: ProtocolExecution entity with updated values
            
        Returns:
            Updated execution
        """
        await self.session.merge(execution)
        await self.session.flush()
        return execution
    
    async def delete(self, execution_id: int) -> bool:
        """
        Delete a protocol execution by ID.
        
        Args:
            execution_id: ID of execution to delete
            
        Returns:
            True if deleted, False if not found
        """
        execution = await self.get_by_id(execution_id)
        if execution is None:
            return False
        
        await self.session.delete(execution)
        await self.session.flush()
        return True
    
    async def get_by_fermentation(self, fermentation_id: int) -> Optional[ProtocolExecution]:
        """
        Get execution for a specific fermentation (unique, one-to-one).
        
        Args:
            fermentation_id: ID of fermentation
            
        Returns:
            Execution if found, None otherwise
        """
        stmt = select(ProtocolExecution).where(
            ProtocolExecution.fermentation_id == fermentation_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_by_status(
        self,
        status: ProtocolExecutionStatus
    ) -> List[ProtocolExecution]:
        """
        Get all executions with a specific status.
        
        Args:
            status: ProtocolExecutionStatus enum value to filter by
            
        Returns:
            List of ProtocolExecution entities with specified status
        """
        stmt = select(ProtocolExecution).where(
            ProtocolExecution.status == status
        ).order_by(ProtocolExecution.id)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_active_by_winery(self, winery_id: int) -> List[ProtocolExecution]:
        """
        Get all active executions for a winery.
        
        Active = status is ACTIVE or PAUSED (not NOT_STARTED, COMPLETED, or ABANDONED).
        
        Args:
            winery_id: Winery ID
            
        Returns:
            List of active ProtocolExecution entities for winery
        """
        stmt = select(ProtocolExecution).where(
            (ProtocolExecution.winery_id == winery_id) &
            (ProtocolExecution.status.in_([
                ProtocolExecutionStatus.ACTIVE,
                ProtocolExecutionStatus.PAUSED
            ]))
        ).order_by(ProtocolExecution.id)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def list_by_winery_paginated(
        self, winery_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[ProtocolExecution], int]:
        """
        Get executions for a winery with pagination.
        
        Args:
            winery_id: Winery ID
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Tuple of (executions list, total count)
        """
        # Get total count
        count_stmt = select(func.count(ProtocolExecution.id)).where(
            ProtocolExecution.winery_id == winery_id
        )
        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalars().first() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        stmt = select(ProtocolExecution).where(
            ProtocolExecution.winery_id == winery_id
        ).order_by(ProtocolExecution.id.desc()).offset(offset).limit(page_size)
        
        result = await self.session.execute(stmt)
        executions = result.scalars().all()
        
        return executions, total_count
