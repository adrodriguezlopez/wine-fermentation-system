"""
Unit tests for FermentationNoteRepository.

Tests repository methods with mocked session manager to verify business logic
without database interaction.

MIGRATED: Using ADR-012 shared unit testing infrastructure.
Reduced from ~80 lines of fixture boilerplate to ~10 lines.
"""

import pytest

# Import User first to ensure SQLAlchemy can resolve relationships in BaseSample
from src.shared.auth.domain.entities.user import User  # noqa: F401

from src.shared.testing.unit import (
    MockSessionManagerBuilder,
    create_query_result,
    create_empty_result,
    create_mock_entity,
)
from src.modules.fermentation.src.repository_component.repositories.fermentation_note_repository import (
    FermentationNoteRepository,
)
from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
    FermentationNoteCreate,
    FermentationNoteUpdate,
)
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
from src.modules.fermentation.src.repository_component.errors import EntityNotFoundError


@pytest.fixture
def sample_fermentation():
    """Create a mock fermentation entity using shared factory."""
    return create_mock_entity(
        Fermentation,
        id=1,
        winery_id=100,
        name="Test Fermentation",
        is_deleted=False
    )


@pytest.fixture
def sample_note():
    """Create a mock note entity using shared factory."""
    return create_mock_entity(
        FermentationNote,
        id=1,
        fermentation_id=1,
        note_text="Test note",
        action_taken="Test action",
        created_by_user_id=5,
        is_deleted=False
    )


class TestCreate:
    """Tests for creating fermentation notes."""

    @pytest.mark.asyncio
    async def test_create_success(self, sample_fermentation):
        """Test creating a note when fermentation exists and belongs to winery."""
        # Arrange
        create_data = FermentationNoteCreate(
            note_text="New note",
            action_taken="Action taken",
            created_by_user_id=5,
        )
        
        # Mock fermentation lookup - returns fermentation when queried
        fermentation_result = create_query_result([sample_fermentation])
        
        # Create session manager with configured execute result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(fermentation_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.create(1, 100, create_data)
        
        # Assert
        assert result is not None
        assert result.fermentation_id == 1
        assert result.note_text == "New note"
        assert result.action_taken == "Action taken"
        assert result.created_by_user_id == 5
        assert result.is_deleted == False

    @pytest.mark.asyncio
    async def test_create_fermentation_not_found(self):
        """Test creating note when fermentation doesn't exist."""
        # Arrange
        create_data = FermentationNoteCreate(
            note_text="New note",
            action_taken="Action taken",
            created_by_user_id=5,
        )
        
        # Mock fermentation not found
        empty_result = create_empty_result()
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await repository.create(999, 100, create_data)
        
        assert "not found" in str(exc_info.value).lower()
        assert "999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_wrong_winery(self):
        """Test creating note when fermentation belongs to different winery."""
        # Arrange
        create_data = FermentationNoteCreate(
            note_text="New note",
            action_taken="Action taken",
            created_by_user_id=5,
        )
        
        # Mock fermentation not found (due to winery mismatch)
        empty_result = create_empty_result()
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act & Assert
        with pytest.raises(EntityNotFoundError) as exc_info:
            await repository.create(1, 999, create_data)
        
        assert "not found" in str(exc_info.value).lower()
        assert "does not belong to winery" in str(exc_info.value).lower()


class TestGetById:
    """Tests for retrieving a note by ID."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, sample_note):
        """Test retrieving an existing note."""
        # Arrange
        note_result = create_query_result([sample_note])
        
        # Create session manager with configured execute result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(note_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.get_by_id(1, 100)
        
        # Assert
        assert result == sample_note
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test retrieving non-existent note."""
        # Arrange
        empty_result = create_empty_result()
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.get_by_id(999, 100)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_wrong_winery(self):
        """Test retrieving note from different winery returns None."""
        # Arrange
        empty_result = create_empty_result()
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.get_by_id(1, 999)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_soft_deleted_not_returned(self):
        """Test soft deleted notes are not returned."""
        # Arrange
        empty_result = create_empty_result()
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.get_by_id(1, 100)
        
        # Assert
        assert result is None


