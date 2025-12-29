"""
Vineyard Router - REST API endpoints

Handles HTTP requests for vineyard management operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated

from src.modules.fruit_origin.src.api_component.schemas.requests.vineyard_requests import (
    VineyardCreateRequest,
    VineyardUpdateRequest,
)
from src.modules.fruit_origin.src.api_component.schemas.responses.vineyard_responses import (
    VineyardResponse,
    VineyardListResponse,
)
from src.modules.fruit_origin.src.api_component.dependencies.services import (
    get_fruit_origin_service,
)
from src.modules.fruit_origin.src.service_component.interfaces.fruit_origin_service_interface import (
    IFruitOriginService,
)
from src.modules.fruit_origin.src.domain.dtos.vineyard_dtos import (
    VineyardCreate,
    VineyardUpdate,
)
from src.shared.auth.infra.api.dependencies import get_current_user
from src.shared.auth.domain.dtos import UserContext


router = APIRouter(
    prefix="/api/v1/vineyards",
    tags=["Vineyards"]
)


@router.post(
    "/",
    response_model=VineyardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new vineyard",
    description="Creates a new vineyard for the authenticated user's winery. Requires WINEMAKER or ADMIN role."
)
async def create_vineyard(
    request: VineyardCreateRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFruitOriginService, Depends(get_fruit_origin_service)]
) -> VineyardResponse:
    """
    Create a new vineyard.
    
    **Authentication:** Required (JWT Bearer token)
    **Authorization:** WINEMAKER or ADMIN role
    **Multi-tenancy:** Vineyard created for user's winery (from JWT token)
    
    **Business Rules:**
    - Code must be unique within winery
    - Code automatically converted to uppercase
    - Code must be alphanumeric (hyphens/underscores allowed)
    
    **Returns:** Created vineyard with ID and timestamps
    """
    vineyard_dto = VineyardCreate(
        code=request.code,
        name=request.name,
        notes=request.notes
    )
    
    vineyard = await service.create_vineyard(
        winery_id=user.winery_id,
        user_id=user.user_id,
        data=vineyard_dto
    )
    
    return VineyardResponse.model_validate(vineyard)


@router.get(
    "/{vineyard_id}",
    response_model=VineyardResponse,
    summary="Get vineyard by ID",
    description="Retrieves a vineyard by ID. Only returns if vineyard belongs to user's winery."
)
async def get_vineyard(
    vineyard_id: int,
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFruitOriginService, Depends(get_fruit_origin_service)]
) -> VineyardResponse:
    """
    Get vineyard by ID.
    
    **Authentication:** Required (JWT Bearer token)
    **Authorization:** Any authenticated user
    **Multi-tenancy:** Only returns vineyard if it belongs to user's winery
    
    **Returns:** Vineyard details
    **Raises:** 404 if vineyard not found or doesn't belong to user's winery
    """
    vineyard = await service.get_vineyard(vineyard_id, user.winery_id)
    
    if not vineyard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vineyard {vineyard_id} not found"
        )
    
    return VineyardResponse.model_validate(vineyard)


@router.get(
    "/",
    response_model=VineyardListResponse,
    summary="List vineyards",
    description="Lists all vineyards for the authenticated user's winery."
)
async def list_vineyards(
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFruitOriginService, Depends(get_fruit_origin_service)],
    include_deleted: bool = False
) -> VineyardListResponse:
    """
    List vineyards for user's winery.
    
    **Authentication:** Required (JWT Bearer token)
    **Authorization:** Any authenticated user
    **Multi-tenancy:** Only returns vineyards from user's winery
    
    **Query Parameters:**
    - `include_deleted`: Include soft-deleted vineyards (default: false)
    
    **Returns:** List of vineyards with total count
    """
    vineyards = await service.list_vineyards(
        winery_id=user.winery_id,
        include_deleted=include_deleted
    )
    
    return VineyardListResponse(
        vineyards=[VineyardResponse.model_validate(v) for v in vineyards],
        total=len(vineyards)
    )


@router.patch(
    "/{vineyard_id}",
    response_model=VineyardResponse,
    summary="Update vineyard",
    description="Updates a vineyard's name and/or notes. Requires WINEMAKER or ADMIN role."
)
async def update_vineyard(
    vineyard_id: int,
    request: VineyardUpdateRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFruitOriginService, Depends(get_fruit_origin_service)]
) -> VineyardResponse:
    """
    Update vineyard details.
    
    **Authentication:** Required (JWT Bearer token)
    **Authorization:** WINEMAKER or ADMIN role
    **Multi-tenancy:** Can only update vineyards from user's winery
    
    **Updatable Fields:**
    - `name`: Vineyard name
    - `notes`: Optional notes
    
    **Note:** Code cannot be changed after creation
    
    **Returns:** Updated vineyard
    **Raises:** 404 if vineyard not found or doesn't belong to user's winery
    """
    # Create update DTO only with provided fields
    update_data = {}
    if request.name is not None:
        update_data['name'] = request.name
    if request.notes is not None:
        update_data['notes'] = request.notes
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    vineyard_dto = VineyardUpdate(**update_data)
    
    vineyard = await service.update_vineyard(
        vineyard_id=vineyard_id,
        winery_id=user.winery_id,
        user_id=user.user_id,
        data=vineyard_dto
    )
    
    if not vineyard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vineyard {vineyard_id} not found"
        )
    
    return VineyardResponse.model_validate(vineyard)


@router.delete(
    "/{vineyard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete vineyard",
    description="Soft deletes a vineyard. Cannot delete if vineyard has active harvest lots. Requires ADMIN role."
)
async def delete_vineyard(
    vineyard_id: int,
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[IFruitOriginService, Depends(get_fruit_origin_service)]
) -> None:
    """
    Soft delete a vineyard.
    
    **Authentication:** Required (JWT Bearer token)
    **Authorization:** ADMIN role
    **Multi-tenancy:** Can only delete vineyards from user's winery
    
    **Business Rules:**
    - Cannot delete vineyard with active (non-deleted) harvest lots
    - Performs soft delete (is_deleted = True)
    - Cascade to blocks is handled automatically
    
    **Returns:** 204 No Content on success
    **Raises:**
    - 404 if vineyard not found or doesn't belong to user's winery
    - 409 if vineyard has active harvest lots
    """
    success = await service.delete_vineyard(
        vineyard_id=vineyard_id,
        winery_id=user.winery_id,
        user_id=user.user_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vineyard {vineyard_id} not found"
        )
