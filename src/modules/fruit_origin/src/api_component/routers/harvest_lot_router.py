"""
Harvest Lot Router - REST API endpoints

Handles HTTP requests for harvest lot management operations.
Follows same pattern as vineyard_router.py.

Phase 3 - Complete CRUD operations:
- POST / - Create harvest lot
- GET /{id} - Get harvest lot by ID  
- GET / - List harvest lots (filter by vineyard_id)
- PATCH /{id} - Update harvest lot (partial updates)
- DELETE /{id} - Delete harvest lot (soft delete)

Future endpoints (Phase 3 integration):
- GET /{id}/usage - Check usage in fermentations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional

from src.modules.fruit_origin.src.api_component.schemas.requests.harvest_lot_requests import (
    HarvestLotCreateRequest,
    HarvestLotUpdateRequest,
)
from src.modules.fruit_origin.src.api_component.schemas.responses.harvest_lot_responses import (
    HarvestLotResponse,
    HarvestLotListResponse,
)
from src.modules.fruit_origin.src.api_component.dependencies.services import (
    get_fruit_origin_service,
)
from src.modules.fruit_origin.src.service_component.interfaces.fruit_origin_service_interface import (
    IFruitOriginService,
)
from src.modules.fruit_origin.src.domain.dtos.harvest_lot_dtos import (
    HarvestLotCreate,
    HarvestLotUpdate,
)
from src.shared.auth.infra.api.dependencies import get_current_user
from src.shared.auth.domain.dtos import UserContext


router = APIRouter(
    prefix="/api/v1/harvest-lots",
    tags=["Harvest Lots"]
)


@router.post(
    "/",
    response_model=HarvestLotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new harvest lot",
    description="Creates a harvest lot for a vineyard block with validation"
)
async def create_harvest_lot(
    request: HarvestLotCreateRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFruitOriginService, Depends(get_fruit_origin_service)]
) -> HarvestLotResponse:
    """
    Create a new harvest lot.
    
    **Business Rules:**
    - Code must be unique within winery
    - Code automatically converted to uppercase
    - Block must exist and belong to user's winery
    - Weight must be positive
    - Harvest date should be <= today (soft validation)
    
    **Returns:** Created harvest lot with ID and timestamps
    **Raises:**
    - 404 if block not found or doesn't belong to user's winery
    - 409 if code already exists for this winery
    - 400 if validation fails
    """
    harvest_lot_dto = HarvestLotCreate(
        block_id=request.block_id,
        code=request.code,
        harvest_date=request.harvest_date,
        weight_kg=request.weight_kg,
        brix_at_harvest=request.brix_at_harvest,
        brix_method=request.brix_method,
        brix_measured_at=request.brix_measured_at,
        grape_variety=request.grape_variety,
        clone=request.clone,
        rootstock=request.rootstock,
        pick_method=request.pick_method,
        pick_start_time=request.pick_start_time,
        pick_end_time=request.pick_end_time,
        bins_count=request.bins_count,
        field_temp_c=request.field_temp_c,
        notes=request.notes
    )
    
    harvest_lot = await service.create_harvest_lot(
        winery_id=user.winery_id,
        user_id=user.user_id,
        data=harvest_lot_dto
    )
    
    return HarvestLotResponse.model_validate(harvest_lot)


@router.get(
    "/{lot_id}",
    response_model=HarvestLotResponse,
    status_code=status.HTTP_200_OK,
    summary="Get harvest lot by ID",
    description="Retrieves a single harvest lot with multi-tenancy enforcement"
)
async def get_harvest_lot(
    lot_id: int,
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFruitOriginService, Depends(get_fruit_origin_service)]
) -> HarvestLotResponse:
    """
    Get a harvest lot by ID.
    
    **Security:** Only returns lots owned by user's winery
    **Returns:** Harvest lot details
    **Raises:** 404 if lot not found or doesn't belong to user's winery
    """
    harvest_lot = await service.get_harvest_lot(
        lot_id=lot_id,
        winery_id=user.winery_id
    )
    
    if not harvest_lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Harvest lot {lot_id} not found or access denied"
        )
    
    return HarvestLotResponse.model_validate(harvest_lot)


@router.get(
    "/",
    response_model=HarvestLotListResponse,
    status_code=status.HTTP_200_OK,
    summary="List harvest lots",
    description="Lists all harvest lots for the winery, optionally filtered by vineyard"
)
async def list_harvest_lots(
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFruitOriginService, Depends(get_fruit_origin_service)],
    vineyard_id: Optional[int] = Query(None, description="Filter by vineyard ID")
) -> HarvestLotListResponse:
    """
    List all harvest lots for the authenticated user's winery.
    
    **Filters:**
    - vineyard_id: Optional filter to show lots from specific vineyard
    
    **Security:** Only returns lots owned by user's winery
    **Returns:** List of harvest lots (may be empty)
    """
    harvest_lots = await service.list_harvest_lots(
        winery_id=user.winery_id,
        vineyard_id=vineyard_id
    )
    
    return HarvestLotListResponse(
        lots=[HarvestLotResponse.model_validate(lot) for lot in harvest_lots],
        total=len(harvest_lots)
    )


@router.patch(
    "/{lot_id}",
    response_model=HarvestLotResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a harvest lot",
    description="Updates an existing harvest lot (partial updates allowed)"
)
async def update_harvest_lot(
    lot_id: int,
    request: HarvestLotUpdateRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFruitOriginService, Depends(get_fruit_origin_service)]
) -> HarvestLotResponse:
    """
    Update a harvest lot with partial data.
    
    **Business Rules:**
    - Only provided fields are updated (partial updates)
    - Code must remain unique within winery
    - Cannot change block_id after creation
    - At least one field must be provided
    
    **Returns:** Updated harvest lot
    **Raises:**
    - 400 if no fields provided to update
    - 404 if lot not found or doesn't belong to user's winery
    - 409 if code already exists for another lot
    """
    # Check if at least one field is provided
    data_dict = request.model_dump(exclude_unset=True)
    if not data_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided to update"
        )
    
    # Convert to service DTO
    harvest_lot_dto = HarvestLotUpdate(**data_dict)
    
    updated_lot = await service.update_harvest_lot(
        lot_id=lot_id,
        winery_id=user.winery_id,
        user_id=user.user_id,
        data=harvest_lot_dto
    )
    
    return HarvestLotResponse.model_validate(updated_lot)


@router.delete(
    "/{lot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a harvest lot",
    description="Soft-deletes a harvest lot (sets is_deleted=True)"
)
async def delete_harvest_lot(
    lot_id: int,
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFruitOriginService, Depends(get_fruit_origin_service)]
):
    """
    Delete a harvest lot (soft delete).
    
    **Business Rules:**
    - Soft delete (sets is_deleted flag)
    - Cannot delete if used in fermentation (future validation)
    
    **Returns:** 204 No Content on success
    **Raises:**
    - 404 if lot not found or doesn't belong to user's winery
    - 409 if lot is used in fermentation (future)
    """
    await service.delete_harvest_lot(
        lot_id=lot_id,
        winery_id=user.winery_id,
        user_id=user.user_id
    )
    
    # Return 204 No Content (FastAPI automatically removes response body)
