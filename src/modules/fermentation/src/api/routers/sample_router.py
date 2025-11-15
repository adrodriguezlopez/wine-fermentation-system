"""
Sample Router - REST API endpoints for sample management

Implements CRUD operations for fermentation samples with:
- JWT authentication
- Role-based authorization
- Multi-tenancy enforcement (via fermentation ownership)
- Request/response validation

Sample endpoints are nested under fermentation endpoints:
- POST /fermentations/{id}/samples
- GET /fermentations/{id}/samples
- GET /fermentations/{id}/samples/{sample_id}
- GET /fermentations/{id}/samples/latest

Following ADR-006 API Layer Design
"""

from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from typing import Annotated, List, Optional
from datetime import datetime

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker, get_current_user

from src.modules.fermentation.src.api.schemas.requests.sample_requests import (
    SampleCreateRequest
)
from src.modules.fermentation.src.api.schemas.responses.sample_responses import (
    SampleResponse
)
from src.modules.fermentation.src.api.error_handlers import handle_service_errors
from src.modules.fermentation.src.service_component.interfaces.sample_service_interface import ISampleService
from src.modules.fermentation.src.domain.dtos import SampleCreate
from src.modules.fermentation.src.domain.enums.sample_type import SampleType
from src.modules.fermentation.src.service_component.errors import (
    ValidationError,
    NotFoundError
)

# Import dependencies
from src.modules.fermentation.src.api.dependencies import get_sample_service

router = APIRouter(prefix="/api/v1/fermentations", tags=["samples"])


# ======================================================================================
# POST /fermentations/{fermentation_id}/samples - Create Sample
# ======================================================================================

@router.post(
    "/{fermentation_id}/samples",
    response_model=SampleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a sample measurement to a fermentation",
    description="Creates a new sample measurement for the specified fermentation. Requires WINEMAKER or ADMIN role."
)
@handle_service_errors
async def create_sample(
    fermentation_id: int = Path(..., gt=0, description="ID of the fermentation"),
    request: SampleCreateRequest = ...,
    current_user: Annotated[UserContext, Depends(require_winemaker)] = None,
    sample_service: Annotated[ISampleService, Depends(get_sample_service)] = None
) -> SampleResponse:
    """
    Add a new sample measurement to a fermentation.
    
    Args:
        fermentation_id: ID of the fermentation
        request: Sample data (validated by Pydantic)
        current_user: Authenticated user context
        sample_service: Sample service instance
        
    Returns:
        SampleResponse: Created sample with ID and timestamps
    
    Raises:
        HTTP 403: Insufficient permissions (not WINEMAKER or ADMIN)
        HTTP 404: Fermentation not found
        HTTP 422: Invalid sample data
        HTTP 401: Not authenticated
    """
    # Convert API request to service DTO
    sample_dto = SampleCreate(
        sample_type=SampleType(request.sample_type),  # Convert string to enum
        value=request.value,
        units=request.units,
        recorded_at=request.recorded_at
    )
    
    # Call service to create sample
    sample = await sample_service.add_sample(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id,
        user_id=current_user.user_id,
        data=sample_dto
    )
    
    # Convert entity to response DTO
    return SampleResponse.from_entity(sample)


# ======================================================================================
# GET /fermentations/{fermentation_id}/samples - List Samples
# ======================================================================================

@router.get(
    "/{fermentation_id}/samples",
    response_model=List[SampleResponse],
    status_code=status.HTTP_200_OK,
    summary="List all samples for a fermentation",
    description="Retrieves all samples for the specified fermentation in chronological order."
)
async def list_samples(
    fermentation_id: int = Path(..., gt=0, description="ID of the fermentation"),
    current_user: Annotated[UserContext, Depends(get_current_user)] = None,
    sample_service: Annotated[ISampleService, Depends(get_sample_service)] = None
) -> List[SampleResponse]:
    """
    List all samples for a fermentation.
    
    Args:
        fermentation_id: ID of the fermentation
        current_user: Authenticated user context
        sample_service: Sample service instance
        
    Returns:
        List[SampleResponse]: Samples in chronological order
    
    Raises:
        HTTP 404: Fermentation not found
        HTTP 401: Not authenticated
    """
    try:
        samples = await sample_service.get_samples_by_fermentation(
            fermentation_id=fermentation_id,
            winery_id=current_user.winery_id
        )
        
        return [SampleResponse.from_entity(s) for s in samples]
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# ======================================================================================
# GET /fermentations/{fermentation_id}/samples/latest - Latest Sample (MUST BE BEFORE /{sample_id})
# ======================================================================================

