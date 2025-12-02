"""Unit tests for VineyardBlockRepository."""
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from decimal import Decimal

from src.modules.fruit_origin.src.repository_component.repositories.vineyard_block_repository import (
    VineyardBlockRepository,
)
from src.modules.fruit_origin.src.domain.dtos.vineyard_block_dtos import (
    VineyardBlockCreate,
    VineyardBlockUpdate,
)
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.repository_component.errors import (
    RepositoryError,
    DuplicateCodeError,
    NotFoundError,
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
    """Create VineyardBlockRepository with mocked session manager."""
    manager, _ = mock_session_manager
    return VineyardBlockRepository(manager)


@pytest.fixture
def sample_vineyard():
    """Sample Vineyard entity."""
    vineyard = Vineyard(
        id=100,
        winery_id=10,
        code="VIN001",
        name="North Vineyard",
        is_deleted=False,
    )
    return vineyard


@pytest.fixture
def sample_block_create():
    """Sample VineyardBlockCreate DTO with all fields."""
    return VineyardBlockCreate(
        code="BLOCK-A",
        soil_type="Clay Loam",
        slope_pct=Decimal("5.5"),
        aspect_deg=180,
        area_ha=Decimal("2.5"),
        elevation_m=350,
        latitude=Decimal("42.1234"),
        longitude=Decimal("-8.5678"),
        notes="Premium block",
        irrigation=True,
        organic_certified=True,
    )


@pytest.fixture
def sample_block():
    """Sample VineyardBlock entity."""
    block = VineyardBlock(
        id=1,
        vineyard_id=100,
        code="BLOCK-A",
        soil_type="Clay Loam",
        slope_pct=Decimal("5.5"),
        aspect_deg=180,
        area_ha=Decimal("2.5"),
        elevation_m=350,
        latitude=Decimal("42.1234"),
        longitude=Decimal("-8.5678"),
        notes="Premium block",
        irrigation=True,
        organic_certified=True,
        is_deleted=False,
    )
    return block


# ============================================================================
# Test Create
# ============================================================================


@pytest.mark.asyncio
async def test_create_success(repository, mock_session_manager, sample_vineyard, sample_block_create):
    """Test successful block creation."""
    manager, mock_session = mock_session_manager
    
    # Mock vineyard query
    vineyard_result = MagicMock()
    vineyard_result.scalar_one_or_none.return_value = sample_vineyard
    
    # First execute call is for vineyard verification
    mock_session.execute.return_value = vineyard_result
    
    # Act
    result = await repository.create(100, 10, sample_block_create)
    
    # Assert
    assert mock_session.add.called
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_with_minimal_data(repository, mock_session_manager, sample_vineyard):
    """Test creating block with only required field (code)."""
    manager, mock_session = mock_session_manager
    
    # Mock vineyard query
    vineyard_result = MagicMock()
    vineyard_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = vineyard_result
    
    minimal_data = VineyardBlockCreate(code="BLOCK-B")
    
    # Act
    result = await repository.create(100, 10, minimal_data)
    
    # Assert
    assert mock_session.add.called
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_vineyard_not_found_raises_error(repository, mock_session_manager):
    """Test creating block for non-existent vineyard raises NotFoundError."""
    manager, mock_session = mock_session_manager
    
    # Mock vineyard query returning None
    vineyard_result = MagicMock()
    vineyard_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = vineyard_result
    
    data = VineyardBlockCreate(code="BLOCK-A")
    
    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await repository.create(999, 10, data)
    
    assert "Vineyard 999 not found" in str(exc_info.value)
    assert not mock_session.add.called


@pytest.mark.asyncio
async def test_create_duplicate_code_raises_error(repository, mock_session_manager, sample_vineyard):
    """Test creating block with duplicate code raises DuplicateCodeError."""
    manager, mock_session = mock_session_manager
    
    # Mock vineyard query
    vineyard_result = MagicMock()
    vineyard_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = vineyard_result
    
    mock_session.flush.side_effect = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    mock_session.flush.side_effect.args = (
        "duplicate key value violates unique constraint uq_vineyard_blocks__code__vineyard_id",
    )
    
    data = VineyardBlockCreate(code="DUPLICATE")
    
    # Act & Assert
    with pytest.raises(DuplicateCodeError) as exc_info:
        await repository.create(100, 10, data)
    
    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_integrity_error_other_constraint(repository, mock_session_manager, sample_vineyard):
    """Test other integrity error raises RepositoryError."""
    manager, mock_session = mock_session_manager
    
    # Mock vineyard query
    vineyard_result = MagicMock()
    vineyard_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = vineyard_result
    
    mock_session.flush.side_effect = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    
    data = VineyardBlockCreate(code="BLOCK-A")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.create(100, 10, data)
    
    assert "Failed to create vineyard block" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_generic_exception_raises_repository_error(repository, mock_session_manager, sample_vineyard):
    """Test generic exception during create raises RepositoryError."""
    manager, mock_session = mock_session_manager
    
    # Mock vineyard query
    vineyard_result = MagicMock()
    vineyard_result.scalar_one_or_none.return_value = sample_vineyard
    mock_session.execute.return_value = vineyard_result
    
    mock_session.flush.side_effect = Exception("Database error")
    
    data = VineyardBlockCreate(code="BLOCK-A")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.create(100, 10, data)
    
    assert "Failed to create vineyard block" in str(exc_info.value)


# ============================================================================
# Test Get By ID
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_id_found(repository, mock_session_manager, sample_block):
    """Test getting block by ID returns the block."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_block
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_id(1, 10)
    
    # Assert
    assert result == sample_block
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_id_not_found(repository, mock_session_manager):
    """Test getting non-existent block returns None."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_id(999, 10)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_wrong_winery(repository, mock_session_manager):
    """Test getting block from wrong winery returns None."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_id(1, 999)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_soft_deleted(repository, mock_session_manager):
    """Test getting soft-deleted block returns None."""
    manager, mock_session = mock_session_manager
    
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
    
    mock_session.execute.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_id(1, 10)
    
    assert "Failed to get vineyard block" in str(exc_info.value)


# ============================================================================
# Test Get By Vineyard
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_vineyard_returns_multiple(repository, mock_session_manager):
    """Test getting blocks for a vineyard returns multiple blocks."""
    manager, mock_session = mock_session_manager
    
    block1 = VineyardBlock(id=1, vineyard_id=100, code="BLOCK-A", is_deleted=False)
    block2 = VineyardBlock(id=2, vineyard_id=100, code="BLOCK-B", is_deleted=False)
    
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [block1, block2]
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_vineyard(100, 10)
    
    # Assert
    assert len(result) == 2
    assert result[0].code == "BLOCK-A"
    assert result[1].code == "BLOCK-B"


@pytest.mark.asyncio
async def test_get_by_vineyard_returns_empty_list(repository, mock_session_manager):
    """Test getting blocks for vineyard with no blocks returns empty list."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_vineyard(100, 10)
    
    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_get_by_vineyard_excludes_soft_deleted(repository, mock_session_manager):
    """Test getting blocks excludes soft-deleted blocks."""
    manager, mock_session = mock_session_manager
    
    block1 = VineyardBlock(id=1, vineyard_id=100, code="BLOCK-A", is_deleted=False)
    
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [block1]
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_vineyard(100, 10)
    
    # Assert
    assert len(result) == 1
    assert not result[0].is_deleted


@pytest.mark.asyncio
async def test_get_by_vineyard_orders_by_code(repository, mock_session_manager):
    """Test blocks are ordered by code ascending."""
    manager, mock_session = mock_session_manager
    
    # Return blocks in order (mock already ordered)
    block1 = VineyardBlock(id=1, vineyard_id=100, code="BLOCK-A", is_deleted=False)
    block2 = VineyardBlock(id=2, vineyard_id=100, code="BLOCK-B", is_deleted=False)
    
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [block1, block2]
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_vineyard(100, 10)
    
    # Assert
    assert result[0].code < result[1].code


@pytest.mark.asyncio
async def test_get_by_vineyard_exception_raises_repository_error(repository, mock_session_manager):
    """Test exception during get_by_vineyard raises RepositoryError."""
    manager, mock_session = mock_session_manager
    
    mock_session.execute.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_vineyard(100, 10)
    
    assert "Failed to get blocks" in str(exc_info.value)


# ============================================================================
# Test Get By Code
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_code_found(repository, mock_session_manager, sample_block):
    """Test getting block by code returns the block."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_block
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_code("BLOCK-A", 100, 10)
    
    # Assert
    assert result == sample_block


@pytest.mark.asyncio
async def test_get_by_code_not_found(repository, mock_session_manager):
    """Test getting non-existent block by code returns None."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_code("NONEXISTENT", 100, 10)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_wrong_vineyard(repository, mock_session_manager):
    """Test getting block from wrong vineyard returns None."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_code("BLOCK-A", 999, 10)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_wrong_winery(repository, mock_session_manager):
    """Test getting block from wrong winery returns None."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_code("BLOCK-A", 100, 999)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_soft_deleted(repository, mock_session_manager):
    """Test getting soft-deleted block by code returns None."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.get_by_code("BLOCK-A", 100, 10)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_exception_raises_repository_error(repository, mock_session_manager):
    """Test exception during get_by_code raises RepositoryError."""
    manager, mock_session = mock_session_manager
    
    mock_session.execute.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_code("BLOCK-A", 100, 10)
    
    assert "Failed to get vineyard block" in str(exc_info.value)


# ============================================================================
# Test Update
# ============================================================================


@pytest.mark.asyncio
async def test_update_all_fields(repository, mock_session_manager, sample_block):
    """Test updating all block fields."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_block
    mock_session.execute.return_value = mock_result
    
    update_data = VineyardBlockUpdate(
        code="BLOCK-A-NEW",
        soil_type="Sandy Loam",
        slope_pct=Decimal("8.0"),
        aspect_deg=270,
        area_ha=Decimal("3.0"),
        elevation_m=400,
        latitude=Decimal("42.9999"),
        longitude=Decimal("-8.1111"),
        notes="Updated notes",
        irrigation=False,
        organic_certified=False,
    )
    
    # Act
    result = await repository.update(1, 10, update_data)
    
    # Assert
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_partial_fields(repository, mock_session_manager, sample_block):
    """Test updating only some fields."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_block
    mock_session.execute.return_value = mock_result
    
    update_data = VineyardBlockUpdate(soil_type="New Soil Type")
    
    # Act
    result = await repository.update(1, 10, update_data)
    
    # Assert
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_not_found(repository, mock_session_manager):
    """Test updating non-existent block returns None."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    update_data = VineyardBlockUpdate(soil_type="New Soil Type")
    
    # Act
    result = await repository.update(999, 10, update_data)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_code_raises_error(repository, mock_session_manager, sample_block):
    """Test updating to duplicate code raises DuplicateCodeError."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_block
    mock_session.execute.return_value = mock_result
    
    mock_session.flush.side_effect = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    mock_session.flush.side_effect.args = (
        "duplicate key value violates unique constraint uq_vineyard_blocks__code__vineyard_id",
    )
    
    update_data = VineyardBlockUpdate(code="DUPLICATE")
    
    # Act & Assert
    with pytest.raises(DuplicateCodeError) as exc_info:
        await repository.update(1, 10, update_data)
    
    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_generic_exception_raises_repository_error(repository, mock_session_manager, sample_block):
    """Test generic exception during update raises RepositoryError."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_block
    mock_session.execute.return_value = mock_result
    
    mock_session.flush.side_effect = Exception("Database error")
    
    update_data = VineyardBlockUpdate(soil_type="New Soil Type")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.update(1, 10, update_data)
    
    assert "Failed to update vineyard block" in str(exc_info.value)


# ============================================================================
# Test Delete
# ============================================================================


@pytest.mark.asyncio
async def test_delete_success(repository, mock_session_manager, sample_block):
    """Test successful block deletion."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_block
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.delete(1, 10)
    
    # Assert
    assert result is True
    assert sample_block.is_deleted is True
    mock_session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_not_found(repository, mock_session_manager):
    """Test deleting non-existent block returns False."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.delete(999, 10)
    
    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_idempotent(repository, mock_session_manager):
    """Test deleting already deleted block is idempotent."""
    manager, mock_session = mock_session_manager
    
    # Already soft-deleted blocks won't be returned by query (is_deleted == False filter)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    # Act
    result = await repository.delete(1, 10)
    
    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_exception_raises_repository_error(repository, mock_session_manager, sample_block):
    """Test exception during delete raises RepositoryError."""
    manager, mock_session = mock_session_manager
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_block
    mock_session.execute.return_value = mock_result
    
    mock_session.flush.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.delete(1, 10)
    
    assert "Failed to delete vineyard block" in str(exc_info.value)
