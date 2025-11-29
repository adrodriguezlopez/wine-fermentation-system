"""Unit tests for VineyardRepository."""
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from src.modules.fruit_origin.src.repository_component.repositories.vineyard_repository import (
    VineyardRepository,
)
from src.modules.fruit_origin.src.domain.dtos.vineyard_dtos import (
    VineyardCreate,
    VineyardUpdate,
)
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.repository_component.errors import (
    RepositoryError,
    DuplicateCodeError,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager that returns a mock session."""
    manager = Mock()
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.execute = AsyncMock()
    
    # Create a proper async context manager mock
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context.__aexit__ = AsyncMock(return_value=None)
    
    # Make get_session return the context manager
    manager.get_session = Mock(return_value=mock_context)
    manager.close = AsyncMock()
    return manager, mock_session


@pytest.fixture
def repository(mock_session_manager):
    """Create VineyardRepository with mocked session manager."""
    manager, _ = mock_session_manager
    return VineyardRepository(manager)


@pytest.fixture
def sample_vineyard_create():
    """Sample VineyardCreate DTO."""
    return VineyardCreate(
        code="VIN001",
        name="North Vineyard",
        notes="Premium location",
    )


@pytest.fixture
def sample_vineyard():
    """Sample Vineyard entity."""
    vineyard = Vineyard(
        id=1,
        winery_id=10,
        code="VIN001",
        name="North Vineyard",
        notes="Premium location",
        is_deleted=False,
    )
    vineyard.created_at = datetime(2024, 1, 1, 12, 0, 0)
    vineyard.updated_at = datetime(2024, 1, 1, 12, 0, 0)
    return vineyard


# ============================================================================
# Tests: create()
# ============================================================================


@pytest.mark.asyncio
async def test_create_success(repository, mock_session_manager, sample_vineyard_create):
    """Test successful vineyard creation."""
    manager, mock_session = mock_session_manager
    # Arrange
    winery_id = 10

    # Act
    result = await repository.create(winery_id, sample_vineyard_create)

    # Assert
    assert mock_session.add.called
    added_vineyard = mock_session.add.call_args[0][0]
    assert isinstance(added_vineyard, Vineyard)
    assert added_vineyard.winery_id == winery_id
    assert added_vineyard.code == "VIN001"
    assert added_vineyard.name == "North Vineyard"
    assert added_vineyard.notes == "Premium location"
    assert added_vineyard.is_deleted is False
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_with_minimal_data(repository, mock_session_manager):
    """Test creating vineyard with only required fields."""
    manager, mock_session = mock_session_manager
    # Arrange
    data = VineyardCreate(code="VIN002", name="South Vineyard")

    # Act
    result = await repository.create(20, data)

    # Assert
    added_vineyard = mock_session.add.call_args[0][0]
    assert added_vineyard.code == "VIN002"
    assert added_vineyard.name == "South Vineyard"
    assert added_vineyard.notes is None


@pytest.mark.asyncio
async def test_create_duplicate_code_raises_error(
    repository, mock_session_manager, sample_vineyard_create
):
    """Test creating vineyard with duplicate code raises DuplicateCodeError."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_session.flush.side_effect = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    mock_session.flush.side_effect.args = (
        "duplicate key value violates unique constraint uq_vineyards__code__winery_id",
    )

    # Act & Assert
    with pytest.raises(DuplicateCodeError) as exc_info:
        await repository.create(10, sample_vineyard_create)

    assert "VIN001" in str(exc_info.value)
    assert "winery 10" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_integrity_error_other_constraint(
    repository, mock_session_manager, sample_vineyard_create
):
    """Test creating vineyard with other integrity error raises RepositoryError."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_session.flush.side_effect = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    mock_session.flush.side_effect.args = ("some other constraint violation",)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.create(10, sample_vineyard_create)

    assert "Failed to create vineyard" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_generic_exception_raises_repository_error(
    repository, mock_session_manager, sample_vineyard_create
):
    """Test generic exception during create raises RepositoryError."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_session.flush.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.create(10, sample_vineyard_create)

    assert "Failed to create vineyard" in str(exc_info.value)


# ============================================================================
# Tests: get_by_id()
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_id_found(repository, mock_session_manager, sample_vineyard):
    """Test getting vineyard by ID returns vineyard."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_id(1, 10)

    # Assert
    assert result == sample_vineyard
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository, mock_session_manager):
    """Test getting non-existent vineyard returns None."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_id(999, 10)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_wrong_winery(repository, mock_session_manager):
    """Test getting vineyard with wrong winery_id returns None."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_id(1, 999)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_soft_deleted(repository, mock_session_manager):
    """Test getting soft-deleted vineyard returns None."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_id(1, 10)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_exception_raises_repository_error(repository, mock_session_manager):
    """Test exception during get_by_id raises RepositoryError."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_session.execute.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_id(1, 10)

    assert "Failed to get vineyard" in str(exc_info.value)


# ============================================================================
# Tests: get_by_winery()
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_winery_returns_multiple(repository, mock_session_manager):
    """Test getting all vineyards for a winery."""
    manager, mock_session = mock_session_manager
    # Arrange
    vineyard1 = Vineyard(
        id=1, winery_id=10, code="VIN001", name="North", is_deleted=False
    )
    vineyard2 = Vineyard(
        id=2, winery_id=10, code="VIN002", name="South", is_deleted=False
    )

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [vineyard1, vineyard2]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_winery(10)

    # Assert
    assert len(result) == 2
    assert result[0] == vineyard1
    assert result[1] == vineyard2


@pytest.mark.asyncio
async def test_get_by_winery_returns_empty_list(repository, mock_session_manager):
    """Test getting vineyards for winery with no vineyards."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_winery(999)

    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_get_by_winery_excludes_soft_deleted(repository, mock_session_manager):
    """Test get_by_winery excludes soft-deleted vineyards."""
    manager, mock_session = mock_session_manager
    # Arrange
    vineyard1 = Vineyard(
        id=1, winery_id=10, code="VIN001", name="North", is_deleted=False
    )

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [vineyard1]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_winery(10)

    # Assert
    assert len(result) == 1
    assert result[0].is_deleted is False


