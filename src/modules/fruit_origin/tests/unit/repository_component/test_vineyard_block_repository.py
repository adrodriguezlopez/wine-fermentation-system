"""Unit tests for VineyardBlockRepository."""
import pytest
from sqlalchemy.exc import IntegrityError
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
def sample_vineyard():
    """Sample Vineyard entity."""
    return create_mock_entity(
        Vineyard,
        id=100,
        winery_id=10,
        code="VIN001",
        name="North Vineyard",
        is_deleted=False,
    )


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
    return create_mock_entity(
        VineyardBlock,
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


# ============================================================================
# Test Create
# ============================================================================


@pytest.mark.asyncio
async def test_create_success(sample_vineyard, sample_block_create):
    """Test successful block creation."""
    vineyard_result = create_query_result([sample_vineyard])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(vineyard_result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.create(100, 10, sample_block_create)


@pytest.mark.asyncio
async def test_create_with_minimal_data(sample_vineyard):
    """Test creating block with only required field (code)."""
    vineyard_result = create_query_result([sample_vineyard])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(vineyard_result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    minimal_data = VineyardBlockCreate(code="BLOCK-B")
    
    # Act
    result = await repository.create(100, 10, minimal_data)


@pytest.mark.asyncio
async def test_create_vineyard_not_found_raises_error():
    """Test creating block for non-existent vineyard raises NotFoundError."""
    vineyard_result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(vineyard_result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    data = VineyardBlockCreate(code="BLOCK-A")
    
    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await repository.create(999, 10, data)
    
    assert "Vineyard 999 not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_duplicate_code_raises_error(sample_vineyard):
    """Test creating block with duplicate code raises DuplicateCodeError."""
    vineyard_result = create_query_result([sample_vineyard])
    
    integrity_error = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    integrity_error.args = (
        "duplicate key value violates unique constraint uq_vineyard_blocks__code__vineyard_id",
    )
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(vineyard_result)
        .with_flush_side_effect(integrity_error)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    data = VineyardBlockCreate(code="DUPLICATE")
    
    # Act & Assert
    with pytest.raises(DuplicateCodeError) as exc_info:
        await repository.create(100, 10, data)
    
    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_integrity_error_other_constraint(sample_vineyard):
    """Test other integrity error raises RepositoryError."""
    vineyard_result = create_query_result([sample_vineyard])
    
    integrity_error = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(vineyard_result)
        .with_flush_side_effect(integrity_error)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    data = VineyardBlockCreate(code="BLOCK-A")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.create(100, 10, data)
    
    assert "Failed to create vineyard block" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_generic_exception_raises_repository_error(sample_vineyard):
    """Test generic exception during create raises RepositoryError."""
    vineyard_result = create_query_result([sample_vineyard])
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(vineyard_result)
        .with_flush_side_effect(Exception("Database error"))
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    data = VineyardBlockCreate(code="BLOCK-A")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.create(100, 10, data)
    
    assert "Failed to create vineyard block" in str(exc_info.value)


# ============================================================================
# Test Get By ID
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_id_found(sample_block):
    """Test getting block by ID returns the block."""
    result = create_query_result([sample_block])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_id(1, 10)
    
    # Assert
    assert result == sample_block


@pytest.mark.asyncio
async def test_get_by_id_not_found():
    """Test getting non-existent block returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_id(999, 10)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_wrong_winery():
    """Test getting block from wrong winery returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_id(1, 999)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_soft_deleted():
    """Test getting soft-deleted block returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
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
    repository = VineyardBlockRepository(session_manager)
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_id(1, 10)
    
    assert "Failed to get vineyard block" in str(exc_info.value)


# ============================================================================
# Test Get By Vineyard
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_vineyard_returns_multiple():
    """Test getting blocks for a vineyard returns multiple blocks."""
    block1 = create_mock_entity(VineyardBlock, id=1, vineyard_id=100, code="BLOCK-A", is_deleted=False)
    block2 = create_mock_entity(VineyardBlock, id=2, vineyard_id=100, code="BLOCK-B", is_deleted=False)
    
    result = create_query_result([block1, block2])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_vineyard(100, 10)
    
    # Assert
    assert len(result) == 2
    assert result[0].code == "BLOCK-A"
    assert result[1].code == "BLOCK-B"


@pytest.mark.asyncio
async def test_get_by_vineyard_returns_empty_list():
    """Test getting blocks for vineyard with no blocks returns empty list."""
    result = create_query_result([])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_vineyard(100, 10)
    
    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_get_by_vineyard_excludes_soft_deleted():
    """Test getting blocks excludes soft-deleted blocks."""
    block1 = create_mock_entity(VineyardBlock, id=1, vineyard_id=100, code="BLOCK-A", is_deleted=False)
    
    result = create_query_result([block1])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_vineyard(100, 10)
    
    # Assert
    assert len(result) == 1
    assert not result[0].is_deleted


@pytest.mark.asyncio
async def test_get_by_vineyard_orders_by_code():
    """Test blocks are ordered by code ascending."""
    block1 = create_mock_entity(VineyardBlock, id=1, vineyard_id=100, code="BLOCK-A", is_deleted=False)
    block2 = create_mock_entity(VineyardBlock, id=2, vineyard_id=100, code="BLOCK-B", is_deleted=False)
    
    result = create_query_result([block1, block2])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_vineyard(100, 10)
    
    # Assert
    assert result[0].code < result[1].code


@pytest.mark.asyncio
async def test_get_by_vineyard_exception_raises_repository_error():
    """Test exception during get_by_vineyard raises RepositoryError."""
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_side_effect(Exception("Database error"))
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_vineyard(100, 10)
    
    assert "Failed to get blocks" in str(exc_info.value)


# ============================================================================
# Test Get By Code
# ============================================================================


@pytest.mark.asyncio
async def test_get_by_code_found(sample_block):
    """Test getting block by code returns the block."""
    result = create_query_result([sample_block])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_code("BLOCK-A", 100, 10)
    
    # Assert
    assert result == sample_block


@pytest.mark.asyncio
async def test_get_by_code_not_found():
    """Test getting non-existent block by code returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_code("NONEXISTENT", 100, 10)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_wrong_vineyard():
    """Test getting block from wrong vineyard returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_code("BLOCK-A", 999, 10)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_wrong_winery():
    """Test getting block from wrong winery returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_code("BLOCK-A", 100, 999)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_code_soft_deleted():
    """Test getting soft-deleted block by code returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.get_by_code("BLOCK-A", 100, 10)
    
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
    repository = VineyardBlockRepository(session_manager)
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.get_by_code("BLOCK-A", 100, 10)
    
    assert "Failed to get vineyard block" in str(exc_info.value)


# ============================================================================
# Test Update
# ============================================================================


@pytest.mark.asyncio
async def test_update_all_fields(sample_block):
    """Test updating all block fields."""
    result = create_query_result([sample_block])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
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


@pytest.mark.asyncio
async def test_update_partial_fields(sample_block):
    """Test updating only some fields."""
    result = create_query_result([sample_block])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    update_data = VineyardBlockUpdate(soil_type="New Soil Type")
    
    # Act
    result = await repository.update(1, 10, update_data)


@pytest.mark.asyncio
async def test_update_not_found():
    """Test updating non-existent block returns None."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    update_data = VineyardBlockUpdate(soil_type="New Soil Type")
    
    # Act
    result = await repository.update(999, 10, update_data)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_duplicate_code_raises_error(sample_block):
    """Test updating to duplicate code raises DuplicateCodeError."""
    result = create_query_result([sample_block])
    
    integrity_error = IntegrityError(
        "statement", "params", "orig", connection_invalidated=False
    )
    integrity_error.args = (
        "duplicate key value violates unique constraint uq_vineyard_blocks__code__vineyard_id",
    )
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .with_flush_side_effect(integrity_error)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    update_data = VineyardBlockUpdate(code="DUPLICATE")
    
    # Act & Assert
    with pytest.raises(DuplicateCodeError) as exc_info:
        await repository.update(1, 10, update_data)
    
    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_generic_exception_raises_repository_error(sample_block):
    """Test generic exception during update raises RepositoryError."""
    result = create_query_result([sample_block])
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .with_flush_side_effect(Exception("Database error"))
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    update_data = VineyardBlockUpdate(soil_type="New Soil Type")
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.update(1, 10, update_data)
    
    assert "Failed to update vineyard block" in str(exc_info.value)


# ============================================================================
# Test Delete
# ============================================================================


@pytest.mark.asyncio
async def test_delete_success(sample_block):
    """Test successful block deletion."""
    result = create_query_result([sample_block])
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.delete(1, 10)
    
    # Assert
    assert result is True
    assert sample_block.is_deleted is True


@pytest.mark.asyncio
async def test_delete_not_found():
    """Test deleting non-existent block returns False."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.delete(999, 10)
    
    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_idempotent():
    """Test deleting already deleted block is idempotent."""
    result = create_empty_result()
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act
    result = await repository.delete(1, 10)
    
    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_exception_raises_repository_error(sample_block):
    """Test exception during delete raises RepositoryError."""
    result = create_query_result([sample_block])
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .with_flush_side_effect(Exception("Database error"))
        .build()
    )
    repository = VineyardBlockRepository(session_manager)
    
    # Act & Assert
    with pytest.raises(RepositoryError) as exc_info:
        await repository.delete(1, 10)
    
    assert "Failed to delete vineyard block" in str(exc_info.value)
