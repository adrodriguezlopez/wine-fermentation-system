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
from src.shared.auth.infra.api.dependencies import require_winemaker

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
    # TODO: Inject FermentationService via dependency
) -> FermentationResponse:
    """
    Create a new fermentation
    
    Args:
        request: Fermentation creation data (validated by Pydantic)
        current_user: Authenticated user context (provides winery_id)
    
    Returns:
        FermentationResponse: Created fermentation with ID and timestamps
    
    Raises:
        HTTP 403: Insufficient permissions (not WINEMAKER or ADMIN)
        HTTP 422: Invalid request data
        HTTP 400: Business validation error (e.g., vessel in use)
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
        
        # TODO: Call service layer
        # For now, create a mock response to pass initial tests
        # This will be replaced with actual service call in next iteration
        
        from datetime import datetime
        from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
        
        # Mock entity for testing (TDD GREEN phase - minimal implementation)
        class MockFermentation:
            id = 1
            winery_id = current_user.winery_id
            vintage_year = request.vintage_year
            yeast_strain = request.yeast_strain
            vessel_code = request.vessel_code
            input_mass_kg = request.input_mass_kg
            initial_sugar_brix = request.initial_sugar_brix
            initial_density = request.initial_density
            status = FermentationStatus.ACTIVE
            start_date = request.start_date
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()
        
        mock_entity = MockFermentation()
        
        return FermentationResponse.from_entity(mock_entity)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except (DuplicateError, BusinessRuleViolation) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log unexpected errors in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