@router.get(
    "/{fermentation_id}/samples/latest",
    response_model=SampleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the latest sample",
    description="Retrieves the most recent sample for the fermentation, optionally filtered by type."
)
async def get_latest_sample(
    fermentation_id: int = Path(..., gt=0, description="ID of the fermentation"),
    sample_type: Optional[str] = Query(None, description="Filter by sample type (e.g., 'sugar', 'temperature')"),
    current_user: Annotated[UserContext, Depends(get_current_user)] = None,
    sample_service: Annotated[ISampleService, Depends(get_sample_service)] = None
) -> SampleResponse:
    """
    Get the latest sample for a fermentation.
    
    Args:
        fermentation_id: ID of the fermentation
        sample_type: Optional filter by sample type
        current_user: Authenticated user context
        sample_service: Sample service instance
        
    Returns:
        SampleResponse: Latest sample data
    
    Raises:
        HTTP 404: No samples found or fermentation not found
        HTTP 401: Not authenticated
    """
    try:
        # Convert string to SampleType enum if provided
        from src.modules.fermentation.src.domain.enums.sample_type import SampleType
        sample_type_enum = None
        if sample_type:
            try:
                sample_type_enum = SampleType(sample_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid sample type: {sample_type}"
                )
        
        sample = await sample_service.get_latest_sample(
            fermentation_id=fermentation_id,
            winery_id=current_user.winery_id,
            sample_type=sample_type_enum
        )
        
        if sample is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No samples found"
            )
        
        return SampleResponse.from_entity(sample)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# ======================================================================================
# GET /fermentations/{fermentation_id}/samples/{sample_id} - Get Sample
# ======================================================================================

@router.get(
    "/{fermentation_id}/samples/{sample_id}",
    response_model=SampleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific sample",
    description="Retrieves a specific sample by ID."
)
async def get_sample(
    fermentation_id: int = Path(..., gt=0, description="ID of the fermentation"),
    sample_id: int = Path(..., gt=0, description="ID of the sample"),
    current_user: Annotated[UserContext, Depends(get_current_user)] = None,
    sample_service: Annotated[ISampleService, Depends(get_sample_service)] = None
) -> SampleResponse:
    """
    Get a specific sample by ID.
    
    Args:
        fermentation_id: ID of the fermentation
        sample_id: ID of the sample
        current_user: Authenticated user context
        sample_service: Sample service instance
        
    Returns:
        SampleResponse: Sample data
    
    Raises:
        HTTP 404: Sample or fermentation not found
        HTTP 401: Not authenticated
    """
    try:
        sample = await sample_service.get_sample(
            sample_id=sample_id,
            fermentation_id=fermentation_id,
            winery_id=current_user.winery_id
        )
        
        if sample is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample with id {sample_id} not found"
        )
        
        return SampleResponse.from_entity(sample)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# ======================================================================================
# GET /api/v1/samples/types - Get Available Sample Types
# ======================================================================================

# Create a separate router for non-nested sample endpoints
samples_router = APIRouter(prefix="/api/v1/samples", tags=["samples"])

@samples_router.get(
    "/types",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get available sample types",
    description="Returns a list of available sample types that can be recorded."
)
async def get_sample_types() -> List[str]:
    """
    Get available sample types.
    
    Returns a list of valid sample type values that can be used
    when creating samples. No authentication required (public endpoint).
    
    Returns:
        List[str]: List of sample type values (e.g., ["sugar", "temperature", "density"])
    """
    return [sample_type.value for sample_type in SampleType]


# ======================================================================================
# GET /api/v1/samples/timerange - Get Samples in Time Range
# ======================================================================================