@pytest.mark.asyncio
async def test_get_by_winery_exception_raises_repository_error(
    repository, mock_session_manager
):
    """Test exception during get_by_winery raises RepositoryError."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_session.execute.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_winery(10)

    assert "Failed to get vineyards" in str(exc_info.value)


# ============================================================================
# Tests: get_by_code()
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_code_found(repository, mock_session_manager, sample_vineyard):
    """Test getting vineyard by code returns vineyard."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_code("VIN001", 10)

    # Assert
    assert result == sample_vineyard


@pytest.mark.asyncio
async def test_get_by_code_not_found(repository, mock_session_manager):
    """Test getting non-existent code returns None."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_code("NONEXISTENT", 10)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_wrong_winery(repository, mock_session_manager):
    """Test getting code with wrong winery returns None."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_code("VIN001", 999)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_soft_deleted(repository, mock_session_manager):
    """Test getting soft-deleted vineyard by code returns None."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_code("VIN001", 10)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_exception_raises_repository_error(repository, mock_session_manager):
    """Test exception during get_by_code raises RepositoryError."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_session.execute.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_code("VIN001", 10)

    assert "Failed to get vineyard by code" in str(exc_info.value)


# ============================================================================
# Tests: update()
# ============================================================================


@pytest.mark.asyncio
async def test_update_all_fields(repository, mock_session_manager, sample_vineyard):
    """Test updating all vineyard fields."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = mock_result

    update_data = VineyardUpdate(
        code="VIN001-NEW",
        name="Updated Vineyard",
        notes="Updated notes",
    )

    # Act
    result = await repository.update(1, 10, update_data)

    # Assert
    assert result.code == "VIN001-NEW"
    assert result.name == "Updated Vineyard"
    assert result.notes == "Updated notes"
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_partial_fields(repository, mock_session_manager, sample_vineyard):
    """Test updating only some fields."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = mock_result

    update_data = VineyardUpdate(name="Partially Updated")

    # Act
    result = await repository.update(1, 10, update_data)

    # Assert
    assert result.code == "VIN001"  # Unchanged
    assert result.name == "Partially Updated"
    assert result.notes == "Premium location"  # Unchanged


@pytest.mark.asyncio
async def test_update_not_found(repository, mock_session_manager):
    """Test updating non-existent vineyard returns None."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    update_data = VineyardUpdate(name="Updated")

    # Act
    result = await repository.update(999, 10, update_data)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_code_raises_error(
    repository, mock_session_manager, sample_vineyard
):
    """Test updating to duplicate code raises DuplicateCodeError."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = mock_result

    mock_session.flush.side_effect = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    mock_session.flush.side_effect.args = (
        "duplicate key value violates unique constraint uq_vineyards__code__winery_id",
    )

    update_data = VineyardUpdate(code="DUPLICATE")

    # Act & Assert
    with pytest.raises(DuplicateCodeError) as exc_info:
        await repository.update(1, 10, update_data)

    assert "DUPLICATE" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_generic_exception_raises_repository_error(
    repository, mock_session_manager, sample_vineyard
):
    """Test generic exception during update raises RepositoryError."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = mock_result

    mock_session.flush.side_effect = Exception("Database error")

    update_data = VineyardUpdate(name="Updated")

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.update(1, 10, update_data)

    assert "Failed to update vineyard" in str(exc_info.value)


# ============================================================================
# Tests: delete()
# ============================================================================


@pytest.mark.asyncio
async def test_delete_success(repository, mock_session_manager, sample_vineyard):
    """Test successful vineyard deletion."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.delete(1, 10)

    # Assert
    assert result is True
    assert sample_vineyard.is_deleted is True
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(repository, mock_session_manager):
    """Test deleting non-existent vineyard returns False."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.delete(999, 10)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_idempotent(repository, mock_session_manager, sample_vineyard):
    """Test deleting already deleted vineyard is idempotent."""
    manager, mock_session = mock_session_manager
    # Arrange
    sample_vineyard.is_deleted = True
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = mock_result

    # Act
    result = await repository.delete(1, 10)

    # Assert
    assert result is True
    assert sample_vineyard.is_deleted is True


@pytest.mark.asyncio
async def test_delete_exception_raises_repository_error(
    repository, mock_session_manager, sample_vineyard
):
    """Test exception during delete raises RepositoryError."""
    manager, mock_session = mock_session_manager
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = mock_result

    mock_session.flush.side_effect = Exception("Database error")

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.delete(1, 10)

    assert "Failed to delete vineyard" in str(exc_info.value)
