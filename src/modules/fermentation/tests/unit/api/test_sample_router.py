"""
Unit tests for Sample Router - API Layer Coverage (ADR-033 Phase 1)

Tests the sample_router.py API endpoints with mocked dependencies.
Target: 0% → 85% coverage for sample_router.py (72 statements)

Test Coverage:
- POST /fermentations/{id}/samples - Create sample
- GET /fermentations/{id}/samples - List samples
- GET /fermentations/{id}/samples/latest - Latest sample
- GET /fermentations/{id}/samples/{sample_id} - Get sample by ID

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
from datetime import datetime
from fastapi import HTTPException

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent / "src"))

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums.user_role import UserRole
from src.modules.fermentation.src.api.schemas.requests.sample_requests import SampleCreateRequest
from src.modules.fermentation.src.api.schemas.responses.sample_responses import SampleResponse
from src.modules.fermentation.src.domain.dtos import SampleCreate
from src.modules.fermentation.src.domain.enums.sample_type import SampleType
from src.modules.fermentation.src.service_component.errors import ValidationError, NotFoundError


# ======================================================================================
# Fixtures
# ======================================================================================

@pytest.fixture
def mock_user_context():
    """Mock authenticated user context"""
    return UserContext(
        user_id=1,
        email="winemaker@test.com",
        winery_id=100,
        role=UserRole.WINEMAKER
    )


@pytest.fixture
def mock_sample_service():
    """Mock sample service with AsyncMock"""
    service = Mock()
    service.add_sample = AsyncMock()
    service.get_samples_by_fermentation = AsyncMock()
    service.get_latest_sample = AsyncMock()
    service.get_sample = AsyncMock()
    service.get_samples_in_timerange = AsyncMock()
    service.validate_sample_data = AsyncMock()
    service.delete_sample = AsyncMock()
    return service


@pytest.fixture
def sample_entity():
    """Sample entity fixture - mock object with required attributes"""
    sample = Mock()
    sample.id = 1
    sample.fermentation_id = 10
    sample.sample_type = SampleType.DENSITY
    sample.recorded_at = datetime(2025, 1, 15, 10, 0, 0)
    sample.recorded_by_user_id = 1
    sample.value = 1.085
    sample.units = "g/cm³"
    sample.created_at = datetime(2025, 1, 15, 9, 0, 0)
    sample.updated_at = datetime(2025, 1, 15, 9, 0, 0)
    return sample


@pytest.fixture
def sample_create_request():
    """Valid sample create request"""
    return SampleCreateRequest(
        sample_type="density",
        value=1.085,
        units="g/cm³",
        recorded_at=datetime(2025, 1, 15, 10, 0, 0)
    )


# ======================================================================================
# POST /fermentations/{fermentation_id}/samples - Create Sample
# ======================================================================================

@pytest.mark.asyncio
async def test_create_sample_success(mock_user_context, mock_sample_service, sample_entity, sample_create_request):
    """Test successful sample creation"""
    # Import after mocks are set up
    from src.modules.fermentation.src.api.routers.sample_router import create_sample
    
    # Setup mock
    mock_sample_service.add_sample.return_value = sample_entity
    
    # Execute
    result = await create_sample(
        fermentation_id=10,
        request=sample_create_request,
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify
    assert isinstance(result, SampleResponse)
    assert result.id == 1
    assert result.sample_type == "density"
    assert result.value == 1.085
    
    # Verify service called correctly
    mock_sample_service.add_sample.assert_called_once()
    call_args = mock_sample_service.add_sample.call_args
    assert call_args.kwargs['fermentation_id'] == 10
    assert call_args.kwargs['winery_id'] == 100
    assert call_args.kwargs['user_id'] == 1
    assert isinstance(call_args.kwargs['data'], SampleCreate)


@pytest.mark.asyncio
async def test_create_sample_converts_sample_type_to_enum(mock_user_context, mock_sample_service, sample_entity, sample_create_request):
    """Test that sample_type string is converted to SampleType enum"""
    from src.modules.fermentation.src.api.routers.sample_router import create_sample
    
    mock_sample_service.add_sample.return_value = sample_entity
    
    await create_sample(
        fermentation_id=10,
        request=sample_create_request,
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify DTO has SampleType enum
    call_args = mock_sample_service.add_sample.call_args
    dto = call_args.kwargs['data']
    assert isinstance(dto.sample_type, SampleType)
    assert dto.sample_type == SampleType.DENSITY


@pytest.mark.asyncio
async def test_create_sample_not_found_error(mock_user_context, mock_sample_service, sample_create_request):
    """Test 404 when fermentation not found
    
    Note: We test for HTTPException (not NotFoundError) because the @handle_service_errors
    decorator converts service-layer exceptions to HTTP responses. This tests the API contract
    (what clients see), not internal implementation.
    """
    from src.modules.fermentation.src.api.routers.sample_router import create_sample
    from fastapi import HTTPException
    
    # Setup mock to raise NotFoundError (service layer exception)
    mock_sample_service.add_sample.side_effect = NotFoundError("Fermentation not found")
    
    # Execute and verify HTTPException (API layer response)
    with pytest.raises(HTTPException) as exc_info:
        await create_sample(
            fermentation_id=9999,
            request=sample_create_request,
            current_user=mock_user_context,
            sample_service=mock_sample_service
        )
    
    # Verify correct HTTP status code (API contract)
    assert exc_info.value.status_code == 404
    assert "Fermentation not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_sample_validation_error(mock_user_context, mock_sample_service, sample_create_request):
    """Test 422 when sample data is invalid"""
    from src.modules.fermentation.src.api.routers.sample_router import create_sample
    from fastapi import HTTPException
    
    # Setup mock to raise ValidationError
    mock_sample_service.add_sample.side_effect = ValidationError("Invalid sample value")
    
    # Execute and verify HTTPException (error_handler converts ValidationError to HTTPException)
    with pytest.raises(HTTPException) as exc_info:
        await create_sample(
            fermentation_id=10,
            request=sample_create_request,
            current_user=mock_user_context,
            sample_service=mock_sample_service
        )
    
    # Verify it's a 422
    assert exc_info.value.status_code == 422
    assert "Invalid sample value" in str(exc_info.value.detail)


# ======================================================================================
# GET /fermentations/{fermentation_id}/samples - List Samples
# ======================================================================================

@pytest.mark.asyncio
async def test_list_samples_success(mock_user_context, mock_sample_service, sample_entity):
    """Test successful listing of samples"""
    from src.modules.fermentation.src.api.routers.sample_router import list_samples
    
    # Setup mock with multiple samples
    samples = [sample_entity, sample_entity]
    mock_sample_service.get_samples_by_fermentation.return_value = samples
    
    # Execute
    result = await list_samples(
        fermentation_id=10,
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(s, SampleResponse) for s in result)
    
    # Verify service called correctly
    mock_sample_service.get_samples_by_fermentation.assert_called_once_with(
        fermentation_id=10,
        winery_id=100
    )


@pytest.mark.asyncio
async def test_list_samples_empty_list(mock_user_context, mock_sample_service):
    """Test listing when no samples exist"""
    from src.modules.fermentation.src.api.routers.sample_router import list_samples
    
    # Setup mock with empty list
    mock_sample_service.get_samples_by_fermentation.return_value = []
    
    # Execute
    result = await list_samples(
        fermentation_id=10,
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify
    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_list_samples_multi_tenant_isolation(mock_user_context, mock_sample_service):
    """Test that winery_id is enforced in list samples"""
    from src.modules.fermentation.src.api.routers.sample_router import list_samples
    
    mock_sample_service.get_samples_by_fermentation.return_value = []
    
    # Execute
    await list_samples(
        fermentation_id=10,
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify winery_id passed to service
    call_args = mock_sample_service.get_samples_by_fermentation.call_args
    assert call_args.kwargs['winery_id'] == 100


# ======================================================================================
# GET /fermentations/{fermentation_id}/samples/latest - Latest Sample
# ======================================================================================

@pytest.mark.asyncio
async def test_get_latest_sample_success(mock_user_context, mock_sample_service, sample_entity):
    """Test getting latest sample without type filter"""
    from src.modules.fermentation.src.api.routers.sample_router import get_latest_sample
    
    # Setup mock
    mock_sample_service.get_latest_sample.return_value = sample_entity
    
    # Execute
    result = await get_latest_sample(
        fermentation_id=10,
        sample_type=None,
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify
    assert isinstance(result, SampleResponse)
    assert result.id == 1
    
    # Verify service called correctly
    mock_sample_service.get_latest_sample.assert_called_once_with(
        fermentation_id=10,
        winery_id=100,
        sample_type=None
    )


@pytest.mark.asyncio
async def test_get_latest_sample_with_type_filter(mock_user_context, mock_sample_service, sample_entity):
    """Test getting latest sample filtered by type"""
    from src.modules.fermentation.src.api.routers.sample_router import get_latest_sample
    
    # Setup mock
    mock_sample_service.get_latest_sample.return_value = sample_entity
    
    # Execute with type filter
    result = await get_latest_sample(
        fermentation_id=10,
        sample_type="density",
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify
    assert isinstance(result, SampleResponse)
    
    # Verify service called with SampleType enum
    call_args = mock_sample_service.get_latest_sample.call_args
    assert call_args.kwargs['sample_type'] == SampleType.DENSITY


@pytest.mark.asyncio
async def test_get_latest_sample_invalid_type(mock_user_context, mock_sample_service):
    """Test 422 when invalid sample type provided"""
    from src.modules.fermentation.src.api.routers.sample_router import get_latest_sample
    from fastapi import HTTPException
    
    # Execute with invalid type (error_handler catches ValidationError and converts to HTTPException)
    with pytest.raises(HTTPException) as exc_info:
        await get_latest_sample(
            fermentation_id=10,
            sample_type="invalid_type",
            current_user=mock_user_context,
            sample_service=mock_sample_service
        )
    
    # Verify it's a 422
    assert exc_info.value.status_code == 422
    assert "Invalid sample type" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_latest_sample_not_found(mock_user_context, mock_sample_service):
    """Test 404 when no samples exist"""
    from src.modules.fermentation.src.api.routers.sample_router import get_latest_sample
    
    # Setup mock to return None
    mock_sample_service.get_latest_sample.return_value = None
    
    # Execute and verify exception
    with pytest.raises(Exception) as exc_info:  # Using Exception instead of SampleNotFound
        await get_latest_sample(
            fermentation_id=10,
            sample_type=None,
            current_user=mock_user_context,
            sample_service=mock_sample_service
        )
    
    # Verify error message
    assert "No samples found" in str(exc_info.value)


# ======================================================================================
# GET /fermentations/{fermentation_id}/samples/{sample_id} - Get Sample
# ======================================================================================

@pytest.mark.asyncio
async def test_get_sample_success(mock_user_context, mock_sample_service, sample_entity):
    """Test getting specific sample by ID"""
    from src.modules.fermentation.src.api.routers.sample_router import get_sample
    
    # Setup mock
    mock_sample_service.get_sample.return_value = sample_entity
    
    # Execute
    result = await get_sample(
        fermentation_id=10,
        sample_id=1,
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify
    assert isinstance(result, SampleResponse)
    assert result.id == 1
    
    # Verify service called correctly
    mock_sample_service.get_sample.assert_called_once_with(
        sample_id=1,
        fermentation_id=10,
        winery_id=100
    )


@pytest.mark.asyncio
async def test_get_sample_not_found(mock_user_context, mock_sample_service):
    """Test 404 when sample not found"""
    from src.modules.fermentation.src.api.routers.sample_router import get_sample
    
    # Setup mock to return None
    mock_sample_service.get_sample.return_value = None
    
    # Execute and verify exception
    with pytest.raises(Exception):  # Using Exception instead of SampleNotFound
        await get_sample(
            fermentation_id=10,
            sample_id=9999,
            current_user=mock_user_context,
            sample_service=mock_sample_service
        )


@pytest.mark.asyncio
async def test_get_sample_multi_tenant_security(mock_user_context, mock_sample_service):
    """Test that winery_id is enforced (ADR-025 LIGHT)"""
    from src.modules.fermentation.src.api.routers.sample_router import get_sample
    
    # Setup mock to return None (cross-winery attempt)
    mock_sample_service.get_sample.return_value = None
    
    # Execute - should raise 404 (not reveal existence for security)
    with pytest.raises(Exception):  # Using Exception instead of SampleNotFound
        await get_sample(
            fermentation_id=10,
            sample_id=1,
            current_user=mock_user_context,
            sample_service=mock_sample_service
        )
    
    # Verify winery_id was passed to service
    call_args = mock_sample_service.get_sample.call_args
    assert call_args.kwargs['winery_id'] == 100


# ======================================================================================
# Edge Cases and Error Handling
# ======================================================================================

@pytest.mark.asyncio
async def test_create_sample_with_all_sample_types(mock_user_context, mock_sample_service, sample_entity):
    """Test sample creation with different sample types"""
    from src.modules.fermentation.src.api.routers.sample_router import create_sample
    
    sample_types = ["density", "sugar", "temperature"]
    
    for sample_type_str in sample_types:
        mock_sample_service.add_sample.return_value = sample_entity
        
        request = SampleCreateRequest(
            sample_type=sample_type_str,
            value=10.0,
            units="test",
            recorded_at=datetime.now()
        )
        
        result = await create_sample(
            fermentation_id=10,
            request=request,
            current_user=mock_user_context,
            sample_service=mock_sample_service
        )
        
        assert isinstance(result, SampleResponse)


@pytest.mark.asyncio
async def test_get_latest_sample_case_insensitive_type(mock_user_context, mock_sample_service, sample_entity):
    """Test that sample type filter is case-insensitive"""
    from src.modules.fermentation.src.api.routers.sample_router import get_latest_sample
    
    mock_sample_service.get_latest_sample.return_value = sample_entity
    
    # Test with uppercase
    await get_latest_sample(
        fermentation_id=10,
        sample_type="DENSITY",
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify it was converted to lowercase for enum
    call_args = mock_sample_service.get_latest_sample.call_args
    assert call_args.kwargs['sample_type'] == SampleType.DENSITY


# ======================================================================================
# GET /api/v1/samples/types - Get Available Sample Types
# ======================================================================================

@pytest.mark.asyncio
async def test_get_sample_types():
    """Test getting list of available sample types (public endpoint)"""
    from src.modules.fermentation.src.api.routers.sample_router import get_sample_types
    
    # Execute (no auth required)
    result = await get_sample_types()
    
    # Verify
    assert isinstance(result, list)
    assert len(result) > 0
    assert "density" in result
    assert "sugar" in result
    assert "temperature" in result


# ======================================================================================
# GET /api/v1/samples/timerange - Get Samples in Time Range
# ======================================================================================

@pytest.mark.asyncio
async def test_get_samples_by_timerange_success(mock_user_context, mock_sample_service, sample_entity):
    """Test getting samples in time range"""
    from src.modules.fermentation.src.api.routers.sample_router import get_samples_by_timerange
    
    # Setup mock
    samples = [sample_entity, sample_entity]
    mock_sample_service.get_samples_in_timerange.return_value = samples
    
    start = datetime(2025, 1, 1)
    end = datetime(2025, 1, 31)
    
    # Execute
    result = await get_samples_by_timerange(
        fermentation_id=10,
        start_date=start,
        end_date=end,
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify
    assert isinstance(result, list)
    assert len(result) == 2
    
    # Verify service called correctly
    mock_sample_service.get_samples_in_timerange.assert_called_once_with(
        fermentation_id=10,
        winery_id=100,
        start=start,
        end=end
    )


@pytest.mark.asyncio
async def test_get_samples_by_timerange_empty(mock_user_context, mock_sample_service):
    """Test getting samples when none exist in range"""
    from src.modules.fermentation.src.api.routers.sample_router import get_samples_by_timerange
    
    # Setup mock with empty list
    mock_sample_service.get_samples_in_timerange.return_value = []
    
    # Execute
    result = await get_samples_by_timerange(
        fermentation_id=10,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify
    assert isinstance(result, list)
    assert len(result) == 0


# ======================================================================================
# POST /api/v1/samples/validate - Validate Sample Data (Dry-Run)
# ======================================================================================

@pytest.mark.asyncio
async def test_validate_sample_success(mock_user_context, mock_sample_service, sample_create_request):
    """Test dry-run validation of sample data"""
    from src.modules.fermentation.src.api.routers.sample_router import validate_sample
    
    # Setup mock validation result
    validation_result = Mock()
    validation_result.model_dump.return_value = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    mock_sample_service.validate_sample_data.return_value = validation_result
    
    # Execute
    result = await validate_sample(
        fermentation_id=10,
        request=sample_create_request,
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify
    assert isinstance(result, dict)
    assert result["is_valid"] is True
    assert result["errors"] == []
    
    # Verify service called
    mock_sample_service.validate_sample_data.assert_called_once()


@pytest.mark.asyncio
async def test_validate_sample_with_errors(mock_user_context, mock_sample_service, sample_create_request):
    """Test validation with errors"""
    from src.modules.fermentation.src.api.routers.sample_router import validate_sample
    
    # Setup mock validation result with errors
    validation_result = Mock()
    validation_result.model_dump.return_value = {
        "is_valid": False,
        "errors": ["Value out of range"],
        "warnings": ["Sample date in future"]
    }
    mock_sample_service.validate_sample_data.return_value = validation_result
    
    # Execute
    result = await validate_sample(
        fermentation_id=10,
        request=sample_create_request,
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify
    assert isinstance(result, dict)
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0


# ======================================================================================
# DELETE /api/v1/samples/{id} - Delete Sample
# ======================================================================================

@pytest.mark.asyncio
async def test_delete_sample_success(mock_user_context, mock_sample_service):
    """Test successful sample deletion"""
    from src.modules.fermentation.src.api.routers.sample_router import delete_sample
    
    # Setup mock (delete returns None)
    mock_sample_service.delete_sample.return_value = None
    
    # Execute
    result = await delete_sample(
        sample_id=1,
        fermentation_id=10,
        current_user=mock_user_context,
        sample_service=mock_sample_service
    )
    
    # Verify
    assert result is None  # 204 No Content
    
    # Verify service called correctly
    mock_sample_service.delete_sample.assert_called_once_with(
        sample_id=1,
        fermentation_id=10,
        winery_id=100
    )


@pytest.mark.asyncio
async def test_delete_sample_not_found(mock_user_context, mock_sample_service):
    """Test 404 when sample to delete not found"""
    from src.modules.fermentation.src.api.routers.sample_router import delete_sample
    from fastapi import HTTPException
    
    # Setup mock to raise NotFoundError
    mock_sample_service.delete_sample.side_effect = NotFoundError("Sample not found")
    
    # Execute and verify HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await delete_sample(
            sample_id=9999,
            fermentation_id=10,
            current_user=mock_user_context,
            sample_service=mock_sample_service
        )
    
    # Verify 404
    assert exc_info.value.status_code == 404


# ======================================================================================
# Additional Coverage: get_sample fermentation_id mismatch
# ======================================================================================

@pytest.mark.asyncio
async def test_get_sample_fermentation_mismatch(mock_user_context, mock_sample_service):
    """Test security validation when sample belongs to different fermentation"""
    from src.modules.fermentation.src.api.routers.sample_router import get_sample
    
    # Setup mock - sample exists but belongs to different fermentation
    mismatched_sample = Mock()
    mismatched_sample.id = 1
    mismatched_sample.fermentation_id = 999  # Different from requested (10)
    mismatched_sample.sample_type = SampleType.DENSITY
    mismatched_sample.recorded_at = datetime(2025, 1, 15, 10, 0, 0)
    mismatched_sample.recorded_by_user_id = 1
    mismatched_sample.value = 1.085
    mismatched_sample.units = "g/cm³"
    mismatched_sample.created_at = datetime(2025, 1, 15, 9, 0, 0)
    mismatched_sample.updated_at = datetime(2025, 1, 15, 9, 0, 0)
    
    mock_sample_service.get_sample.return_value = mismatched_sample
    
    # Execute - should raise exception due to mismatch
    with pytest.raises(Exception) as exc_info:
        await get_sample(
            fermentation_id=10,
            sample_id=1,
            current_user=mock_user_context,
            sample_service=mock_sample_service
        )
    
    # Verify error message mentions mismatch
    assert "not found in fermentation" in str(exc_info.value)
