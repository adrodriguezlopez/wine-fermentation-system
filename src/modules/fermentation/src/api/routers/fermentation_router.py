"""
Fermentation Router - REST API endpoints for fermentation management

Implements CRUD operations with:
- JWT authentication
- Role-based authorization  
- Multi-tenancy enforcement
- Request/response validation

Following ADR-006 API Layer Design
"""

from fastapi import APIRouter, Depends, status, HTTPException
from typing import Annotated

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker, get_current_user

from src.modules.fermentation.src.api.schemas.requests.fermentation_requests import (
    FermentationCreateRequest,
    FermentationUpdateRequest
)
from src.modules.fermentation.src.api.schemas.responses.fermentation_responses import (
    FermentationResponse
)
from src.modules.fermentation.src.service_component.interfaces.fermentation_service_interface import IFermentationService
from src.modules.fermentation.src.domain.dtos import FermentationCreate
from src.modules.fermentation.src.service_component.errors import (
    ValidationError,
    NotFoundError,
    DuplicateError,
    BusinessRuleViolation
)
from src.modules.fermentation.src.api.dependencies import get_fermentation_service


# Router instance
router = APIRouter(
    prefix="/api/v1/fermentations",
    tags=["fermentations"]
)


@router.post(
    "",
    response_model=FermentationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new fermentation",
    description="Creates a new fermentation for the authenticated user's winery. Requires WINEMAKER or ADMIN role."
)
async def create_fermentation(
    request: FermentationCreateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[IFermentationService, Depends(get_fermentation_service)]
) -> FermentationResponse:
    """
    Create a new fermentation
    
    Args:
        request: Fermentation creation data (validated by Pydantic)
        current_user: Authenticated user context (provides winery_id)
        service: Fermentation service (injected via dependency)
    
    Returns:
        FermentationResponse: Created fermentation with ID and timestamps
    
    Raises:
        HTTP 403: Insufficient permissions (not WINEMAKER or ADMIN)
        HTTP 422: Invalid request data (Pydantic validation)
        HTTP 400: Business validation error (e.g., vessel in use, invalid ranges)
        HTTP 401: Not authenticated
    """
    try:
        # Convert API request to service DTO
        create_dto = FermentationCreate(
            fermented_by_user_id=current_user.user_id,  # From auth context
            vintage_year=request.vintage_year,
            yeast_strain=request.yeast_strain,
            vessel_code=request.vessel_code,
            input_mass_kg=request.input_mass_kg,
            initial_sugar_brix=request.initial_sugar_brix,
            initial_density=request.initial_density,
            start_date=request.start_date
        )
        
        # Call service layer (REFACTOR: replaced mock with real service)
        created_fermentation = await service.create_fermentation(
            winery_id=current_user.winery_id,  # Multi-tenancy from auth context
            user_id=current_user.user_id,      # Audit trail
            data=create_dto
        )
        
        # Convert entity to response DTO
        return FermentationResponse.from_entity(created_fermentation)
        
    except ValidationError as e:
        # Service validation failed (business rules)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        # Validation errors from service (includes validator errors)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (DuplicateError, BusinessRuleViolation) as e:
        # Business logic violations (e.g., vessel in use)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log unexpected errors in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/{fermentation_id}", response_model=FermentationResponse, status_code=200)
async def get_fermentation(
    fermentation_id: int,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFermentationService, Depends(get_fermentation_service)]
) -> FermentationResponse:
    """
    Get a single fermentation by ID.
    
    TDD GREEN Phase: Minimal implementation to pass tests.
    
    Args:
        fermentation_id: ID of the fermentation to retrieve
        current_user: Authenticated user context (multi-tenancy)
        service: Injected fermentation service
    
    Returns:
        FermentationResponse: Fermentation data
    
    Raises:
        HTTPException 404: Fermentation not found or access denied (multi-tenancy)
        HTTPException 401/403: Authentication/authorization failure
    
    Business Rules:
        - Multi-tenancy: Only returns fermentation from user's winery
        - Service returns None for wrong winery (security - don't reveal existence)
        - Soft-deleted records return 404
    """
    try:
        fermentation = await service.get_fermentation(
            fermentation_id=fermentation_id,
            winery_id=current_user.winery_id
        )
        
        if fermentation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fermentation with ID {fermentation_id} not found"
            )
        
        return FermentationResponse.from_entity(fermentation)
    
    except HTTPException:
        # Re-raise HTTP exceptions (404, etc.)
        raise
    except Exception as e:
        # Log unexpected errors in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
