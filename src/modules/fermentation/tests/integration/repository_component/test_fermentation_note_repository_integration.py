"""
Integration tests for FermentationNoteRepository.

Tests repository with real SQLite database to verify multi-tenant security,
soft delete behavior, and data persistence.
"""

import pytest
import pytest_asyncio
from datetime import datetime
from uuid import uuid4

from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
    FermentationNoteCreate,
    FermentationNoteUpdate,
)
from src.modules.fermentation.src.repository_component.errors import EntityNotFoundError

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def test_winery_id():
    """Return a test winery ID."""
    return 100


@pytest.fixture
def test_user_id():
    """Return a test user ID."""
    return 5


@pytest_asyncio.fixture
async def test_fermentation(test_models, db_session, test_winery_id, test_user_id):
    """Create a test fermentation."""
    Fermentation = test_models['Fermentation']
    fermentation = Fermentation(
        winery_id=test_winery_id,
        fermented_by_user_id=test_user_id,
        vintage_year=2024,
        yeast_strain="Test Yeast",
        vessel_code=f"VESSEL-{uuid4().hex[:8]}",
        input_mass_kg=1000.0,
        initial_sugar_brix=22.5,
        initial_density=1.090,
        status="ACTIVE",
        start_date=datetime.utcnow(),
        is_deleted=False,
    )
    db_session.add(fermentation)
    await db_session.flush()  # Flush to get ID without committing transaction
    return fermentation


@pytest_asyncio.fixture
async def other_winery_fermentation(test_models, db_session):
    """Create fermentation for a different winery."""
    Fermentation = test_models['Fermentation']
    fermentation = Fermentation(
        winery_id=999,
        fermented_by_user_id=99,
        vintage_year=2024,
        yeast_strain="Other Yeast",
        vessel_code=f"OTHER-{uuid4().hex[:8]}",
        input_mass_kg=500.0,
        initial_sugar_brix=20.0,
        initial_density=1.080,
        status="ACTIVE",
        start_date=datetime.utcnow(),
        is_deleted=False,
    )
    db_session.add(fermentation)
    await db_session.flush()  # Flush to get ID without committing transaction
    return fermentation


class TestCreate:
    """Integration tests for creating fermentation notes."""

    @pytest.mark.asyncio
    async def test_create_success(
        self, repository, test_fermentation, test_winery_id, test_user_id
    ):
        """Test creating a note for valid fermentation."""
        # Arrange
        create_data = FermentationNoteCreate(
            note_text="Fermentation progressing well",
            action_taken="Monitored temperature",
            created_by_user_id=test_user_id,
        )
        
        # Act
        result = await repository.create(
            test_fermentation.id, test_winery_id, create_data
        )
        
        # Assert
        assert result.id is not None
        assert result.fermentation_id == test_fermentation.id
        assert result.note_text == "Fermentation progressing well"
        assert result.action_taken == "Monitored temperature"
        assert result.created_by_user_id == test_user_id
        assert result.is_deleted is False
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_create_fermentation_not_found(
        self, repository, test_winery_id, test_user_id
    ):
        """Test creating note for non-existent fermentation."""
        # Arrange
        create_data = FermentationNoteCreate(
            note_text="Test note",
            action_taken="Test action",
            created_by_user_id=test_user_id,
        )
        
        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await repository.create(99999, test_winery_id, create_data)
        
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_wrong_winery(
        self, repository, other_winery_fermentation, test_winery_id, test_user_id
    ):
        """Test creating note for fermentation from different winery."""
        # Arrange
        create_data = FermentationNoteCreate(
            note_text="Test note",
            action_taken="Test action",
            created_by_user_id=test_user_id,
        )
        
        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await repository.create(
                other_winery_fermentation.id, test_winery_id, create_data
            )
        
        assert "does not belong to winery" in str(exc_info.value).lower()


