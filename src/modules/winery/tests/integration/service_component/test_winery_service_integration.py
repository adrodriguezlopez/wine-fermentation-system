"""
Integration tests for WineryService.

These tests verify the behavior of the WineryService with a real database connection
and real repository implementations (while mocking cross-module dependencies).
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.winery.src.service_component.services.winery_service import WineryService
from src.modules.winery.src.domain.dtos.winery_dtos import (
    WineryCreate,
    WineryUpdate,
)
from src.shared.domain.errors import (
    WineryNotFound,
    DuplicateCodeError,
    InvalidWineryData,
    WineryHasActiveDataError,
)


# ================================
# Create Tests
# ================================


@pytest.mark.asyncio
class TestWineryServiceCreate:
    """Test winery creation through the service layer."""

    async def test_create_winery_success(
        self, winery_service: WineryService, test_winery: Winery
    ):
        """
        GIVEN a valid WineryCreate
        WHEN creating a new winery
        THEN the winery should be created successfully with all fields
        """
        # Arrange
        unique_code = f"NEW-{str(uuid4())[:8].upper()}"
        dto = WineryCreate(
            code=unique_code,
            name="New Test Winery",
            location="Mendoza, Argentina",
            notes="A beautiful winery in the Andes",
        )

        # Act
        result = await winery_service.create_winery(dto)

        # Assert
        assert result is not None
        assert result.code == unique_code
        assert result.name == "New Test Winery"
        assert result.location == "Mendoza, Argentina"
        assert result.notes == "A beautiful winery in the Andes"
        assert result.is_deleted is False

    async def test_create_winery_with_minimal_fields(
        self, winery_service: WineryService
    ):
        """
        GIVEN a WineryCreate with only required fields
        WHEN creating a new winery
        THEN the winery should be created with optional fields as None
        """
        # Arrange
        unique_code = f"MIN-{str(uuid4())[:8].upper()}"
        dto = WineryCreate(
            code=unique_code,
            name="Minimal Winery",
        )

        # Act
        result = await winery_service.create_winery(dto)

        # Assert
        assert result is not None
        assert result.code == unique_code
        assert result.name == "Minimal Winery"
        assert result.location is None
        assert result.notes is None

    async def test_create_winery_duplicate_code_fails(
        self, winery_service: WineryService, test_winery: Winery
    ):
        """
        GIVEN a WineryCreate with a code that already exists
        WHEN creating a new winery
        THEN DuplicateCodeError should be raised
        """
        # Arrange
        dto = WineryCreate(
            code=test_winery.code,  # Existing code
            name="Another Winery",
        )

        # Act & Assert
        with pytest.raises(DuplicateCodeError) as exc_info:
            await winery_service.create_winery(dto)
        
        assert test_winery.code in str(exc_info.value)

    async def test_create_winery_invalid_code_format_fails(
        self, winery_service: WineryService
    ):
        """
        GIVEN a WineryCreate with an invalid code format (lowercase)
        WHEN creating a new winery
        THEN InvalidWineryData should be raised
        """
        # Arrange
        dto = WineryCreate(
            code="invalid-lowercase",  # Should be uppercase
            name="Invalid Winery",
        )

        # Act & Assert
        with pytest.raises(InvalidWineryData) as exc_info:
            await winery_service.create_winery(dto)
        
        assert "uppercase" in str(exc_info.value).lower()


# ================================
# Read Tests
# ================================


@pytest.mark.asyncio
class TestWineryServiceRead:
    """Test winery retrieval operations."""

    async def test_get_winery_success(
        self, winery_service: WineryService, test_winery: Winery
    ):
        """
        GIVEN an existing winery ID
        WHEN getting the winery by ID
        THEN the correct winery should be returned
        """
        # Act
        result = await winery_service.get_winery(test_winery.id)

        # Assert
        assert result is not None
        assert result.id == test_winery.id
        assert result.code == test_winery.code
        assert result.name == test_winery.name

    async def test_get_winery_not_found(self, winery_service: WineryService):
        """
        GIVEN a non-existent winery ID
        WHEN getting the winery by ID
        THEN WineryNotFound should be raised
        """
        # Arrange
        non_existent_id = str(uuid4())

        # Act & Assert
        with pytest.raises(WineryNotFound) as exc_info:
            await winery_service.get_winery(non_existent_id)
        
        assert non_existent_id in str(exc_info.value)

    async def test_get_winery_by_code_success(
        self, winery_service: WineryService, test_winery: Winery
    ):
        """
        GIVEN an existing winery code
        WHEN getting the winery by code
        THEN the correct winery should be returned
        """
        # Act
        result = await winery_service.get_winery_by_code(test_winery.code)

        # Assert
        assert result is not None
        assert result.id == test_winery.id
        assert result.code == test_winery.code
        assert result.name == test_winery.name

    async def test_list_wineries_returns_all(
        self, winery_service: WineryService, test_winery: Winery, test_winery_2: Winery
    ):
        """
        GIVEN multiple existing wineries
        WHEN listing all wineries
        THEN all non-deleted wineries should be returned
        """
        # Act
        result = await winery_service.list_wineries()

        # Assert
        assert len(result) >= 2
        winery_ids = [w.id for w in result]
        assert test_winery.id in winery_ids
        assert test_winery_2.id in winery_ids

    async def test_winery_exists_true(
        self, winery_service: WineryService, test_winery: Winery
    ):
        """
        GIVEN an existing winery ID
        WHEN checking if the winery exists
        THEN True should be returned
        """
        # Act
        result = await winery_service.winery_exists(test_winery.id)

        # Assert
        assert result is True

    async def test_winery_exists_false(self, winery_service: WineryService):
        """
        GIVEN a non-existent winery ID
        WHEN checking if the winery exists
        THEN False should be returned
        """
        # Arrange
        non_existent_id = str(uuid4())

        # Act
        result = await winery_service.winery_exists(non_existent_id)

        # Assert
        assert result is False


# ================================
# Update Tests
# ================================


@pytest.mark.asyncio
class TestWineryServiceUpdate:
    """Test winery update operations."""

    async def test_update_winery_success(
        self, winery_service: WineryService, test_winery: Winery
    ):
        """
        GIVEN an existing winery and valid update data
        WHEN updating the winery
        THEN the winery should be updated successfully
        """
        # Arrange
        dto = WineryUpdate(
            name="Updated Winery Name",
            location="Updated Location",
            notes="Updated notes",
        )

        # Act
        result = await winery_service.update_winery(test_winery.id, dto)

        # Assert
        assert result is not None
        assert result.id == test_winery.id
        assert result.name == "Updated Winery Name"
        assert result.location == "Updated Location"
        assert result.notes == "Updated notes"

    async def test_update_winery_partial(
        self, winery_service: WineryService, test_winery: Winery
    ):
        """
        GIVEN an existing winery and partial update data
        WHEN updating only some fields
        THEN only specified fields should be updated
        """
        # Arrange
        original_location = test_winery.location
        dto = WineryUpdate(
            name="Partially Updated Name",
        )

        # Act
        result = await winery_service.update_winery(test_winery.id, dto)

        # Assert
        assert result is not None
        assert result.name == "Partially Updated Name"
        assert result.location == original_location  # Unchanged

    async def test_update_winery_not_found(self, winery_service: WineryService):
        """
        GIVEN a non-existent winery ID
        WHEN attempting to update
        THEN WineryNotFound should be raised
        """
        # Arrange
        non_existent_id = str(uuid4())
        dto = WineryUpdate(name="Updated Name")

        # Act & Assert
        with pytest.raises(WineryNotFound):
            await winery_service.update_winery(non_existent_id, dto)


# ================================
# Delete Tests
# ================================


@pytest.mark.asyncio
class TestWineryServiceDelete:
    """Test winery deletion operations."""

    async def test_delete_winery_success(
        self, winery_service: WineryService, test_winery: Winery
    ):
        """
        GIVEN an existing winery with no dependent data
        WHEN deleting the winery
        THEN the winery should be marked as deleted
        """
        # Act
        await winery_service.delete_winery(test_winery.id)

        # Assert - Verify it's deleted
        with pytest.raises(WineryNotFound):
            await winery_service.get_winery(test_winery.id)

    async def test_delete_winery_with_vineyards_fails(
        self, winery_service: WineryService, test_winery: Winery
    ):
        """
        GIVEN a winery with associated vineyards
        WHEN attempting to delete the winery
        THEN WineryHasActiveDataError should be raised
        """
        # Arrange - Mock vineyard_repo to return non-empty list
        winery_service._vineyard_repo.get_by_winery = AsyncMock(return_value=[{"id": "1"}])

        # Act & Assert
        with pytest.raises(WineryHasActiveDataError) as exc_info:
            await winery_service.delete_winery(test_winery.id)
        
        assert "vineyards" in str(exc_info.value).lower()

    async def test_delete_winery_with_fermentations_fails(
        self, winery_service: WineryService, test_winery: Winery
    ):
        """
        GIVEN a winery with associated fermentations
        WHEN attempting to delete the winery
        THEN WineryHasActiveDataError should be raised
        """
        # Arrange - Mock fermentation_repo to return non-empty list
        winery_service._fermentation_repo.get_by_winery = AsyncMock(return_value=[{"id": "1"}])

        # Act & Assert
        with pytest.raises(WineryHasActiveDataError) as exc_info:
            await winery_service.delete_winery(test_winery.id)
        
        assert "fermentations" in str(exc_info.value).lower()


# ================================
# Statistics Tests
# ================================


@pytest.mark.asyncio
class TestWineryServiceStatistics:
    """Test winery statistics operations."""

    async def test_count_wineries(
        self, winery_service: WineryService, test_winery: Winery, test_winery_2: Winery
    ):
        """
        GIVEN multiple existing wineries
        WHEN counting wineries
        THEN the correct count should be returned
        """
        # Act
        result = await winery_service.count_wineries()

        # Assert
        assert result >= 2  # At least our two test wineries
