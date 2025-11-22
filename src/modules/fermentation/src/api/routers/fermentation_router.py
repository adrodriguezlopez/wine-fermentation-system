"""
Fermentation Router - REST API endpoints for fermentation management

Implements CRUD operations with:
- JWT authentication
- Role-based authorization  
- Multi-tenancy enforcement
- Request/response validation

Following ADR-006 API Layer Design
"""

from fastapi import APIRouter, Depends, status, HTTPException, Query, Path, Body
from typing import Annotated, Optional

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker, get_current_user

from src.modules.fermentation.src.api.schemas.requests.fermentation_requests import (
    FermentationCreateRequest,
    FermentationUpdateRequest,
    StatusUpdateRequest,
    CompleteFermentationRequest,
    FermentationWithBlendCreateRequest
)
from src.modules.fermentation.src.api.schemas.responses.fermentation_responses import (
    FermentationResponse,
    PaginatedResponse,
    ValidationResponse,
    ValidationErrorDetail,
    TimelineResponse,
    StatisticsResponse
)
from src.modules.fermentation.src.service_component.interfaces.fermentation_service_interface import IFermentationService
from src.modules.fermentation.src.service_component.interfaces.sample_service_interface import ISampleService
from src.modules.fermentation.src.domain.interfaces.unit_of_work_interface import IUnitOfWork
from src.modules.fermentation.src.domain.dtos import FermentationCreate, FermentationUpdate, FermentationWithBlendCreate, LotSourceData
from src.modules.fermentation.src.service_component.errors import (
    ValidationError,
    NotFoundError,
    DuplicateError,
    BusinessRuleViolation
)
from src.modules.fermentation.src.api.dependencies import get_fermentation_service, get_sample_service, get_unit_of_work
from src.modules.fermentation.src.api.error_handlers import handle_service_errors


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
@handle_service_errors
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


@router.post(
    "/blends",
    response_model=FermentationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create fermentation with blend (multiple harvest lots)",
    description="Creates a fermentation from multiple harvest lots atomically. Uses UnitOfWork pattern to ensure all-or-nothing creation."
)
@handle_service_errors
async def create_fermentation_with_blend(
    request: FermentationWithBlendCreateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[IFermentationService, Depends(get_fermentation_service)],
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)]
) -> FermentationResponse:
    """
    Create fermentation from multiple harvest lots (blend) - ATOMIC operation.
    
    Uses UnitOfWork pattern to ensure:
    - Fermentation + all lot sources created together
    - Automatic rollback if any operation fails
    - Data consistency across multiple tables
    
    Args:
        request: Fermentation + blend data (validated by Pydantic)
        current_user: Authenticated user context (provides winery_id)
        service: Fermentation service (injected)
        uow: Unit of Work for atomic transaction (injected)
    
    Returns:
        FermentationResponse: Created fermentation with ID
    
    Raises:
        HTTP 403: Insufficient permissions (not WINEMAKER or ADMIN)
        HTTP 422: Invalid request data (Pydantic validation)
        HTTP 400: Business validation error
            - Harvest lot doesn't exist or doesn't belong to winery
            - Mass mismatch (sum of lots != fermentation mass)
            - Duplicate lot IDs
            - Lot already exhausted
        HTTP 401: Not authenticated
    
    Use Case (ADR-001 Fruit Origin Model):
        Creating wine blends from multiple vineyard blocks while
        maintaining complete traceability and referential integrity.
    
    Example Request:
        ```json
        {
          "vintage_year": 2024,
          "yeast_strain": "EC-1118",
          "input_mass_kg": 100.0,
          "initial_sugar_brix": 22.5,
          "initial_density": 1.095,
          "start_date": "2024-11-22T10:00:00",
          "lot_sources": [
            {"harvest_lot_id": 1, "mass_used_kg": 60.0},
            {"harvest_lot_id": 2, "mass_used_kg": 40.0}
          ]
        }
        ```
    
    Status: ✅ NEW - Part of UnitOfWork implementation (Nov 22, 2025)
    """
    # Convert API request to service DTOs
    fermentation_dto = FermentationCreate(
        fermented_by_user_id=current_user.user_id,
        vintage_year=request.vintage_year,
        yeast_strain=request.yeast_strain,
        vessel_code=request.vessel_code,
        input_mass_kg=request.input_mass_kg,
        initial_sugar_brix=request.initial_sugar_brix,
        initial_density=request.initial_density,
        start_date=request.start_date
    )
    
    lot_sources_dto = [
        LotSourceData(
            harvest_lot_id=lot.harvest_lot_id,
            mass_used_kg=lot.mass_used_kg,
            notes=lot.notes
        )
        for lot in request.lot_sources
    ]
    
    blend_dto = FermentationWithBlendCreate(
        fermentation_data=fermentation_dto,
        lot_sources=lot_sources_dto
    )
    
    # Call service layer with UnitOfWork
    created_fermentation = await service.create_fermentation_with_blend(
        winery_id=current_user.winery_id,
        user_id=current_user.user_id,
        data=blend_dto,
        uow=uow
    )
    
    # Convert entity to response DTO
    return FermentationResponse.from_entity(created_fermentation)