class TestGetById:
    """Integration tests for retrieving notes by ID."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(
        self, repository, test_models, db_session, test_fermentation, test_winery_id, test_user_id
    ):
        """Test retrieving an existing note."""
        # Arrange - create a note
        FermentationNote = test_models['FermentationNote']
        note = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="Test note content",
            action_taken="Test action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        db_session.add(note)
        await db_session.flush()
        
        # Act
        result = await repository.get_by_id(note.id, test_winery_id)
        
        # Assert
        assert result is not None
        assert result.id == note.id
        assert result.note_text == "Test note content"
        assert result.action_taken == "Test action"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, test_winery_id):
        """Test retrieving non-existent note."""
        # Act
        result = await repository.get_by_id(99999, test_winery_id)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_wrong_winery(
        self, repository, test_models, db_session, other_winery_fermentation, test_winery_id, test_user_id
    ):
        """Test retrieving note from different winery returns None."""
        # Arrange - create note for other winery
        FermentationNote = test_models['FermentationNote']
        note = FermentationNote(
            fermentation_id=other_winery_fermentation.id,
            note_text="Other winery note",
            action_taken="Other action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        db_session.add(note)
        await db_session.flush()
        
        # Act - try to retrieve with test_winery_id
        result = await repository.get_by_id(note.id, test_winery_id)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_soft_deleted(
        self, repository, test_models, db_session, test_fermentation, test_winery_id, test_user_id
    ):
        """Test soft deleted notes are not returned."""
        # Arrange - create and soft delete a note
        FermentationNote = test_models['FermentationNote']
        note = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="Deleted note",
            action_taken="Deleted action",
            created_by_user_id=test_user_id,
            is_deleted=True,
        )
        db_session.add(note)
        await db_session.flush()
        
        # Act
        result = await repository.get_by_id(note.id, test_winery_id)
        
        # Assert
        assert result is None


class TestGetByFermentation:
    """Integration tests for retrieving notes by fermentation."""

    @pytest.mark.asyncio
    async def test_get_by_fermentation_success(
        self, repository, test_models, db_session, test_fermentation, test_winery_id, test_user_id
    ):
        """Test retrieving all notes for a fermentation."""
        # Arrange - create multiple notes
        FermentationNote = test_models['FermentationNote']
        note1 = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="First note",
            action_taken="First action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        note2 = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="Second note",
            action_taken="Second action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        db_session.add_all([note1, note2])
        await db_session.flush()
        
        # Act
        result = await repository.get_by_fermentation(
            test_fermentation.id, test_winery_id
        )
        
        # Assert
        assert len(result) >= 2
        assert all(note.fermentation_id == test_fermentation.id for note in result)
        assert all(not note.is_deleted for note in result)

    @pytest.mark.asyncio
    async def test_get_by_fermentation_ordered_by_created_at(
        self, repository, test_models, db_session, test_fermentation, test_winery_id, test_user_id
    ):
        """Test notes are ordered by created_at DESC."""
        # Arrange - create notes with different timestamps
        FermentationNote = test_models['FermentationNote']
        note1 = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="Older note",
            action_taken="Older action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        db_session.add(note1)
        await db_session.flush()
        
        note2 = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="Newer note",
            action_taken="Newer action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        db_session.add(note2)
        await db_session.flush()
        
        # Act
        result = await repository.get_by_fermentation(
            test_fermentation.id, test_winery_id
        )
        
        # Assert
        assert len(result) >= 2
        # Verify ordering (newer first)
        for i in range(len(result) - 1):
            assert result[i].created_at >= result[i + 1].created_at

    @pytest.mark.asyncio
    async def test_get_by_fermentation_empty(self, repository, test_fermentation, test_winery_id):
        """Test retrieving notes for fermentation with no notes."""
        # Note: test_fermentation fixture creates fresh fermentation
        # Act
        result = await repository.get_by_fermentation(
            test_fermentation.id, test_winery_id
        )
        
        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_fermentation_wrong_winery(
        self, repository, test_models, db_session, other_winery_fermentation, test_winery_id, test_user_id
    ):
        """Test retrieving notes for fermentation from different winery."""
        # Arrange - create note for other winery
        FermentationNote = test_models['FermentationNote']
        note = FermentationNote(
            fermentation_id=other_winery_fermentation.id,
            note_text="Other winery note",
            action_taken="Other action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        db_session.add(note)
        await db_session.flush()
        
        # Act - try to retrieve with test_winery_id
        result = await repository.get_by_fermentation(
            other_winery_fermentation.id, test_winery_id
        )
        
        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_fermentation_excludes_deleted(
        self, repository, test_models, db_session, test_fermentation, test_winery_id, test_user_id
    ):
        """Test soft deleted notes are excluded."""
        # Arrange - create active and deleted notes
        FermentationNote = test_models['FermentationNote']
        active_note = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="Active note",
            action_taken="Active action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        deleted_note = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="Deleted note",
            action_taken="Deleted action",
            created_by_user_id=test_user_id,
            is_deleted=True,
        )
        db_session.add_all([active_note, deleted_note])
        await db_session.flush()
        
        # Act
        result = await repository.get_by_fermentation(
            test_fermentation.id, test_winery_id
        )
        
        # Assert
        assert all(not note.is_deleted for note in result)
        assert any(note.note_text == "Active note" for note in result)
        assert not any(note.note_text == "Deleted note" for note in result)


class TestUpdate:
    """Integration tests for updating notes."""

    @pytest.mark.asyncio
    async def test_update_success(
        self, repository, test_models, db_session, test_fermentation, test_winery_id, test_user_id
    ):
        """Test updating an existing note."""
        # Arrange - create a note
        FermentationNote = test_models['FermentationNote']
        note = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="Original note",
            action_taken="Original action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        db_session.add(note)
        await db_session.flush()
        
        update_data = FermentationNoteUpdate(
            note_text="Updated note",
            action_taken="Updated action",
        )
        
        # Act
        result = await repository.update(note.id, test_winery_id, update_data)
        
        # Assert
        assert result is not None
        assert result.id == note.id
        assert result.note_text == "Updated note"
        assert result.action_taken == "Updated action"

    @pytest.mark.asyncio
    async def test_update_partial(
        self, repository, test_models, db_session, test_fermentation, test_winery_id, test_user_id
    ):
        """Test partial update of a note."""
        # Arrange
        FermentationNote = test_models['FermentationNote']
        note = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="Original note",
            action_taken="Original action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        db_session.add(note)
        await db_session.flush()
        
        update_data = FermentationNoteUpdate(note_text="Updated note only")
        
        # Act
        result = await repository.update(note.id, test_winery_id, update_data)
        
        # Assert
        assert result.note_text == "Updated note only"
        assert result.action_taken == "Original action"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_not_found(self, repository, test_winery_id):
        """Test updating non-existent note."""
        # Arrange
        update_data = FermentationNoteUpdate(note_text="Updated")
        
        # Act
        result = await repository.update(99999, test_winery_id, update_data)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_wrong_winery(
        self, repository, test_models, db_session, other_winery_fermentation, test_winery_id, test_user_id
    ):
        """Test updating note from different winery."""
        # Arrange - create note for other winery
        FermentationNote = test_models['FermentationNote']
        note = FermentationNote(
            fermentation_id=other_winery_fermentation.id,
            note_text="Other winery note",
            action_taken="Other action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        db_session.add(note)
        await db_session.flush()
        
        update_data = FermentationNoteUpdate(note_text="Attempted update")
        
        # Act
        result = await repository.update(note.id, test_winery_id, update_data)
        
        # Assert
        assert result is None


class TestDelete:
    """Integration tests for deleting notes."""

    @pytest.mark.asyncio
    async def test_delete_success(
        self, repository, test_models, db_session, test_fermentation, test_winery_id, test_user_id
    ):
        """Test soft deleting a note."""
        # Arrange
        FermentationNote = test_models['FermentationNote']
        note = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="Note to delete",
            action_taken="Action to delete",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        db_session.add(note)
        await db_session.flush()
        
        # Act
        result = await repository.delete(note.id, test_winery_id)
        
        # Assert
        assert result is True
        
        # Verify soft delete
        assert note.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository, test_winery_id):
        """Test deleting non-existent note."""
        # Act
        result = await repository.delete(99999, test_winery_id)
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_wrong_winery(
        self, repository, test_models, db_session, other_winery_fermentation, test_winery_id, test_user_id
    ):
        """Test deleting note from different winery."""
        # Arrange
        FermentationNote = test_models['FermentationNote']
        note = FermentationNote(
            fermentation_id=other_winery_fermentation.id,
            note_text="Other winery note",
            action_taken="Other action",
            created_by_user_id=test_user_id,
            is_deleted=False,
        )
        db_session.add(note)
        await db_session.flush()
        
        # Act
        result = await repository.delete(note.id, test_winery_id)
        
        # Assert
        assert result is False
        
        # Verify not deleted
        assert note.is_deleted is False

    @pytest.mark.asyncio
    async def test_delete_already_deleted(
        self, repository, test_models, db_session, test_fermentation, test_winery_id, test_user_id
    ):
        """Test deleting already soft-deleted note."""
        # Arrange
        FermentationNote = test_models['FermentationNote']
        note = FermentationNote(
            fermentation_id=test_fermentation.id,
            note_text="Already deleted",
            action_taken="Already deleted action",
            created_by_user_id=test_user_id,
            is_deleted=True,
        )
        db_session.add(note)
        await db_session.flush()
        
        # Act
        result = await repository.delete(note.id, test_winery_id)
        
        # Assert
        assert result is False