@samples_router.get(
    "/timerange",
    response_model=List[SampleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get samples in time range",
    description="Retrieves all samples within a specific time range for a fermentation."
)
async def get_samples_by_timerange(
    fermentation_id: int = Query(..., gt=0, description="ID of the fermentation"),
    start_date: datetime = Query(..., description="Start of time range (ISO 8601 format)"),
    end_date: datetime = Query(..., description="End of time range (ISO 8601 format)"),
    current_user: Annotated[UserContext, Depends(get_current_user)] = None,
    sample_service: Annotated[ISampleService, Depends(get_sample_service)] = None
) -> List[SampleResponse]:
    """
    Get samples within a time range for a fermentation.
    
    Retrieves all samples recorded between start_date and end_date,
    ordered chronologically. Useful for analyzing trends over specific periods.
    
    Args:
        fermentation_id: ID of the fermentation
        start_date: Start of time range (inclusive)
        end_date: End of time range (inclusive)
        current_user: Authenticated user context
        sample_service: Sample service instance
        
    Returns:
        List[SampleResponse]: Samples in chronological order
    
    Raises:
        HTTP 400: Invalid time range (start >= end)
        HTTP 404: Fermentation not found
        HTTP 401: Not authenticated
    
    Example:
        GET /api/v1/samples/timerange?fermentation_id=1&start_date=2024-11-01T00:00:00&end_date=2024-11-10T23:59:59
    """
    try:
        samples = await sample_service.get_samples_in_timerange(
            fermentation_id=fermentation_id,
            winery_id=current_user.winery_id,
            start=start_date,
            end=end_date
        )
        
        return [SampleResponse.from_entity(s) for s in samples]
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# ======================================================================================
# POST /api/v1/samples/validate - Validate Sample Data (Dry-Run)
# ======================================================================================

@samples_router.post(
    "/validate",
    response_model=dict,  # ValidationResult serialized as dict
    status_code=status.HTTP_200_OK,
    summary="Validate sample data without creating",
    description="Performs dry-run validation of sample data. Useful for frontend validation before submission."
)
async def validate_sample(
    fermentation_id: int = Query(..., gt=0, description="ID of the fermentation"),
    request: SampleCreateRequest = ...,
    current_user: Annotated[UserContext, Depends(get_current_user)] = None,
    sample_service: Annotated[ISampleService, Depends(get_sample_service)] = None
) -> dict:
    """
    Validate sample data without creating the sample (dry-run).
    
    Performs all validation checks that would be applied during sample creation,
    but does not actually create the sample. Useful for providing real-time
    validation feedback in forms.
    
    Args:
        fermentation_id: ID of the fermentation
        request: Sample data to validate
        current_user: Authenticated user context
        sample_service: Sample service instance
        
    Returns:
        ValidationResult: Contains is_valid, errors[], and warnings[]
    
    Raises:
        HTTP 404: Fermentation not found
        HTTP 401: Not authenticated
    
    Example Response:
        {
            "is_valid": true,
            "errors": [],
            "warnings": []
        }
    """
    try:
        # Convert API request to service DTO
        sample_dto = SampleCreate(
            sample_type=SampleType(request.sample_type),
            value=request.value,
            units=request.units,
            recorded_at=request.recorded_at
        )
        
        # Validate via service (does not create sample)
        validation_result = await sample_service.validate_sample_data(
            fermentation_id=fermentation_id,
            winery_id=current_user.winery_id,
            data=sample_dto
        )
        
        # Return as dict for JSON serialization
        return validation_result.model_dump()
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# =============================================================================
# DELETE /api/v1/samples/{id} - Delete sample
# =============================================================================

@samples_router.delete(
    "/{sample_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sample",
    description="Soft deletes a sample (marks as deleted but keeps in database)",
    responses={
        204: {"description": "Sample deleted successfully"},
        404: {"description": "Sample or fermentation not found"},
        403: {"description": "Not authenticated"}
    },
    tags=["samples"]
)
async def delete_sample(
    sample_id: int = Path(..., description="Sample ID", gt=0),
    fermentation_id: int = Query(..., description="Fermentation ID", gt=0),
    sample_service: Annotated[ISampleService, Depends(get_sample_service)] = None,
    current_user: Annotated[UserContext, Depends(get_current_user)] = None
) -> None:
    """
    Delete a sample (soft delete).
    
    **Business Rules:**
    - Sample must exist and belong to specified fermentation
    - Fermentation must belong to user's winery (multi-tenancy)
    - Soft delete only (marks is_deleted=True)
    
    **Authentication:**
    - Required: Yes (JWT Bearer token)
    - Roles: Any authenticated user from the same winery
    
    **Multi-tenancy:**
    - Enforced via fermentation ownership check
    
    **Example:**
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/samples/123?fermentation_id=1" \
         -H "Authorization: Bearer YOUR_JWT_TOKEN"
    ```
    
    Status: ✅ Implemented (Phase 4 - 2025-11-15)
    """
    try:
        await sample_service.delete_sample(
            sample_id=sample_id,
            fermentation_id=fermentation_id,
            winery_id=current_user.winery_id
        )
        # 204 No Content - no body returned
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
