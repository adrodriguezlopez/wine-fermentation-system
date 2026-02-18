"""
Protocol Router - REST API endpoints for protocol management

Implements CRUD operations for fermentation protocols with:
- JWT authentication via require_winemaker
- Multi-tenancy enforcement (winery_id from auth context)
- Version management (semantic versioning)
- Pagination support
- Request/response validation via DTOs

Following ADR-006 API Layer Design
Following ADR-035 Protocol Data Model Schema
"""

from fastapi import APIRouter, Depends, status, HTTPException, Query, Path
from typing import Annotated, Optional, Tuple, List

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker

# Request schemas (Pydantic - for validation)
from src.modules.fermentation.src.api.schemas.requests import (
    ProtocolCreateRequest,
    ProtocolUpdateRequest,
)

# Response schemas (Pydantic - for serialization)
from src.modules.fermentation.src.api.schemas.responses import (
    ProtocolResponse,
    ProtocolListResponse,
)

# Domain DTOs (Dataclasses - for business logic)
from src.modules.fermentation.src.domain.dtos import (
    ProtocolCreate,
    ProtocolUpdate,
)

from src.modules.fermentation.src.domain.repositories.fermentation_protocol_repository_interface import (
    IFermentationProtocolRepository,
)
from src.modules.fermentation.src.repository_component.fermentation_protocol_repository import (
    FermentationProtocolRepository,
)
from src.modules.fermentation.src.api.dependencies import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession


# Router instance
router = APIRouter(
    prefix="/api/v1/protocols",
    tags=["protocols"]
)


def get_protocol_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> IFermentationProtocolRepository:
    """
    Dependency: Get protocol repository instance
    
    Args:
        session: Database session (injected)
    
    Returns:
        IFermentationProtocolRepository: Repository instance
    """
    return FermentationProtocolRepository(session=session)


@router.post(
    "",
    response_model=ProtocolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new fermentation protocol",
    description="Creates a new protocol template for a winery/varietal. Requires WINEMAKER or ADMIN role."
)
async def create_protocol(
    request: ProtocolCreateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    repository: Annotated[IFermentationProtocolRepository, Depends(get_protocol_repository)]
) -> ProtocolResponse:
    """
    Create a new fermentation protocol.
    
    The protocol version must be unique per (winery_id, varietal_code, version) combination.
    New protocols start with is_active=False and must be explicitly activated.
    
    Args:
        request: Protocol creation data (ProtocolCreateRequest - validated by Pydantic)
        current_user: Authenticated user context (provides winery_id)
        repository: Protocol repository (injected)
    
    Returns:
        ProtocolResponse: Created protocol with ID and timestamps
    
    Raises:
        HTTP 403: Insufficient permissions (not WINEMAKER or ADMIN)
        HTTP 422: Invalid request data (Pydantic validation)
            - Version format must be X.Y (e.g., "1.0")
            - Duration must be > 0
            - Varietal code must be 1-4 characters
        HTTP 409: Duplicate protocol version for this (winery, varietal, version)
        HTTP 401: Not authenticated
    """
    try:
        # Convert Pydantic request to domain DTO
        # Ensure winery_id is set to authenticated user's winery
        protocol_dto = ProtocolCreate(
            winery_id=current_user.winery_id,
            varietal_code=request.varietal_code,
            varietal_name=request.varietal_name,
            color=request.color,
            version=request.version,
            protocol_name=request.protocol_name,
            expected_duration_days=request.expected_duration_days,
            created_by_user_id=current_user.user_id,
            description=request.description
        )
        
        # Create protocol via repository
        created_protocol = await repository.create(protocol_dto)
        
        # Convert entity to Pydantic response
        return ProtocolResponse(
            id=created_protocol.id,
            winery_id=created_protocol.winery_id,
            varietal_code=created_protocol.varietal_code,
            varietal_name=created_protocol.varietal_name,
            color=created_protocol.color,
            version=created_protocol.version,
            protocol_name=created_protocol.protocol_name,
            expected_duration_days=created_protocol.expected_duration_days,
            is_active=created_protocol.is_active,
            description=created_protocol.description,
            created_at=created_protocol.created_at,
            updated_at=created_protocol.updated_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        # Check for duplicate constraint violation
        if "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Protocol version {request.version} already exists for this varietal"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create protocol"
        )


