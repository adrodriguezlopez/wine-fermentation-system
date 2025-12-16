"""Unit tests for VineyardRepository."""
import pytest
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
    vineyard = create_mock_entity(
        Vineyard,
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
async def test_create_success(sample_vineyard_create):
    """Test successful vineyard creation."""
    winery_id = 10
    session_manager = MockSessionManagerBuilder().build()
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.create(winery_id, sample_vineyard_create)


@pytest.mark.asyncio
async def test_create_with_minimal_data():
    """Test creating vineyard with only required fields."""
    data = VineyardCreate(code="VIN002", name="South Vineyard")
    session_manager = MockSessionManagerBuilder().build()
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.create(20, data)


@pytest.mark.asyncio
async def test_create_duplicate_code_raises_error(sample_vineyard_create):
    """Test creating vineyard with duplicate code raises DuplicateCodeError."""
    integrity_error = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    integrity_error.args = (
        "duplicate key value violates unique constraint uq_vineyards__code__winery_id",
    )
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_flush_side_effect(integrity_error)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act & Assert
    with pytest.raises(DuplicateCodeError) as exc_info:
        await repository.create(10, sample_vineyard_create)

    assert "VIN001" in str(exc_info.value)
    assert "winery 10" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_integrity_error_other_constraint(sample_vineyard_create):
    """Test creating vineyard with other integrity error raises RepositoryError."""
    integrity_error = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    integrity_error.args = ("some other constraint violation",)
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_flush_side_effect(integrity_error)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.create(10, sample_vineyard_create)

    assert "Failed to create vineyard" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_generic_exception_raises_repository_error(sample_vineyard_create):
    """Test generic exception during create raises RepositoryError."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_flush_side_effect(Exception("Database error"))
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.create(10, sample_vineyard_create)

    assert "Failed to create vineyard" in str(exc_info.value)


# ============================================================================
# Tests: get_by_id()
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_id_found(sample_vineyard):
    """Test getting vineyard by ID returns vineyard."""
    result = create_query_result([sample_vineyard])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.get_by_id(1, 10)

    # Assert
    assert result == sample_vineyard


@pytest.mark.asyncio
async def test_get_by_id_not_found():
    """Test getting non-existent vineyard returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.get_by_id(999, 10)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_wrong_winery():
    """Test getting vineyard with wrong winery_id returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.get_by_id(1, 999)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_soft_deleted():
    """Test getting soft-deleted vineyard returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.get_by_id(1, 10)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_exception_raises_repository_error():
    """Test exception during get_by_id raises RepositoryError."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_side_effect(Exception("Database error"))
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_id(1, 10)

    assert "Failed to get vineyard" in str(exc_info.value)


# ============================================================================
# Tests: get_by_winery()
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_winery_returns_multiple():
    """Test getting all vineyards for a winery."""
    vineyard1 = create_mock_entity(
        Vineyard, id=1, winery_id=10, code="VIN001", name="North", is_deleted=False
    )
    vineyard2 = create_mock_entity(
        Vineyard, id=2, winery_id=10, code="VIN002", name="South", is_deleted=False
    )

    result = create_query_result([vineyard1, vineyard2])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.get_by_winery(10)

    # Assert
    assert len(result) == 2
    assert result[0] == vineyard1
    assert result[1] == vineyard2


@pytest.mark.asyncio
async def test_get_by_winery_returns_empty_list():
    """Test getting vineyards for winery with no vineyards."""
    result = create_query_result([])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.get_by_winery(999)

    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_get_by_winery_excludes_soft_deleted():
    """Test get_by_winery excludes soft-deleted vineyards."""
    vineyard1 = create_mock_entity(
        Vineyard, id=1, winery_id=10, code="VIN001", name="North", is_deleted=False
    )

    result = create_query_result([vineyard1])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.get_by_winery(10)

    # Assert
    assert len(result) == 1
    assert result[0].is_deleted is False


@pytest.mark.asyncio
async def test_get_by_winery_exception_raises_repository_error():
    """Test exception during get_by_winery raises RepositoryError."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_side_effect(Exception("Database error"))
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_winery(10)

    assert "Failed to get vineyards" in str(exc_info.value)


# ============================================================================
# Tests: get_by_code()
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_code_found(sample_vineyard):
    """Test getting vineyard by code returns vineyard."""
    result = create_query_result([sample_vineyard])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.get_by_code("VIN001", 10)

    # Assert
    assert result == sample_vineyard


@pytest.mark.asyncio
async def test_get_by_code_not_found():
    """Test getting non-existent code returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.get_by_code("NONEXISTENT", 10)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_wrong_winery():
    """Test getting code with wrong winery returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.get_by_code("VIN001", 999)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_soft_deleted():
    """Test getting soft-deleted vineyard by code returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.get_by_code("VIN001", 10)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_exception_raises_repository_error():
    """Test exception during get_by_code raises RepositoryError."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_side_effect(Exception("Database error"))
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_code("VIN001", 10)

    assert "Failed to get vineyard by code" in str(exc_info.value)


# ============================================================================
# Tests: update()
# ============================================================================


@pytest.mark.asyncio
async def test_update_all_fields(sample_vineyard):
    """Test updating all vineyard fields."""
    result = create_query_result([sample_vineyard])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

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


@pytest.mark.asyncio
async def test_update_partial_fields(sample_vineyard):
    """Test updating only some fields."""
    result = create_query_result([sample_vineyard])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    update_data = VineyardUpdate(name="Partially Updated")

    # Act
    result = await repository.update(1, 10, update_data)

    # Assert
    assert result.code == "VIN001"  # Unchanged
    assert result.name == "Partially Updated"
    assert result.notes == "Premium location"  # Unchanged


@pytest.mark.asyncio
async def test_update_not_found():
    """Test updating non-existent vineyard returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    update_data = VineyardUpdate(name="Updated")

    # Act
    result = await repository.update(999, 10, update_data)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_code_raises_error(sample_vineyard):
    """Test updating to duplicate code raises DuplicateCodeError."""
    result = create_query_result([sample_vineyard])
    
    integrity_error = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    integrity_error.args = (
        "duplicate key value violates unique constraint uq_vineyards__code__winery_id",
    )
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .with_flush_side_effect(integrity_error)
        .build()
    )
    repository = VineyardRepository(session_manager)

    update_data = VineyardUpdate(code="DUPLICATE")

    # Act & Assert
    with pytest.raises(DuplicateCodeError) as exc_info:
        await repository.update(1, 10, update_data)

    assert "DUPLICATE" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_generic_exception_raises_repository_error(sample_vineyard):
    """Test generic exception during update raises RepositoryError."""
    result = create_query_result([sample_vineyard])
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .with_flush_side_effect(Exception("Database error"))
        .build()
    )
    repository = VineyardRepository(session_manager)

    update_data = VineyardUpdate(name="Updated")

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.update(1, 10, update_data)

    assert "Failed to update vineyard" in str(exc_info.value)


# ============================================================================
# Tests: delete()
# ============================================================================


@pytest.mark.asyncio
async def test_delete_success(sample_vineyard):
    """Test successful vineyard deletion."""
    result = create_query_result([sample_vineyard])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.delete(1, 10)

    # Assert
    assert result is True
    assert sample_vineyard.is_deleted is True


@pytest.mark.asyncio
async def test_delete_not_found():
    """Test deleting non-existent vineyard returns False."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.delete(999, 10)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_idempotent(sample_vineyard):
    """Test deleting already deleted vineyard is idempotent."""
    sample_vineyard.is_deleted = True
    result = create_query_result([sample_vineyard])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act
    result = await repository.delete(1, 10)

    # Assert
    assert result is True
    assert sample_vineyard.is_deleted is True


@pytest.mark.asyncio
async def test_delete_exception_raises_repository_error(sample_vineyard):
    """Test exception during delete raises RepositoryError."""
    result = create_query_result([sample_vineyard])
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .with_flush_side_effect(Exception("Database error"))
        .build()
    )
    repository = VineyardRepository(session_manager)

    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.delete(1, 10)

    assert "Failed to delete vineyard" in str(exc_info.value)
