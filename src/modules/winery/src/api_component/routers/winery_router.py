"""
FastAPI router for Winery API endpoints (Admin namespace).

Provides 6 winery management endpoints:
1. POST /admin/wineries - Create winery (ADMIN only)
2. GET /admin/wineries/{id} - Get winery by ID
3. GET /admin/wineries/code/{code} - Get winery by code
4. GET /admin/wineries - List wineries (ADMIN only)
5. PATCH /admin/wineries/{id} - Update winery
6. DELETE /admin/wineries/{id} - Soft delete winery (ADMIN only)

Authorization:
- CREATE/DELETE/LIST: ADMIN only
- GET/UPDATE: Users can access own winery, ADMIN can access all
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError

from src.shared.auth.infra.api.dependencies import get_current_user, require_admin
from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums.user_role import UserRole
from src.modules.winery.src.api_component.dependencies.services import get_winery_service
from src.modules.winery.src.api_component.schemas.requests.winery_requests import (
    WineryCreateRequest,
    WineryUpdateRequest
)
from src.modules.winery.src.api_component.schemas.responses.winery_responses import (
    WineryResponse,
    PaginatedWineriesResponse
)
from src.modules.winery.src.service_component.services.winery_service import WineryService
from src.modules.winery.src.domain.dtos.winery_dtos import WineryCreate, WineryUpdate
from src.shared.domain.errors import (
    WineryNotFound,
    DuplicateCodeError,
    InvalidWineryData,
    WineryNameAlreadyExists,
)


router = APIRouter(
    prefix="/admin/wineries",
    tags=["Winery Management (Admin)"]
)


# =============================================================================
# Helper Functions
# =============================================================================

async def check_winery_access(
    winery_id: int,
    user: UserContext,
    service: WineryService
) -> None:
    """
    Check if user has access to the specified winery.
    
    - ADMIN: Can access all wineries
    - WINEMAKER: Can only access their own winery
    
    Args:
        winery_id: The winery ID to check access for
        user: Current authenticated user
        service: Winery service instance
        
    Raises:
        HTTPException: 403 if user doesn't have access
        HTTPException: 404 if winery doesn't exist
    """
    if user.role == UserRole.ADMIN:
        # Admin can access all wineries, just verify it exists
        try:
            await service.get_winery(winery_id)
        except WineryNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Winery with ID {winery_id} not found"
            )
        return
    
    # Non-admin users can only access their own winery
    if user.winery_id != winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this winery"
        )
    
    # Verify winery exists
    try:
        await service.get_winery(winery_id)
    except WineryNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Winery with ID {winery_id} not found"
        )


async def check_winery_code_access(
    code: str,
    user: UserContext,
    service: WineryService
) -> None:
    """
    Check if user has access to the winery with specified code.
    
    Args:
        code: The winery code to check access for
        user: Current authenticated user
        service: Winery service instance
        
    Raises:
        HTTPException: 403 if user doesn't have access
        HTTPException: 404 if winery doesn't exist
    """
    try:
        winery = await service.get_winery_by_code(code)
    except WineryNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Winery with code '{code}' not found"
        )
    
    # Check access using winery ID
    if user.role != "ADMIN" and user.winery_id != winery.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this winery"
        )


# =============================================================================
# POST /admin/wineries - Create Winery (ADMIN only)
# =============================================================================

@router.post(
    "",
    response_model=WineryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new winery",
    description="Create a new winery. **ADMIN only**."
)
async def create_winery(
    request: WineryCreateRequest,
    user: Annotated[UserContext, Depends(require_admin)],
    service: Annotated[WineryService, Depends(get_winery_service)]
) -> WineryResponse:
    """
    Create a new winery (ADMIN only).
    
    Args:
        request: Winery creation data
        user: Current authenticated admin user
        service: Winery service instance
        
    Returns:
        Created winery data
        
    Raises:
        409: Duplicate code or name
        422: Invalid request data
    """
    try:
        # Convert API request DTO to domain DTO
        domain_dto = WineryCreate(
            code=request.code,
            name=request.name,
            location=request.location,
            notes=request.notes
        )
        
        winery = await service.create_winery(domain_dto)
        return WineryResponse.from_entity(winery)
    
    except DuplicateCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    
    except InvalidWineryData as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    
    except WineryNameAlreadyExists as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    
    except IntegrityError as e:
        # Catch database-level constraint violations
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'UNIQUE constraint' in error_msg or 'unique' in error_msg.lower():
            if 'name' in error_msg.lower():
                detail = "A winery with this name already exists"
            elif 'code' in error_msg.lower():
                detail = "A winery with this code already exists"
            else:
                detail = "Duplicate value detected"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )


# =============================================================================
# GET /admin/wineries/{id} - Get Winery by ID
# =============================================================================

@router.get(
    "/{winery_id}",
    response_model=WineryResponse,
    summary="Get winery by ID",
    description="Get winery details by ID. Users can only access their own winery, ADMIN can access all."
)
async def get_winery_by_id(
    winery_id: int,
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[WineryService, Depends(get_winery_service)]
) -> WineryResponse:
    """
    Get winery by ID.
    
    Authorization:
    - Users can only access their own winery
    - ADMIN can access all wineries
    
    Args:
        winery_id: Winery ID
        user: Current authenticated user
        service: Winery service instance
        
    Returns:
        Winery data
        
    Raises:
        403: User doesn't have access to this winery
        404: Winery not found
    """
    await check_winery_access(winery_id, user, service)
    
    try:
        winery = await service.get_winery(winery_id)
        return WineryResponse.from_entity(winery)
    
    except WineryNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Winery with ID {winery_id} not found"
        )


# =============================================================================
# GET /admin/wineries/code/{code} - Get Winery by Code
# =============================================================================

@router.get(
    "/code/{code}",
    response_model=WineryResponse,
    summary="Get winery by code",
    description="Get winery details by unique code. Users can only access their own winery, ADMIN can access all."
)
async def get_winery_by_code(
    code: str,
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[WineryService, Depends(get_winery_service)]
) -> WineryResponse:
    """
    Get winery by code.
    
    Authorization:
    - Users can only access their own winery
    - ADMIN can access all wineries
    
    Args:
        code: Winery code
        user: Current authenticated user
        service: Winery service instance
        
    Returns:
        Winery data
        
    Raises:
        403: User doesn't have access to this winery
        404: Winery not found
    """
    await check_winery_code_access(code, user, service)
    
    try:
        winery = await service.get_winery_by_code(code)
        return WineryResponse.from_entity(winery)
    
    except WineryNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Winery with code '{code}' not found"
        )


# =============================================================================
# GET /admin/wineries - List Wineries (ADMIN only)
# =============================================================================

@router.get(
    "",
    response_model=PaginatedWineriesResponse,
    summary="List wineries",
    description="List all wineries with pagination. **ADMIN only**."
)
async def list_wineries(
    user: Annotated[UserContext, Depends(require_admin)],
    service: Annotated[WineryService, Depends(get_winery_service)],
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
) -> PaginatedWineriesResponse:
    """
    List all wineries with pagination (ADMIN only).
    
    Args:
        user: Current authenticated admin user
        service: Winery service instance
        limit: Items per page (1-100)
        offset: Offset for pagination
        
    Returns:
        Paginated list of wineries
    """
    wineries = await service.list_wineries(skip=offset, limit=limit)
    total = await service.count_wineries()
    
    return PaginatedWineriesResponse(
        items=[WineryResponse.from_entity(w) for w in wineries],
        total=total,
        limit=limit,
        offset=offset
    )


# =============================================================================
# PATCH /admin/wineries/{id} - Update Winery
# =============================================================================

@router.patch(
    "/{winery_id}",
    response_model=WineryResponse,
    summary="Update winery",
    description="Update winery details. Users can only update their own winery, ADMIN can update all."
)
async def update_winery(
    winery_id: int,
    request: WineryUpdateRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[WineryService, Depends(get_winery_service)]
) -> WineryResponse:
    """
    Update winery details.
    
    Authorization:
    - Users can only update their own winery
    - ADMIN can update all wineries
    
    Note: Code is immutable and cannot be updated.
    
    Args:
        winery_id: Winery ID
        request: Update data
        user: Current authenticated user
        service: Winery service instance
        
    Returns:
        Updated winery data
        
    Raises:
        403: User doesn't have access to this winery
        404: Winery not found
        409: Duplicate name
    """
    await check_winery_access(winery_id, user, service)
    
    try:
        # Convert API request DTO to domain DTO
        domain_dto = WineryUpdate(
            name=request.name,
            location=request.location,
            notes=request.notes
        )
        
        winery = await service.update_winery(winery_id, domain_dto)
        return WineryResponse.from_entity(winery)
    
    except WineryNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Winery with ID {winery_id} not found"
        )
    
    except InvalidWineryData as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


# =============================================================================
# DELETE /admin/wineries/{id} - Soft Delete Winery (ADMIN only)
# =============================================================================

@router.delete(
    "/{winery_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete winery",
    description="Soft delete a winery. **ADMIN only**. Winery must have no active fermentations."
)
async def delete_winery(
    winery_id: int,
    user: Annotated[UserContext, Depends(require_admin)],
    service: Annotated[WineryService, Depends(get_winery_service)]
) -> None:
    """
    Soft delete a winery (ADMIN only).
    
    Business rules:
    - Winery must not have active fermentations
    - Soft delete only (mark as deleted)
    
    Args:
        winery_id: Winery ID
        user: Current authenticated admin user
        service: Winery service instance
        
    Raises:
        404: Winery not found
        400: Winery has active fermentations
    """
    try:
        await service.delete_winery(winery_id)
    
    except WineryNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Winery with ID {winery_id} not found"
        )
    
    except ValueError as e:
        # Business rule violation (e.g., has active fermentations)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