@router.get(
    "/{protocol_id}",
    response_model=ProtocolResponse,
    summary="Get a specific protocol",
    description="Retrieves a protocol by ID. Multi-tenancy enforced (only accessible by winery that owns it)."
)
async def get_protocol(
    protocol_id: Annotated[int, Path(gt=0, description="Protocol ID")],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    repository: Annotated[IFermentationProtocolRepository, Depends(get_protocol_repository)]
) -> ProtocolResponse:
    """
    Get a specific protocol by ID.
    
    Args:
        protocol_id: ID of the protocol to retrieve
        current_user: Authenticated user context (for multi-tenancy)
        repository: Protocol repository (injected)
    
    Returns:
        ProtocolResponse: Protocol details
    
    Raises:
        HTTP 404: Protocol not found
        HTTP 403: Protocol belongs to different winery
        HTTP 401: Not authenticated
    """
    protocol = await repository.get_by_id(protocol_id)
    
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol {protocol_id} not found"
        )
    
    # Enforce multi-tenancy
    if protocol.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - protocol belongs to different winery"
        )
    
    # Convert entity to Pydantic response
    return ProtocolResponse(
        id=protocol.id,
        winery_id=protocol.winery_id,
        varietal_code=protocol.varietal_code,
        varietal_name=protocol.varietal_name,
        color=protocol.color,
        version=protocol.version,
        protocol_name=protocol.protocol_name,
        is_active=protocol.is_active,
        expected_duration_days=protocol.expected_duration_days,
        description=protocol.description,
        created_at=protocol.created_at,
        updated_at=protocol.updated_at
    )


@router.patch(
    "/{protocol_id}",
    response_model=ProtocolResponse,
    summary="Update a protocol",
    description="Updates protocol metadata (name, description). Cannot update version (create new version instead)."
)
async def update_protocol(
    protocol_id: Annotated[int, Path(gt=0, description="Protocol ID")],
    request: ProtocolUpdateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    repository: Annotated[IFermentationProtocolRepository, Depends(get_protocol_repository)]
) -> ProtocolResponse:
    """
    Update a protocol.
    
    Only metadata can be updated (name, description). Version cannot be changed.
    To create a new version, POST a new protocol with a different version number.
    
    Args:
        protocol_id: ID of the protocol to update
        request: Update data (ProtocolUpdate DTO)
        current_user: Authenticated user context
        repository: Protocol repository (injected)
    
    Returns:
        ProtocolResponse: Updated protocol
    
    Raises:
        HTTP 404: Protocol not found
        HTTP 403: Protocol belongs to different winery
        HTTP 422: Invalid update data
        HTTP 401: Not authenticated
    """
    protocol = await repository.get_by_id(protocol_id)
    
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol {protocol_id} not found"
        )
    
    # Enforce multi-tenancy
    if protocol.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - protocol belongs to different winery"
        )
    
    try:
        # Update allowed fields
        update_data = {k: v for k, v in request.model_dump(exclude_unset=True).items()}
        updated_protocol = await repository.update(protocol_id, update_data)
        
        if not updated_protocol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to update protocol {protocol_id}"
            )
        
        return ProtocolResponse(
            id=updated_protocol.id,
            winery_id=updated_protocol.winery_id,
            varietal_code=updated_protocol.varietal_code,
            varietal_name=updated_protocol.varietal_name,
            color=updated_protocol.color,
            version=updated_protocol.version,
            protocol_name=updated_protocol.protocol_name,
            is_active=updated_protocol.is_active,
            expected_duration_days=updated_protocol.expected_duration_days,
            description=updated_protocol.description,
            created_at=updated_protocol.created_at,
            updated_at=updated_protocol.updated_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.delete(
    "/{protocol_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a protocol",
    description="Soft deletes a protocol (marks as inactive). Hard delete only if no executions exist."
)
async def delete_protocol(
    protocol_id: Annotated[int, Path(gt=0, description="Protocol ID")],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    repository: Annotated[IFermentationProtocolRepository, Depends(get_protocol_repository)]
) -> None:
    """
    Delete a protocol.
    
    Soft delete: Marks protocol as inactive. Existing executions continue with this protocol.
    Hard delete: Only if no executions exist (prevents orphaning active fermentations).
    
    Args:
        protocol_id: ID of the protocol to delete
        current_user: Authenticated user context
        repository: Protocol repository (injected)
    
    Raises:
        HTTP 404: Protocol not found
        HTTP 403: Protocol belongs to different winery
        HTTP 409: Cannot delete - protocol has active executions
        HTTP 401: Not authenticated
    """
    protocol = await repository.get_by_id(protocol_id)
    
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol {protocol_id} not found"
        )
    
    # Enforce multi-tenancy
    if protocol.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - protocol belongs to different winery"
        )
    
    try:
        await repository.delete(protocol_id)
    except Exception as e:
        if "execution" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete protocol with active executions. Mark as inactive instead."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete protocol"
        )