class TestGetByFermentation:
    """Tests for retrieving notes by fermentation."""

    @pytest.mark.asyncio
    async def test_get_by_fermentation_success(self, sample_note):
        """Test retrieving notes for a fermentation."""
        # Arrange
        note2 = create_mock_entity(
            FermentationNote,
            id=2,
            fermentation_id=1,
            note_text="Second note",
            action_taken="Second action",
            created_by_user_id=5,
            is_deleted=False
        )
        
        # Mock multiple notes returned
        notes_result = create_query_result([sample_note, note2])
        
        # Create session manager with configured execute result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(notes_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.get_by_fermentation(1, 100)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == sample_note
        assert result[1] == note2

    @pytest.mark.asyncio
    async def test_get_by_fermentation_empty(self):
        """Test retrieving notes for fermentation with no notes."""
        # Arrange
        empty_result = create_query_result([])
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.get_by_fermentation(1, 100)
        
        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_fermentation_wrong_winery(self):
        """Test retrieving notes for fermentation from different winery returns empty."""
        # Arrange
        empty_result = create_query_result([])
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.get_by_fermentation(1, 999)
        
        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_fermentation_excludes_deleted(self, sample_note):
        """Test that soft deleted notes are excluded."""
        # Arrange
        notes_result = create_query_result([sample_note])
        
        # Create session manager with configured execute result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(notes_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.get_by_fermentation(1, 100)
        
        # Assert
        assert len(result) == 1
        assert all(not note.is_deleted for note in result)


class TestUpdate:
    """Tests for updating fermentation notes."""

    @pytest.mark.asyncio
    async def test_update_success(self, sample_note):
        """Test updating an existing note."""
        # Arrange
        update_data = FermentationNoteUpdate(
            note_text="Updated note",
            action_taken="Updated action",
        )
        
        note_result = create_query_result([sample_note])
        
        # Create session manager with configured execute result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(note_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.update(1, 100, update_data)
        
        # Assert
        assert result == sample_note
        assert sample_note.note_text == "Updated note"
        assert sample_note.action_taken == "Updated action"

    @pytest.mark.asyncio
    async def test_update_partial(self, sample_note):
        """Test partial update of a note."""
        # Arrange
        original_action = sample_note.action_taken
        update_data = FermentationNoteUpdate(note_text="Updated note only")
        
        note_result = create_query_result([sample_note])
        
        # Create session manager with configured execute result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(note_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.update(1, 100, update_data)
        
        # Assert
        assert result.note_text == "Updated note only"
        assert result.action_taken == original_action  # Unchanged

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        """Test updating non-existent note."""
        # Arrange
        update_data = FermentationNoteUpdate(note_text="Updated")
        
        empty_result = create_empty_result()
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.update(999, 100, update_data)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_wrong_winery(self):
        """Test updating note from different winery returns None."""
        # Arrange
        update_data = FermentationNoteUpdate(note_text="Updated")
        
        empty_result = create_empty_result()
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.update(1, 999, update_data)
        
        # Assert
        assert result is None


class TestDelete:
    """Tests for deleting (soft) fermentation notes."""

    @pytest.mark.asyncio
    async def test_delete_success(self, sample_note):
        """Test soft deleting an existing note."""
        # Arrange
        note_result = create_query_result([sample_note])
        
        # Create session manager with configured execute result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(note_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.delete(1, 100)
        
        # Assert
        assert result is True
        assert sample_note.is_deleted is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """Test deleting non-existent note."""
        # Arrange
        empty_result = create_empty_result()
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.delete(999, 100)
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_wrong_winery(self):
        """Test deleting note from different winery returns False."""
        # Arrange
        empty_result = create_empty_result()
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.delete(1, 999)
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_already_deleted(self):
        """Test deleting already soft-deleted note returns False."""
        # Arrange
        empty_result = create_empty_result()
        
        # Create session manager with empty result
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(empty_result)
            .build()
        )
        repository = FermentationNoteRepository(session_manager)
        
        # Act
        result = await repository.delete(1, 100)
        
        # Assert
        assert result is False
