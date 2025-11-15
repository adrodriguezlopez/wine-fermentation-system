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

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker, get_current_user

from src.modules.fermentation.src.api.schemas.requests.sample_requests import (
    SampleCreateRequest
)
from src.modules.fermentation.src.api.schemas.responses.sample_responses import (
    SampleResponse
)
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
    try:
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
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


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
