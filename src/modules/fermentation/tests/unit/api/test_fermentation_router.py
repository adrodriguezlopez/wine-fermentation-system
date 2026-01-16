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
    get_fermentation,
    create_fermentation_with_blend,
    list_fermentations,
    update_fermentation,
    update_fermentation_status,
    complete_fermentation,
    delete_fermentation,
    validate_fermentation_data,
    get_fermentation_timeline,
    get_fermentation_statistics
)
from src.modules.fermentation.src.api.schemas.requests.fermentation_requests import (
    FermentationCreateRequest,
    FermentationWithBlendCreateRequest,
    LotSourceRequest,
    FermentationUpdateRequest,
    StatusUpdateRequest,
    CompleteFermentationRequest
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
    service.create_fermentation_with_blend = AsyncMock()
    service.get_fermentations_by_winery = AsyncMock()
    service.update_fermentation = AsyncMock()
    service.update_status = AsyncMock()
    service.complete_fermentation = AsyncMock()
    service.soft_delete = AsyncMock()
    service.validate_creation_data = Mock()  # Synchronous method
    return service


@pytest.fixture
def mock_sample_service():
    """Mock sample service for timeline and statistics"""
    service = Mock()
    service.get_samples_by_fermentation = AsyncMock()
    return service


@pytest.fixture
def mock_unit_of_work():
    """Mock UnitOfWork for blend creation"""
    return Mock()


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


# ======================================================================================
# Tests for POST /fermentations/blends - Create Fermentation with Blend
# ======================================================================================


@pytest.mark.asyncio
async def test_create_fermentation_with_blend_success(
    mock_user_context,
    mock_fermentation_service,
    mock_unit_of_work,
    sample_fermentation_entity
):
    """Should create fermentation with multiple lot sources successfully."""
    mock_fermentation_service.create_fermentation_with_blend.return_value = sample_fermentation_entity
    
    request = FermentationWithBlendCreateRequest(
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code="TANK-01",
        input_mass_kg=100.0,
        initial_sugar_brix=22.5,
        initial_density=1.092,
        start_date=date(2024, 3, 15),
        lot_sources=[
            LotSourceRequest(harvest_lot_id=1, mass_used_kg=60.0, notes="Block A"),
            LotSourceRequest(harvest_lot_id=2, mass_used_kg=40.0, notes="Block B")
        ]
    )
    
    response = await create_fermentation_with_blend(
        request, 
        mock_user_context, 
        mock_fermentation_service,
        mock_unit_of_work
    )
    
    assert response.id == 1
    assert response.vintage_year == 2024
    mock_fermentation_service.create_fermentation_with_blend.assert_called_once()


@pytest.mark.asyncio
async def test_create_fermentation_with_blend_not_found_error(
    mock_user_context,
    mock_fermentation_service,
    mock_unit_of_work
):
    """Should raise HTTPException 404 for invalid harvest lot."""
    mock_fermentation_service.create_fermentation_with_blend.side_effect = NotFoundError("Harvest lot not found")
    
    request = FermentationWithBlendCreateRequest(
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code="TANK-01",
        input_mass_kg=100.0,
        initial_sugar_brix=22.5,
        initial_density=1.092,
        start_date=date(2024, 3, 15),
        lot_sources=[
            LotSourceRequest(harvest_lot_id=999, mass_used_kg=100.0)
        ]
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await create_fermentation_with_blend(
            request, 
            mock_user_context, 
            mock_fermentation_service,
            mock_unit_of_work
        )
    
    assert exc_info.value.status_code == 404


# ======================================================================================
# Tests for GET /fermentations - List Fermentations
# ======================================================================================


@pytest.mark.asyncio
async def test_list_fermentations_success(
    mock_user_context,
    mock_fermentation_service,
    sample_fermentation_entity
):
    """Should return paginated list of fermentations."""
    mock_fermentation_service.get_fermentations_by_winery.return_value = [sample_fermentation_entity]
    
    response = await list_fermentations(
        mock_user_context, 
        mock_fermentation_service,
        page=1,
        size=20
    )
    
    assert response.total == 1
    assert len(response.items) == 1
    assert response.page == 1
    assert response.items[0].id == 1
    # Don't verify Query parameters, just that method was called
    mock_fermentation_service.get_fermentations_by_winery.assert_called_once()


@pytest.mark.asyncio
async def test_list_fermentations_with_filters(
    mock_user_context,
    mock_fermentation_service
):
    """Should apply status filter and include_completed flag."""
    mock_fermentation_service.get_fermentations_by_winery.return_value = []
    
    response = await list_fermentations(
        mock_user_context,
        mock_fermentation_service,
        page=1,
        size=20,
        status_filter="ACTIVE",
        include_completed=True
    )
    
    assert response.total == 0
    assert len(response.items) == 0
    mock_fermentation_service.get_fermentations_by_winery.assert_called_once_with(
        winery_id=10,
        status="ACTIVE",
        include_completed=True
    )


@pytest.mark.asyncio
async def test_list_fermentations_pagination(
    mock_user_context,
    mock_fermentation_service,
    sample_fermentation_entity
):
    """Should paginate results correctly."""
    # Create 5 fermentation entities
    fermentations = [sample_fermentation_entity for _ in range(5)]
    mock_fermentation_service.get_fermentations_by_winery.return_value = fermentations
    
    response = await list_fermentations(
        mock_user_context,
        mock_fermentation_service,
        page=2,
        size=2
    )
    
    assert response.total == 5
    assert len(response.items) == 2
    assert response.page == 2
    assert response.size == 2


# ======================================================================================
# Tests for PATCH /fermentations/{id} - Update Fermentation
# ======================================================================================


@pytest.mark.asyncio
async def test_update_fermentation_success(
    mock_user_context,
    mock_fermentation_service,
    sample_fermentation_entity
):
    """Should update fermentation successfully."""
    mock_fermentation_service.update_fermentation.return_value = sample_fermentation_entity
    
    request = FermentationUpdateRequest(
        yeast_strain="EC-1118 Updated",
        vessel_code="TANK-02"
    )
    
    response = await update_fermentation(
        fermentation_id=1,
        request=request,
        current_user=mock_user_context,
        fermentation_service=mock_fermentation_service
    )
    
    assert response.id == 1
    mock_fermentation_service.update_fermentation.assert_called_once()


@pytest.mark.asyncio
async def test_update_fermentation_not_found(
    mock_user_context,
    mock_fermentation_service
):
    """Should raise HTTPException 404 when fermentation doesn't exist."""
    mock_fermentation_service.update_fermentation.side_effect = NotFoundError("Fermentation not found")
    
    request = FermentationUpdateRequest(yeast_strain="EC-1118")
    
    with pytest.raises(HTTPException) as exc_info:
        await update_fermentation(
            fermentation_id=999,
            request=request,
            current_user=mock_user_context,
            fermentation_service=mock_fermentation_service
        )
    
    assert exc_info.value.status_code == 404


# ======================================================================================
# Tests for PATCH /fermentations/{id}/status - Update Status
# ======================================================================================


@pytest.mark.asyncio
async def test_update_fermentation_status_success(
    mock_user_context,
    mock_fermentation_service,
    sample_fermentation_entity
):
    """Should update fermentation status successfully."""
    completed_entity = sample_fermentation_entity
    completed_entity.status = FermentationStatus.COMPLETED
    mock_fermentation_service.update_status.return_value = completed_entity
    
    request = StatusUpdateRequest(status="COMPLETED")
    
    response = await update_fermentation_status(
        fermentation_id=1,
        request=request,
        current_user=mock_user_context,
        fermentation_service=mock_fermentation_service
    )
    
    assert response.status == FermentationStatus.COMPLETED
    mock_fermentation_service.update_status.assert_called_once()


@pytest.mark.asyncio
async def test_update_fermentation_status_not_found(
    mock_user_context,
    mock_fermentation_service
):
    """Should raise HTTPException 404 when fermentation doesn't exist."""
    mock_fermentation_service.update_status.side_effect = NotFoundError("Fermentation not found")
    
    request = StatusUpdateRequest(status="COMPLETED")
    
    with pytest.raises(HTTPException) as exc_info:
        await update_fermentation_status(
            fermentation_id=999,
            request=request,
            current_user=mock_user_context,
            fermentation_service=mock_fermentation_service
        )
    
    assert exc_info.value.status_code == 404


# ======================================================================================
# Tests for PATCH /fermentations/{id}/complete - Complete Fermentation
# ======================================================================================


@pytest.mark.asyncio
async def test_complete_fermentation_success(
    mock_user_context,
    mock_fermentation_service,
    sample_fermentation_entity
):
    """Should complete fermentation successfully."""
    completed_entity = sample_fermentation_entity
    completed_entity.status = FermentationStatus.COMPLETED
    mock_fermentation_service.complete_fermentation.return_value = completed_entity
    
    request = CompleteFermentationRequest(
        final_sugar_brix=0.5,
        final_mass_kg=950.0,
        notes="Fermentation completed successfully"
    )
    
    response = await complete_fermentation(
        fermentation_id=1,
        request=request,
        current_user=mock_user_context,
        fermentation_service=mock_fermentation_service
    )
    
    assert response.status == FermentationStatus.COMPLETED
    mock_fermentation_service.complete_fermentation.assert_called_once()


@pytest.mark.asyncio
async def test_complete_fermentation_not_found(
    mock_user_context,
    mock_fermentation_service
):
    """Should raise HTTPException 404 when fermentation doesn't exist."""
    mock_fermentation_service.complete_fermentation.side_effect = NotFoundError("Fermentation not found")
    
    request = CompleteFermentationRequest(
        final_sugar_brix=0.5,
        final_mass_kg=950.0
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await complete_fermentation(
            fermentation_id=999,
            request=request,
            current_user=mock_user_context,
            fermentation_service=mock_fermentation_service
        )
    
    assert exc_info.value.status_code == 404


# ======================================================================================
# Tests for DELETE /fermentations/{id} - Delete Fermentation
# ======================================================================================


@pytest.mark.asyncio
async def test_delete_fermentation_success(
    mock_user_context,
    mock_fermentation_service
):
    """Should delete fermentation successfully."""
    mock_fermentation_service.soft_delete.return_value = True
    
    response = await delete_fermentation(
        fermentation_id=1,
        current_user=mock_user_context,
        fermentation_service=mock_fermentation_service
    )
    
    assert response is None
    mock_fermentation_service.soft_delete.assert_called_once_with(
        fermentation_id=1,
        winery_id=10,
        user_id=1
    )


@pytest.mark.asyncio
async def test_delete_fermentation_not_found(
    mock_user_context,
    mock_fermentation_service
):
    """Should raise HTTPException 404 when fermentation doesn't exist."""
    mock_fermentation_service.soft_delete.return_value = False
    
    with pytest.raises(HTTPException) as exc_info:
        await delete_fermentation(
            fermentation_id=999,
            current_user=mock_user_context,
            fermentation_service=mock_fermentation_service
        )
    
    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()


# ======================================================================================
# Validate Endpoint Tests (Dry-Run Validation)
# ======================================================================================

@pytest.mark.asyncio
async def test_validate_fermentation_success(
    mock_user_context,
    mock_fermentation_service
):
    """Should return valid=True when data passes validation."""
    # Mock the validation result as a simple object with is_valid and errors
    class MockValidationResult:
        is_valid = True
        errors = []
    
    mock_fermentation_service.validate_creation_data.return_value = MockValidationResult()
    
    request = FermentationCreateRequest(
        harvest_lot_id=100,
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code="V-101",
        input_mass_kg=1000.0,
        initial_sugar_brix=24.5,
        initial_density=1.100,
        start_date=date(2024, 9, 15)
    )
    
    response = await validate_fermentation_data(
        request=request,
        current_user=mock_user_context,
        fermentation_service=mock_fermentation_service
    )
    
    assert response.valid is True
    assert len(response.errors) == 0


@pytest.mark.asyncio
async def test_validate_fermentation_with_errors(
    mock_user_context,
    mock_fermentation_service
):
    """Should return valid=False with error details when validation fails."""
    # Mock the validation result with errors
    class MockValidationError:
        def __init__(self, field, message):
            self.field = field
            self.message = message
    
    class MockValidationResult:
        is_valid = False
        errors = [
            MockValidationError("initial_sugar_brix", "Sugar level too low"),
            MockValidationError("vessel_code", "Vessel not available")
        ]
    
    mock_fermentation_service.validate_creation_data.return_value = MockValidationResult()
    
    request = FermentationCreateRequest(
        harvest_lot_id=100,
        vintage_year=2024,
        yeast_strain="EC-1118",
        vessel_code="V-999",
        input_mass_kg=1000.0,
        initial_sugar_brix=10.0,  # Too low
        initial_density=1.050,
        start_date=date(2024, 9, 15)
    )
    
    response = await validate_fermentation_data(
        request=request,
        current_user=mock_user_context,
        fermentation_service=mock_fermentation_service
    )
    
    assert response.valid is False
    assert len(response.errors) == 2
    assert response.errors[0].field == "initial_sugar_brix"
    assert response.errors[1].field == "vessel_code"


# ======================================================================================
# Timeline Endpoint Tests
# ======================================================================================

@pytest.mark.asyncio
async def test_get_fermentation_timeline_success(
    mock_user_context,
    mock_fermentation_service,
    mock_sample_service,
    sample_fermentation_entity
):
    """Should return timeline with fermentation and all samples."""
    mock_fermentation_service.get_fermentation.return_value = sample_fermentation_entity
    
    # Create mock samples as simple objects
    class MockSample:
        def __init__(self, id, sample_type, value, recorded_at):
            self.id = id
            self.fermentation_id = 1
            self.sample_type = sample_type
            self.value = value
            self.recorded_at = recorded_at
            self.recorded_by_user_id = 1
            self.winery_id = 10
            self.units = "°Brix" if sample_type == "sugar" else "°C"
            self.created_at = recorded_at
            self.updated_at = recorded_at
    
    samples = [
        MockSample(1, "sugar", 22.0, datetime(2024, 9, 16, 10, 0)),
        MockSample(2, "temperature", 18.5, datetime(2024, 9, 17, 10, 0)),
        MockSample(3, "sugar", 18.0, datetime(2024, 9, 18, 10, 0))
    ]
    mock_sample_service.get_samples_by_fermentation.return_value = samples
    
    response = await get_fermentation_timeline(
        fermentation_id=1,
        current_user=mock_user_context,
        fermentation_service=mock_fermentation_service,
        sample_service=mock_sample_service
    )
    
    assert response.fermentation.id == 1
    assert response.sample_count == 3
    assert len(response.samples) == 3
    assert response.first_sample_date == datetime(2024, 9, 16, 10, 0)
    assert response.last_sample_date == datetime(2024, 9, 18, 10, 0)


@pytest.mark.asyncio
async def test_get_fermentation_timeline_not_found(
    mock_user_context,
    mock_fermentation_service,
    mock_sample_service
):
    """Should raise HTTPException 404 when fermentation doesn't exist."""
    mock_fermentation_service.get_fermentation.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await get_fermentation_timeline(
            fermentation_id=999,
            current_user=mock_user_context,
            fermentation_service=mock_fermentation_service,
            sample_service=mock_sample_service
        )
    
    assert exc_info.value.status_code == 404


# ======================================================================================
# Statistics Endpoint Tests
# ======================================================================================

@pytest.mark.asyncio
async def test_get_fermentation_statistics_success(
    mock_user_context,
    mock_fermentation_service,
    mock_sample_service,
    sample_fermentation_entity
):
    """Should return calculated statistics with all metrics."""
    mock_fermentation_service.get_fermentation.return_value = sample_fermentation_entity
    
    # Create mock samples with different types
    class MockSample:
        def __init__(self, id, sample_type, value, recorded_at):
            self.id = id
            self.fermentation_id = 1
            self.sample_type = sample_type
            self.value = value
            self.recorded_at = recorded_at
            self.recorded_by_user_id = 1
            self.winery_id = 10
            self.units = "°Brix" if sample_type == "sugar" else "°C"
            self.created_at = recorded_at
            self.updated_at = recorded_at
    
    samples = [
        MockSample(1, "sugar", 22.0, datetime(2024, 9, 16, 10, 0)),
        MockSample(2, "temperature", 18.5, datetime(2024, 9, 17, 10, 0)),
        MockSample(3, "sugar", 15.0, datetime(2024, 9, 20, 10, 0))
    ]
    mock_sample_service.get_samples_by_fermentation.return_value = samples
    
    response = await get_fermentation_statistics(
        fermentation_id=1,
        current_user=mock_user_context,
        fermentation_service=mock_fermentation_service,
        sample_service=mock_sample_service
    )
    
    assert response.total_samples == 3
    assert response.duration_days is not None
    assert response.initial_sugar == 22.5  # From fermentation.initial_sugar_brix
    assert response.latest_sugar == 15.0   # Last SUGAR sample
    assert response.sugar_drop == 7.5  # 22.5 - 15.0


@pytest.mark.asyncio
async def test_get_fermentation_statistics_not_found(
    mock_user_context,
    mock_fermentation_service,
    mock_sample_service
):
    """Should raise HTTPException 404 when fermentation doesn't exist."""
    mock_fermentation_service.get_fermentation.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await get_fermentation_statistics(
            fermentation_id=999,
            current_user=mock_user_context,
            fermentation_service=mock_fermentation_service,
            sample_service=mock_sample_service
        )
    
    assert exc_info.value.status_code == 404
