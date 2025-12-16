"""
FermentationNoteRepository - Implementation of IFermentationNoteRepository interface.

Provides data access for fermentation notes with multi-tenant security through
JOIN with fermentation table to ensure notes belong to the specified winery.
"""

from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
    FermentationNoteCreate,
    FermentationNoteUpdate,
)
from src.modules.fermentation.src.domain.repositories.fermentation_note_repository_interface import (
    IFermentationNoteRepository,
)
from src.shared.infra.repository.base_repository import BaseRepository
from src.modules.fermentation.src.repository_component.errors import EntityNotFoundError


class FermentationNoteRepository(BaseRepository, IFermentationNoteRepository):
    """
    Repository for managing fermentation notes with multi-tenant security.
    
    All operations validate that the fermentation belongs to the specified winery
    through JOIN queries with the fermentation table.
    """

    async def create(
        self,
        fermentation_id: int,
        winery_id: int,
        data: FermentationNoteCreate,
    ) -> FermentationNote:
        """
        Create a new fermentation note.
        
        Args:
            fermentation_id: ID of the fermentation to add note to
            winery_id: ID of the winery (for multi-tenant validation)
            data: DTO containing note data
            
        Returns:
            The created FermentationNote entity
            
        Raises:
            EntityNotFoundError: If fermentation doesn't exist or doesn't belong to winery
        """
        session_cm = await self.get_session()
        async with session_cm as session:
            # Verify fermentation exists and belongs to winery
            fermentation_query = select(Fermentation).where(
                and_(
                    Fermentation.id == fermentation_id,
                    Fermentation.winery_id == winery_id,
                    Fermentation.is_deleted == False,
                )
            )
            result = await session.execute(fermentation_query)
            fermentation = result.scalar_one_or_none()
            
            if not fermentation:
                raise EntityNotFoundError(
                    f"Fermentation with id {fermentation_id} not found or does not belong to winery {winery_id}"
                )
            
            # Create the note
            note = FermentationNote(
                fermentation_id=fermentation_id,
                note_text=data.note_text,
                action_taken=data.action_taken,
                created_by_user_id=data.created_by_user_id,
                is_deleted=False,
            )
            
            session.add(note)
            await session.flush()
            await session.refresh(note)
            
            return note

    async def get_by_id(
        self,
        note_id: int,
        winery_id: int,
    ) -> Optional[FermentationNote]:
        """
        Retrieve a fermentation note by ID with multi-tenant validation.
        
        Args:
            note_id: ID of the note to retrieve
            winery_id: ID of the winery (for multi-tenant validation)
            
        Returns:
            The FermentationNote entity if found and belongs to winery, None otherwise
        """
        session_cm = await self.get_session()
        async with session_cm as session:
            query = (
                select(FermentationNote)
                .join(Fermentation)
                .where(
                    and_(
                        FermentationNote.id == note_id,
                        Fermentation.winery_id == winery_id,
                        FermentationNote.is_deleted == False,
                    )
                )
            )
            
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def get_by_fermentation(
        self,
        fermentation_id: int,
        winery_id: int,
    ) -> List[FermentationNote]:
        """
        Retrieve all notes for a fermentation with multi-tenant validation.
        
        Args:
            fermentation_id: ID of the fermentation
            winery_id: ID of the winery (for multi-tenant validation)
            
        Returns:
            List of FermentationNote entities, ordered by created_at DESC
            Returns empty list if fermentation doesn't belong to winery
        """
        session_cm = await self.get_session()
        async with session_cm as session:
            query = (
                select(FermentationNote)
                .join(Fermentation)
                .where(
                    and_(
                        FermentationNote.fermentation_id == fermentation_id,
                        Fermentation.winery_id == winery_id,
                        FermentationNote.is_deleted == False,
                    )
                )
                .order_by(FermentationNote.created_at.desc())
            )
            
            result = await session.execute(query)
            return list(result.scalars().all())

    async def update(
        self,
        note_id: int,
        winery_id: int,
        data: FermentationNoteUpdate,
    ) -> Optional[FermentationNote]:
        """
        Update an existing fermentation note with multi-tenant validation.
        
        Args:
            note_id: ID of the note to update
            winery_id: ID of the winery (for multi-tenant validation)
            data: DTO containing fields to update (partial updates supported)
            
        Returns:
            The updated FermentationNote entity if found, None otherwise
        """
        session_cm = await self.get_session()
        async with session_cm as session:
            # Retrieve note with multi-tenant validation
            query = (
                select(FermentationNote)
                .join(Fermentation)
                .where(
                    and_(
                        FermentationNote.id == note_id,
                        Fermentation.winery_id == winery_id,
                        FermentationNote.is_deleted == False,
                    )
                )
            )
            
            result = await session.execute(query)
            note = result.scalar_one_or_none()
            
            if not note:
                return None
            
            # Apply updates
            if data.note_text is not None:
                note.note_text = data.note_text
            if data.action_taken is not None:
                note.action_taken = data.action_taken
            
            await session.flush()
            await session.refresh(note)
            
            return note

    async def delete(
        self,
        note_id: int,
        winery_id: int,
    ) -> bool:
        """
        Soft delete a fermentation note with multi-tenant validation.
        
        Args:
            note_id: ID of the note to delete
            winery_id: ID of the winery (for multi-tenant validation)
            
        Returns:
            True if note was deleted, False if not found or doesn't belong to winery
        """
        session_cm = await self.get_session()
        async with session_cm as session:
            # Retrieve note with multi-tenant validation
            query = (
                select(FermentationNote)
                .join(Fermentation)
                .where(
                    and_(
                        FermentationNote.id == note_id,
                        Fermentation.winery_id == winery_id,
                        FermentationNote.is_deleted == False,
                    )
                )
            )
            
            result = await session.execute(query)
            note = result.scalar_one_or_none()
            
            if not note:
                return False
            
            # Soft delete
            note.is_deleted = True
            await session.flush()
            
            return True