@router.get(
    "",
    response_model=ProtocolListResponse,
    summary="List protocols with pagination",
    description="Lists all protocols for the user's winery with pagination support."
)
async def list_protocols(
    page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    current_user: Annotated[UserContext, Depends(require_winemaker)] = None,
    repository: Annotated[IFermentationProtocolRepository, Depends(get_protocol_repository)] = None
) -> ProtocolListResponse:
    """
    List all protocols for the authenticated user's winery.
    
    Supports pagination to efficiently handle large lists.
    Only returns protocols belonging to the user's winery (multi-tenancy).
    
    Args:
        page: Page number (1-indexed, default 1)
        page_size: Items per page (default 20, max 100)
        current_user: Authenticated user context (for winery_id)
        repository: Protocol repository (injected)
    
    Returns:
        ProtocolListResponse: List of protocols with pagination metadata
            - items: List of ProtocolResponse
            - total_count: Total number of protocols
            - page: Current page number
            - page_size: Items per page
            - total_pages: Calculated total pages
    
    Raises:
        HTTP 422: Invalid pagination parameters
        HTTP 401: Not authenticated
    """
    try:
        protocols, total_count = await repository.list_by_winery_paginated(
            winery_id=current_user.winery_id,
            page=page,
            page_size=page_size
        )
        
        items = [
            ProtocolResponse(
                id=p.id,
                winery_id=p.winery_id,
                varietal_code=p.varietal_code,
                varietal_name=p.varietal_name,
                color=p.color,
                version=p.version,
                protocol_name=p.protocol_name,
                is_active=p.is_active,
                expected_duration_days=p.expected_duration_days,
                description=p.description,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in protocols
        ]
        
        return ProtocolListResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=(total_count + page_size - 1) // page_size
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.patch(
    "/{protocol_id}/activate",
    response_model=ProtocolResponse,
    summary="Activate a protocol version",
    description="Activates a protocol version. Deactivates all other versions for the same (winery, varietal)."
)
async def activate_protocol(
    protocol_id: Annotated[int, Path(gt=0, description="Protocol ID")],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    repository: Annotated[IFermentationProtocolRepository, Depends(get_protocol_repository)]
) -> ProtocolResponse:
    """
    Activate a protocol version.
    
    Semantic Versioning Strategy:
    - Only one protocol version can be active per (winery_id, varietal_code)
    - New fermentations use the active version
    - In-progress fermentations continue with their original version
    - Existing executions are NOT retroactively changed
    
    Example:
    - v1.0 (active) has 3 in-progress executions
    - Activate v1.1
    - Result: v1.0 becomes inactive, v1.1 becomes active
    - Existing v1.0 executions continue with v1.0 steps
    - New fermentations use v1.1
    
    Args:
        protocol_id: ID of the protocol version to activate
        current_user: Authenticated user context
        repository: Protocol repository (injected)
    
    Returns:
        ProtocolResponse: Activated protocol
    
    Raises:
        HTTP 404: Protocol not found
        HTTP 403: Protocol belongs to different winery
        HTTP 401: Not authenticated
    """
    protocol = await repository.get_by_id(protocol_id)
    
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol {protocol_id} not found"
        )
    
    # Enforce multi-tenancy
    if protocol.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - protocol belongs to different winery"
        )
    
    try:
        # Deactivate all other versions for this (winery, varietal)
        await repository.deactivate_by_winery_varietal(
            winery_id=current_user.winery_id,
            varietal_code=protocol.varietal_code
        )
        
        # Activate this version
        activated_protocol = await repository.update(
            protocol_id,
            {"is_active": True}
        )
        
        if not activated_protocol:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate protocol"
            )
        
        return ProtocolResponse(
            id=activated_protocol.id,
            winery_id=activated_protocol.winery_id,
            varietal_code=activated_protocol.varietal_code,
            varietal_name=activated_protocol.varietal_name,
            color=activated_protocol.color,
            version=activated_protocol.version,
            protocol_name=activated_protocol.protocol_name,
            is_active=activated_protocol.is_active,
            expected_duration_days=activated_protocol.expected_duration_days,
            description=activated_protocol.description,
            created_at=activated_protocol.created_at,
            updated_at=activated_protocol.updated_at
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate protocol: {str(e)}"
        )