@router.get("/{fermentation_id}", response_model=FermentationResponse, status_code=200)
@handle_service_errors
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


@router.get(
    "",
    response_model=PaginatedResponse[FermentationResponse],
    status_code=status.HTTP_200_OK,
    summary="List fermentations",
    description="List all fermentations for the authenticated user's winery with pagination support."
)
@handle_service_errors
async def list_fermentations(
    current_user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFermentationService, Depends(get_fermentation_service)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by fermentation status"),
    include_completed: bool = Query(False, description="Include completed fermentations")
) -> PaginatedResponse[FermentationResponse]:
    """
    List fermentations for user's winery with pagination.
    
    TDD GREEN Phase: Minimal implementation to pass tests.
    
    Args:
        current_user: Authenticated user context (multi-tenancy)
        service: Injected fermentation service
        page: Page number (1-indexed, default: 1)
        size: Items per page (default: 20, max: 100)
        status_filter: Optional status filter (ACTIVE, COMPLETED, etc.)
        include_completed: Include completed fermentations (default: False)
    
    Returns:
        PaginatedResponse[FermentationResponse]: Paginated list of fermentations
    
    Business Rules:
        - Multi-tenancy: Only returns fermentations from user's winery
        - Pagination: Applied after filtering
        - Status filtering: Client-side or service-side
        - Completed fermentations excluded by default
    """
    # Get all fermentations for winery (service applies multi-tenancy)
    all_fermentations = await service.get_fermentations_by_winery(
        winery_id=current_user.winery_id,
        status=status_filter,
        include_completed=include_completed
    )
    
    # Calculate pagination
    total = len(all_fermentations)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    
    # Slice for current page
    page_items = all_fermentations[start_idx:end_idx]
    
    # Convert entities to response DTOs
    items = [FermentationResponse.from_entity(f) for f in page_items]
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size
    )


