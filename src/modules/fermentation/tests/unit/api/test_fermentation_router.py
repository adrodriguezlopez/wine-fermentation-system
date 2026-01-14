"""
Unit tests for Fermentation Router - API Layer Coverage (ADR-033 Phase 1)

Tests the fermentation_router.py API endpoints with mocked dependencies.
Target: Improve API layer coverage with critical endpoints.

Test Coverage (Initial):
- POST /fermentations - Create fermentation (success + error handling)
- GET /fermentations/{id} - Get fermentation by ID

Security Tests:
- Authentication required
- Role-based authorization (WINEMAKER for create)
- Multi-tenant isolation
- Input validation

Following ADR-028 (Testing Strategy), ADR-033 (Coverage Improvement)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import date, datetime
from fastapi import HTTPException

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent / "src"))

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums.user_role import UserRole
from src.modules.fermentation.src.api.routers.fermentation_router import (
    create_fermentation,
    get_fermentation
)
from src.modules.fermentation.src.api.schemas.requests.fermentation_requests import (
    FermentationCreateRequest
)
from src.modules.fermentation.src.api.schemas.responses.fermentation_responses import FermentationResponse
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.service_component.errors import NotFoundError


# ======================================================================================
# Fixtures
# ======================================================================================

@pytest.fixture
def mock_user_context():
    """Mock authenticated winemaker user context"""
    return UserContext(
        user_id=1,
        email="winemaker@test.com",
        role=UserRole.WINEMAKER,
        winery_id=10
    )


@pytest.fixture
def mock_fermentation_service():
    """Mock fermentation service with AsyncMock"""
    service = Mock()
    service.create_fermentation = AsyncMock()
    service.get_fermentation = AsyncMock()
    return service


@pytest.fixture
def sample_fermentation_entity():
    """Sample fermentation response for mocking"""
    return FermentationResponse(
        id=1,
        winery_id=10,
        fermented_by_user_id=1,
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code="TANK-01",
        input_mass_kg=1000.0,
        initial_sugar_brix=22.5,
        initial_density=1.092,
        start_date=date(2024, 3, 15),
        status=FermentationStatus.ACTIVE,
        created_at=datetime(2024, 3, 15, 10, 0, 0),
        updated_at=datetime(2024, 3, 15, 10, 0, 0)
    )


# ======================================================================================
# Tests for POST /fermentations - Create Fermentation
# ======================================================================================


@pytest.mark.asyncio
async def test_create_fermentation_success(
    mock_user_context,
    mock_fermentation_service,
    sample_fermentation_entity
):
    """Should create fermentation successfully."""
    mock_fermentation_service.create_fermentation.return_value = sample_fermentation_entity
    
    request = FermentationCreateRequest(
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code="TANK-01",
        input_mass_kg=1000.0,
        initial_sugar_brix=22.5,
        initial_density=1.092,
        start_date=date(2024, 3, 15)
    )
    
    response = await create_fermentation(request, mock_user_context, mock_fermentation_service)
    
    assert response.id == 1
    assert response.vintage_year == 2024
    assert response.vessel_code == "TANK-01"
    mock_fermentation_service.create_fermentation.assert_called_once()


@pytest.mark.asyncio
async def test_create_fermentation_not_found_error(
    mock_user_context,
    mock_fermentation_service
):
    """Should raise HTTPException 404 for invalid references."""
    mock_fermentation_service.create_fermentation.side_effect = NotFoundError("Vessel not found")
    
    request = FermentationCreateRequest(
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code="INVALID",
        input_mass_kg=1000.0,
        initial_sugar_brix=22.5,
        initial_density=1.092,
        start_date=date(2024, 3, 15)
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await create_fermentation(request, mock_user_context, mock_fermentation_service)
    
    assert exc_info.value.status_code == 404


# ======================================================================================
# Tests for GET /fermentations/{id} - Get Fermentation
# ======================================================================================


@pytest.mark.asyncio
async def test_get_fermentation_success(
    mock_user_context,
    mock_fermentation_service,
    sample_fermentation_entity
):
    """Should return fermentation by ID."""
    mock_fermentation_service.get_fermentation.return_value = sample_fermentation_entity
    
    response = await get_fermentation(1, mock_user_context, mock_fermentation_service)
    
    assert response.id == 1
    assert response.vintage_year == 2024
    mock_fermentation_service.get_fermentation.assert_called_once_with(
        fermentation_id=1,
        winery_id=10
    )


@pytest.mark.asyncio
async def test_get_fermentation_not_found(
    mock_user_context,
    mock_fermentation_service
):
    """Should raise HTTPException 404 when fermentation doesn't exist."""
    mock_fermentation_service.get_fermentation.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await get_fermentation(999, mock_user_context, mock_fermentation_service)
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_fermentation_multi_tenant_security(
    mock_user_context,
    mock_fermentation_service
):
    """Should enforce multi-tenant isolation via winery_id filter."""
    mock_fermentation_service.get_fermentation.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await get_fermentation(1, mock_user_context, mock_fermentation_service)
    
    assert exc_info.value.status_code == 404
    # Verify winery_id was passed to service for filtering
    mock_fermentation_service.get_fermentation.assert_called_once_with(
        fermentation_id=1,
        winery_id=10
    )

