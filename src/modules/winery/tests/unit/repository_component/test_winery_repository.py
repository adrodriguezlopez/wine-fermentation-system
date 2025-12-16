"""Unit tests for WineryRepository."""
import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from src.modules.winery.src.repository_component.repositories.winery_repository import (
    WineryRepository,
    RepositoryError,
    DuplicateNameError,
)
from src.modules.winery.src.domain.dtos.winery_dtos import (
    WineryCreate,
    WineryUpdate,
)
from src.modules.winery.src.domain.entities.winery import Winery

# ADR-012: Import shared testing utilities
from src.shared.testing.unit import (
    MockSessionManagerBuilder,
    create_query_result,
    create_empty_result,
    create_mock_entity,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_winery_create():
    """Sample WineryCreate DTO."""
    return WineryCreate(
        name="Sunset Vineyards",
        region="Napa Valley",
    )


@pytest.fixture
def sample_winery():
    """Sample Winery entity."""
    winery = create_mock_entity(
        Winery,
        id=1,
        name="Sunset Vineyards",
        region="Napa Valley",
        is_deleted=False,
    )
    winery.created_at = datetime(2024, 1, 1, 12, 0, 0)
    winery.updated_at = datetime(2024, 1, 1, 12, 0, 0)
    return winery


# ============================================================================
# Tests: create()
# ============================================================================


@pytest.mark.asyncio
async def test_create_success(sample_winery_create):
    """Test successful winery creation."""
    session_manager = MockSessionManagerBuilder().build()
    repository = WineryRepository(session_manager)
    
    # Act
    result = await repository.create(sample_winery_create)


@pytest.mark.asyncio
async def test_create_with_minimal_data():
    """Test creating winery with only required fields."""
    data = WineryCreate(name="Mountain Winery")
    session_manager = MockSessionManagerBuilder().build()
    repository = WineryRepository(session_manager)

    # Act
    result = await repository.create(data)


@pytest.mark.asyncio
async def test_create_duplicate_name_raises_error(sample_winery_create):
    """Test creating winery with duplicate name raises DuplicateNameError."""
    integrity_error = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    integrity_error.args = (
        "duplicate key value violates unique constraint uq_wineries__name",
    )
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_flush_side_effect(integrity_error)
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act & Assert
    with pytest.raises(DuplicateNameError) as exc_info:
        await repository.create(sample_winery_create)

    assert "Sunset Vineyards" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_integrity_error_other_constraint(sample_winery_create):
    """Test IntegrityError from non-duplicate-name constraint raises RepositoryError."""
    integrity_error = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    integrity_error.args = ("some other constraint violation",)
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_flush_side_effect(integrity_error)
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.create(sample_winery_create)

    assert "Failed to create winery" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_generic_exception(sample_winery_create):
    """Test generic exception during create raises RepositoryError."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_flush_side_effect(Exception("Database connection lost"))
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.create(sample_winery_create)

    assert "Failed to create winery" in str(exc_info.value)


# ============================================================================
# Tests: get_by_id()
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_id_found(sample_winery):
    """Test getting winery by ID when it exists."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_query_result([sample_winery]))
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act
    result = await repository.get_by_id(1)

    # Assert
    assert result == sample_winery


@pytest.mark.asyncio
async def test_get_by_id_not_found():
    """Test getting winery by ID when it doesn't exist."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_empty_result())
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act
    result = await repository.get_by_id(999)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_exception():
    """Test get_by_id raises RepositoryError on exception."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_side_effect(Exception("Database error"))
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_id(1)

    assert "Failed to get winery" in str(exc_info.value)


# ============================================================================
# Tests: get_all()
# ============================================================================


@pytest.mark.asyncio
async def test_get_all_success(sample_winery):
    """Test getting all wineries."""
    winery2 = create_mock_entity(
        Winery,
        id=2,
        name="River Valley Wines",
        region="Sonoma",
        is_deleted=False,
    )
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_query_result([sample_winery, winery2]))
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act
    result = await repository.get_all()

    # Assert
    assert len(result) == 2
    assert result[0] == sample_winery
    assert result[1] == winery2