@router.patch(
    "/{fermentation_id}",
    response_model=FermentationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a fermentation process",
    description="""
    Update an existing fermentation process with partial data.
    
    This endpoint allows updating specific fields of a fermentation process.
    Only the fields provided in the request will be updated.
    
    **Permissions Required:**
    - Must be authenticated
    - Must be a winemaker
    - Must own the winery associated with the fermentation
    
    **Validations:**
    - Fermentation must exist and belong to user's winery
    - Numeric values must be within valid ranges
    - Dates must be logically consistent
    """,
    responses={
        200: {"description": "Fermentation successfully updated"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized - user is not a winemaker or doesn't own the winery"},
        404: {"description": "Fermentation not found"},
        422: {"description": "Validation error - invalid data provided"},
        500: {"description": "Internal server error"}
    }
)
@handle_service_errors
async def update_fermentation(
    fermentation_id: int = Path(..., gt=0, description="ID of the fermentation to update"),
    request: FermentationUpdateRequest = Body(...),
    current_user: UserContext = Depends(require_winemaker),
    fermentation_service: IFermentationService = Depends(get_fermentation_service)
) -> FermentationResponse:
    """
    Update a fermentation process.
    
    Args:
        fermentation_id: ID of the fermentation to update
        request: Request body with fields to update
        current_user: Authenticated user context
        fermentation_service: Fermentation service instance
        
    Returns:
        Updated fermentation data
        
    Raises:
        HTTPException: If not authorized, not found, or validation fails
    """
    # Build FermentationUpdate DTO with only provided fields
    update_dto = FermentationUpdate(
        yeast_strain=request.yeast_strain,
        vessel_code=request.vessel_code,
        input_mass_kg=request.input_mass_kg,
        initial_sugar_brix=request.initial_sugar_brix,
        initial_density=request.initial_density,
        vintage_year=request.vintage_year,
        start_date=request.start_date
    )
    
    # Call service to update
    updated_fermentation = await fermentation_service.update_fermentation(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id,
        user_id=current_user.user_id,
        data=update_dto
    )
    
    # Convert to response DTO
    return FermentationResponse.from_entity(updated_fermentation)


@router.patch(
    "/{fermentation_id}/status",
    response_model=FermentationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update fermentation status",
    description="""
    Update the status of a fermentation process.
    
    This endpoint handles status transitions in the fermentation lifecycle:
    - planning → in_progress
    - in_progress → monitoring
    - monitoring → completed
    
    **Permissions Required:**
    - Must be authenticated
    - Must be a winemaker
    - Must own the winery associated with the fermentation
    
    **Validations:**
    - Fermentation must exist and belong to user's winery
    - Status transition must be valid according to business rules
    - Invalid transitions will return 422 error
    """,
    responses={
        204: {"description": "Status successfully updated"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized - user is not a winemaker or doesn't own the winery"},
        404: {"description": "Fermentation not found"},
        422: {"description": "Validation error - invalid status or transition"},
        500: {"description": "Internal server error"}
    }
)
@handle_service_errors
async def update_fermentation_status(
    fermentation_id: int = Path(..., gt=0, description="ID of the fermentation to update"),
    request: StatusUpdateRequest = Body(...),
    current_user: UserContext = Depends(require_winemaker),
    fermentation_service: IFermentationService = Depends(get_fermentation_service)
) -> FermentationResponse:
    """
    Update fermentation status.
    
    Args:
        fermentation_id: ID of the fermentation to update
        request: Request body with new status
        current_user: Authenticated user context
        fermentation_service: Fermentation service instance
        
    Raises:
        HTTPException: If not authorized, not found, or invalid transition
    """
    # Call service to update status (service will validate transition)
    updated_fermentation = await fermentation_service.update_status(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id,
        user_id=current_user.user_id,
        new_status=request.status  # Pass as string, service converts to enum
    )
    
    # Convert to response DTO
    return FermentationResponse.from_entity(updated_fermentation)


@router.patch(
    "/{fermentation_id}/complete",
    response_model=FermentationResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete a fermentation process",
    description="""
    Mark a fermentation as completed and record final metrics.
    
    This endpoint:
    1. Validates that fermentation exists and is in 'monitoring' status
    2. Records final metrics (sugar brix, mass, notes)
    3. Transitions status to 'completed'
    4. Sets completion timestamp
    
    **Permissions Required:**
    - Must be authenticated
    - Must be a winemaker
    - Must own the winery associated with the fermentation
    
    **Validations:**
    - Fermentation must be in 'monitoring' status
    - Final sugar brix must be between 0 and 50
    - Final mass must be greater than 0
    """,
    responses={
        200: {"description": "Fermentation successfully completed"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized - user is not a winemaker or doesn't own the winery"},
        404: {"description": "Fermentation not found"},
        422: {"description": "Validation error - invalid status or data"},
        500: {"description": "Internal server error"}
    }
)
@handle_service_errors
async def complete_fermentation(
    fermentation_id: int = Path(..., gt=0, description="ID of the fermentation to complete"),
    request: CompleteFermentationRequest = Body(...),
    current_user: UserContext = Depends(require_winemaker),
    fermentation_service: IFermentationService = Depends(get_fermentation_service)
) -> FermentationResponse:
    """
    Complete a fermentation process.
    
    Args:
        fermentation_id: ID of the fermentation to complete
        request: Request body with final metrics
        current_user: Authenticated user context
        fermentation_service: Fermentation service instance
        
    Returns:
        Completed fermentation data
        
    Raises:
        HTTPException: If not authorized, not found, or validation fails
    """
    # Call service to complete fermentation
    completed_fermentation = await fermentation_service.complete_fermentation(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id,
        user_id=current_user.user_id,
        final_sugar_brix=request.final_sugar_brix,
        final_mass_kg=request.final_mass_kg,
        notes=request.notes
    )
    
    # Convert to response DTO
    return FermentationResponse.from_entity(completed_fermentation)


@router.delete(
    "/{fermentation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a fermentation process",
    description="""
    Soft delete a fermentation process.
    
    This endpoint performs a soft delete, marking the fermentation as deleted
    without physically removing it from the database. The fermentation will
    no longer appear in list queries but can be recovered if needed.
    
    **Permissions Required:**
    - Must be authenticated
    - Must be a winemaker
    - Must own the winery associated with the fermentation
    
    **Validations:**
    - Fermentation must exist and belong to user's winery
    - Fermentation must not already be deleted
    """,
    responses={
        204: {"description": "Fermentation successfully deleted"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized - user is not a winemaker or doesn't own the winery"},
        404: {"description": "Fermentation not found"},
        500: {"description": "Internal server error"}
    }
)
@handle_service_errors
async def delete_fermentation(
    fermentation_id: int = Path(..., gt=0, description="ID of the fermentation to delete"),
    current_user: UserContext = Depends(require_winemaker),
    fermentation_service: IFermentationService = Depends(get_fermentation_service)
) -> None:
    """
    Delete a fermentation process (soft delete).
    
    Args:
        fermentation_id: ID of the fermentation to delete
        current_user: Authenticated user context
        fermentation_service: Fermentation service instance
        
    Raises:
        HTTPException: If not authorized or not found
    """
    # Call service to soft delete
    success = await fermentation_service.soft_delete(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id,
        user_id=current_user.user_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fermentation with id {fermentation_id} not found"
        )


@router.post(
    "/validate",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate fermentation creation data",
    description="""
    Validate fermentation creation data without actually creating the fermentation.
    
    This endpoint performs a dry-run validation of fermentation creation data,
    checking all business rules and constraints without persisting to the database.
    
    Useful for:
    - Pre-flight validation in forms
    - Checking data quality before submission
    - Getting detailed validation errors
    
    **Permissions Required:**
    - Must be authenticated
    - Must be a winemaker
    
    **Returns:**
    - valid: true if data passes all validations
    - errors: list of validation errors (empty if valid)
    """,
    responses={
        200: {"description": "Validation completed (check 'valid' field in response)"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized - user is not a winemaker"},
        500: {"description": "Internal server error"}
    }
)
@handle_service_errors
async def validate_fermentation_data(
    request: FermentationCreateRequest = Body(...),
    current_user: UserContext = Depends(require_winemaker),
    fermentation_service: IFermentationService = Depends(get_fermentation_service)
) -> ValidationResponse:
    """
    Validate fermentation creation data.
    
    Args:
        request: Request body with fermentation data to validate
        current_user: Authenticated user context
        fermentation_service: Fermentation service instance
        
    Returns:
        ValidationResponse with validation results and any errors
        
    Raises:
        HTTPException: If not authorized
    """
    # Build FermentationCreate DTO
    fermentation_dto = FermentationCreate(
        fermented_by_user_id=current_user.user_id,
        vintage_year=request.vintage_year,
        yeast_strain=request.yeast_strain,
        vessel_code=request.vessel_code,
        input_mass_kg=request.input_mass_kg,
        initial_sugar_brix=request.initial_sugar_brix,
        initial_density=request.initial_density,
        start_date=request.start_date
    )
    
    # Call service to validate (doesn't create anything - synchronous method)
    validation_result = fermentation_service.validate_creation_data(
        data=fermentation_dto
    )
    
    # Build response
    if validation_result.is_valid:
        return ValidationResponse(valid=True, errors=[])
    
    # Convert validation errors to response DTOs
    error_details = [
        ValidationErrorDetail(
            field=error.field,
            message=error.message,
            code=None  # ValidationError doesn't have code field
        )
        for error in validation_result.errors
    ]
    
    return ValidationResponse(valid=False, errors=error_details)


# =============================================================================
# GET /api/v1/fermentations/{id}/timeline - Get Fermentation Timeline
# =============================================================================

@router.get(
    "/{fermentation_id}/timeline",
    response_model=TimelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get fermentation timeline",
    description="Retrieves fermentation details with all samples in chronological order",
    responses={
        200: {"description": "Timeline data retrieved successfully"},
        404: {"description": "Fermentation not found"},
        403: {"description": "Not authenticated"}
    },
    tags=["fermentations"]
)
@handle_service_errors
async def get_fermentation_timeline(
    fermentation_id: int = Path(..., description="Fermentation ID", gt=0),
    current_user: Annotated[UserContext, Depends(get_current_user)] = None,
    fermentation_service: Annotated[IFermentationService, Depends(get_fermentation_service)] = None,
    sample_service: Annotated[ISampleService, Depends(get_sample_service)] = None
) -> TimelineResponse:
    """
    Get complete timeline for a fermentation.
    
    Combines fermentation data with all samples in chronological order.
    Useful for visualizing fermentation progress over time.
    
    **Business Rules:**
    - Returns fermentation details + all samples
    - Samples ordered by recorded_at (chronological)
    - Includes metadata: sample_count, first/last sample dates
    
    **Authentication:**
    - Required: Yes (JWT Bearer token)
    - Roles: Any authenticated user from the same winery
    
    **Multi-tenancy:**
    - Enforced via fermentation ownership check
    
    **Example Response:**
    ```json
    {
        "fermentation": {...},
        "samples": [{...}, {...}],
        "sample_count": 15,
        "first_sample_date": "2024-11-01T10:00:00",
        "last_sample_date": "2024-11-15T14:30:00"
    }
    ```
    
    Status: ✅ Implemented (Phase 4 - 2025-11-15)
    """
    # Step 1: Get fermentation
    fermentation = await fermentation_service.get_fermentation(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id
    )
    
    if fermentation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fermentation {fermentation_id} not found"
        )
    
    # Step 2: Get all samples for fermentation (chronologically ordered)
    samples = await sample_service.get_samples_by_fermentation(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id
    )
    
    # Step 3: Build response
    from src.modules.fermentation.src.api.schemas.responses.sample_responses import SampleResponse
    
    fermentation_response = FermentationResponse.from_entity(fermentation)
    sample_responses = [SampleResponse.from_entity(s) for s in samples]
    
    # Calculate metadata
    sample_count = len(samples)
    first_sample_date = samples[0].recorded_at if samples else None
    last_sample_date = samples[-1].recorded_at if samples else None
    
    return TimelineResponse(
        fermentation=fermentation_response,
        samples=sample_responses,
        sample_count=sample_count,
        first_sample_date=first_sample_date,
        last_sample_date=last_sample_date
    )


# =============================================================================
# GET /api/v1/fermentations/{id}/statistics - Get Fermentation Statistics
# =============================================================================

@router.get(
    "/{fermentation_id}/statistics",
    response_model=StatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get fermentation statistics",
    description="Calculates and returns statistical analysis of fermentation progress",
    responses={
        200: {"description": "Statistics calculated successfully"},
        404: {"description": "Fermentation not found"},
        403: {"description": "Not authenticated"}
    },
    tags=["fermentations"]
)
@handle_service_errors
async def get_fermentation_statistics(
    fermentation_id: int = Path(..., description="Fermentation ID", gt=0),
    current_user: Annotated[UserContext, Depends(get_current_user)] = None,
    fermentation_service: Annotated[IFermentationService, Depends(get_fermentation_service)] = None,
    sample_service: Annotated[ISampleService, Depends(get_sample_service)] = None
) -> StatisticsResponse:
    """
    Get statistical analysis for a fermentation.
    
    Calculates aggregated metrics including:
    - Duration (days from start to last sample)
    - Sample counts (total + by type)
    - Sugar progression (initial, latest, drop)
    - Temperature averages
    - Sample frequency
    
    **Business Rules:**
    - Requires at least fermentation data (samples optional)
    - Sugar statistics require sugar samples
    - Duration calculated from start_date to last sample
    
    **Authentication:**
    - Required: Yes (JWT Bearer token)
    - Roles: Any authenticated user from the same winery
    
    **Multi-tenancy:**
    - Enforced via fermentation ownership check
    
    **Example Response:**
    ```json
    {
        "fermentation_id": 1,
        "status": "ACTIVE",
        "start_date": "2024-11-01T10:00:00",
        "duration_days": 14.5,
        "total_samples": 25,
        "samples_by_type": {"sugar": 10, "temperature": 8, "density": 7},
        "initial_sugar": 22.5,
        "latest_sugar": 12.0,
        "sugar_drop": 10.5,
        "avg_temperature": 18.2,
        "avg_samples_per_day": 1.72
    }
    ```
    
    Status: ✅ Implemented (Phase 4 - 2025-11-15)
    """
    from src.modules.fermentation.src.domain.enums.sample_type import SampleType
    from collections import Counter
    
    # Step 1: Get fermentation
    fermentation = await fermentation_service.get_fermentation(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id
    )
    
    if fermentation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fermentation {fermentation_id} not found"
        )
    
    # Step 2: Get all samples
    samples = await sample_service.get_samples_by_fermentation(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id
    )
    
    # Step 3: Calculate statistics
    total_samples = len(samples)
    
    # Count samples by type
    sample_types = [s.sample_type for s in samples]
    samples_by_type = dict(Counter(sample_types))
    
    # Duration calculation
    duration_days = None
    if samples:
        last_sample_date = samples[-1].recorded_at
        duration = last_sample_date - fermentation.start_date
        duration_days = duration.total_seconds() / 86400  # Convert to days
    
    # Sugar statistics
    sugar_samples = [s for s in samples if s.sample_type == SampleType.SUGAR.value]
    initial_sugar = fermentation.initial_sugar_brix
    latest_sugar = None
    sugar_drop = None
    
    if sugar_samples:
        latest_sugar = sugar_samples[-1].value
        sugar_drop = initial_sugar - latest_sugar
    
    # Temperature statistics
    temp_samples = [s for s in samples if s.sample_type == SampleType.TEMPERATURE.value]
    avg_temperature = None
    if temp_samples:
        avg_temperature = sum(s.value for s in temp_samples) / len(temp_samples)
    
    # Sample frequency
    avg_samples_per_day = None
    if duration_days and duration_days > 0:
        avg_samples_per_day = total_samples / duration_days
    
    return StatisticsResponse(
        fermentation_id=fermentation.id,
        status=fermentation.status,
        start_date=fermentation.start_date,
        duration_days=duration_days,
        total_samples=total_samples,
        samples_by_type=samples_by_type,
        initial_sugar=initial_sugar,
        latest_sugar=latest_sugar,
        sugar_drop=sugar_drop,
        avg_temperature=avg_temperature,
        avg_samples_per_day=avg_samples_per_day
    )