@pytest.mark.asyncio
async def test_get_all_empty():
    """Test getting all wineries when none exist."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_empty_result())
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act
    result = await repository.get_all()

    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_get_all_exception():
    """Test get_all raises RepositoryError on exception."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_side_effect(Exception("Database error"))
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_all()

    assert "Failed to get all wineries" in str(exc_info.value)


# ============================================================================
# Tests: get_by_name()
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_name_found(sample_winery):
    """Test getting winery by name when it exists."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_query_result([sample_winery]))
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act
    result = await repository.get_by_name("Sunset Vineyards")

    # Assert
    assert result == sample_winery


@pytest.mark.asyncio
async def test_get_by_name_not_found():
    """Test getting winery by name when it doesn't exist."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_empty_result())
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act
    result = await repository.get_by_name("Nonexistent Winery")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_name_exception():
    """Test get_by_name raises RepositoryError on exception."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_side_effect(Exception("Database error"))
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_name("Test Winery")

    assert "Failed to get winery by name" in str(exc_info.value)


# ============================================================================
# Tests: update()
# ============================================================================


@pytest.mark.asyncio
async def test_update_success(sample_winery):
    """Test successful winery update."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_query_result([sample_winery]))
        .build()
    )
    repository = WineryRepository(session_manager)
    
    update_data = WineryUpdate(name="New Name", region="New Region")

    # Act
    result = await repository.update(1, update_data)

    # Assert
    assert result == sample_winery
    assert sample_winery.name == "New Name"
    assert sample_winery.region == "New Region"


@pytest.mark.asyncio
async def test_update_partial(sample_winery):
    """Test partial winery update (only name)."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_query_result([sample_winery]))
        .build()
    )
    repository = WineryRepository(session_manager)
    
    original_region = sample_winery.region
    update_data = WineryUpdate(name="Updated Name")

    # Act
    result = await repository.update(1, update_data)

    # Assert
    assert sample_winery.name == "Updated Name"
    assert sample_winery.region == original_region


@pytest.mark.asyncio
async def test_update_not_found():
    """Test updating nonexistent winery returns None."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_empty_result())
        .build()
    )
    repository = WineryRepository(session_manager)
    
    update_data = WineryUpdate(name="New Name")

    # Act
    result = await repository.update(999, update_data)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_name_raises_error(sample_winery):
    """Test updating to duplicate name raises DuplicateNameError."""
    integrity_error = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    integrity_error.args = (
        "duplicate key value violates unique constraint uq_wineries__name",
    )
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_query_result([sample_winery]))
        .with_flush_side_effect(integrity_error)
        .build()
    )
    repository = WineryRepository(session_manager)
    
    update_data = WineryUpdate(name="Existing Winery")

    # Act & Assert
    with pytest.raises(DuplicateNameError):
        await repository.update(1, update_data)


@pytest.mark.asyncio
async def test_update_exception(sample_winery):
    """Test update raises RepositoryError on generic exception."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_query_result([sample_winery]))
        .with_flush_side_effect(Exception("Database error"))
        .build()
    )
    repository = WineryRepository(session_manager)
    
    update_data = WineryUpdate(name="New Name")

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.update(1, update_data)

    assert "Failed to update winery" in str(exc_info.value)


# ============================================================================
# Tests: delete()
# ============================================================================


@pytest.mark.asyncio
async def test_delete_success(sample_winery):
    """Test successful soft delete of winery."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_query_result([sample_winery]))
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act
    result = await repository.delete(1)

    # Assert
    assert result is True
    assert sample_winery.is_deleted is True


@pytest.mark.asyncio
async def test_delete_not_found():
    """Test deleting nonexistent winery returns False."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_empty_result())
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act
    result = await repository.delete(999)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_exception(sample_winery):
    """Test delete raises RepositoryError on exception."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(create_query_result([sample_winery]))
        .with_flush_side_effect(Exception("Database error"))
        .build()
    )
    repository = WineryRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.delete(1)

    assert "Failed to delete winery" in str(exc_info.value)
