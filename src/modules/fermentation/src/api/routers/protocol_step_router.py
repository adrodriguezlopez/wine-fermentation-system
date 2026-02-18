"""
Protocol Steps Router - REST API endpoints for protocol step management

Implements CRUD operations for protocol steps with:
- JWT authentication via require_winemaker
- Multi-tenancy enforcement (via protocol's winery_id)
- Step ordering and dependencies
- Pagination support
- Request/response validation via DTOs

Following ADR-006 API Layer Design
Following ADR-035 Protocol Data Model Schema
"""

from fastapi import APIRouter, Depends, status, HTTPException, Query, Path
from typing import Annotated, Optional

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker

# Request schemas (Pydantic - for validation)
from src.modules.fermentation.src.api.schemas.requests import (
    StepCreateRequest,
    StepUpdateRequest,
)

# Response schemas (Pydantic - for serialization)
from src.modules.fermentation.src.api.schemas.responses import (
    StepResponse,
    StepListResponse,
)

# Domain DTOs (Dataclasses - for business logic)
from src.modules.fermentation.src.domain.dtos import (
    StepCreate,
    StepUpdate,
)
from src.modules.fermentation.src.domain.repositories.protocol_step_repository_interface import (
    IProtocolStepRepository,
)
from src.modules.fermentation.src.domain.repositories.fermentation_protocol_repository_interface import (
    IFermentationProtocolRepository,
)
from src.modules.fermentation.src.repository_component.protocol_step_repository import (
    ProtocolStepRepository,
)
from src.modules.fermentation.src.repository_component.fermentation_protocol_repository import (
    FermentationProtocolRepository,
)
from src.modules.fermentation.src.api.dependencies import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession


# Router instance
router = APIRouter(
    prefix="/api/v1/protocols",
    tags=["protocol-steps"]
)


def get_step_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> IProtocolStepRepository:
    """Dependency: Get protocol step repository instance"""
    return ProtocolStepRepository(session=session)


def get_protocol_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> IFermentationProtocolRepository:
    """Dependency: Get protocol repository instance"""
    return FermentationProtocolRepository(session=session)


@router.post(
    "/{protocol_id}/steps",
    response_model=StepResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a step to a protocol",
    description="Creates a new step within a protocol. Steps are ordered and can have dependencies."
)
async def create_protocol_step(
    protocol_id: Annotated[int, Path(gt=0, description="Protocol ID")],
    request: StepCreateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    step_repository: Annotated[IProtocolStepRepository, Depends(get_step_repository)],
    protocol_repository: Annotated[IFermentationProtocolRepository, Depends(get_protocol_repository)]
) -> StepResponse:
    """
    Add a step to a protocol.
    
    Args:
        protocol_id: ID of the parent protocol
        request: Step creation data (StepCreateRequest - validated by Pydantic)
        current_user: Authenticated user context
        step_repository: Step repository (injected)
        protocol_repository: Protocol repository (injected)
    
    Returns:
        StepResponse: Created step with ID
    
    Raises:
        HTTP 404: Protocol not found
        HTTP 403: Protocol belongs to different winery
        HTTP 422: Invalid request data (validation error)
            - Step type must be one of 6 categories
            - Day must be >= 0
            - Tolerance must be >= 0
            - Criticality must be 0-100
        HTTP 409: Duplicate step order
        HTTP 401: Not authenticated
    """
    # Verify protocol exists and belongs to user's winery
    protocol = await protocol_repository.get_by_id(protocol_id)
    
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol {protocol_id} not found"
        )
    
    if protocol.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - protocol belongs to different winery"
        )
    
    try:
        # Create step DTO from request
        step_dto = StepCreate(
            protocol_id=protocol_id,
            step_order=request.step_order,
            step_type=request.step_type,
            description=request.description,
            expected_day=request.expected_day,
            tolerance_hours=request.tolerance_hours,
            duration_minutes=request.duration_minutes,
            criticality_score=request.criticality_score,
            can_repeat_daily=request.can_repeat_daily,
            depends_on_step_id=request.depends_on_step_id,
            notes=request.notes
        )
        
        # Create step
        created_step = await step_repository.create(step_dto)
        
        return StepResponse(
            id=created_step.id,
            protocol_id=created_step.protocol_id,
            step_order=created_step.step_order,
            step_type=created_step.step_type,
            description=created_step.description,
            expected_day=created_step.expected_day,
            tolerance_hours=created_step.tolerance_hours,
            duration_minutes=created_step.duration_minutes,
            criticality_score=created_step.criticality_score,
            can_repeat_daily=created_step.can_repeat_daily,
            depends_on_step_id=created_step.depends_on_step_id,
            notes=created_step.notes,
            created_at=created_step.created_at,
            updated_at=created_step.updated_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        if "unique" in str(e).lower() or "order" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Step order {request.step_order} already exists for this protocol"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create step"
        )


@router.patch(
    "/{protocol_id}/steps/{step_id}",
    response_model=StepResponse,
    summary="Update a protocol step",
    description="Updates step metadata (description, timing, criticality). Cannot change step order or step type."
)
async def update_protocol_step(
    protocol_id: Annotated[int, Path(gt=0, description="Protocol ID")],
    step_id: Annotated[int, Path(gt=0, description="Step ID")],
    request: StepUpdateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    step_repository: Annotated[IProtocolStepRepository, Depends(get_step_repository)],
    protocol_repository: Annotated[IFermentationProtocolRepository, Depends(get_protocol_repository)]
) -> StepResponse:
    """
    Update a protocol step.
    
    Args:
        protocol_id: ID of the parent protocol
        step_id: ID of the step to update
        request: Update data (StepUpdate DTO)
        current_user: Authenticated user context
        step_repository: Step repository (injected)
        protocol_repository: Protocol repository (injected)
    
    Returns:
        StepResponse: Updated step
    
    Raises:
        HTTP 404: Protocol or step not found
        HTTP 403: Protocol belongs to different winery
        HTTP 422: Invalid update data
        HTTP 401: Not authenticated
    """
    # Verify protocol exists and belongs to user's winery
    protocol = await protocol_repository.get_by_id(protocol_id)
    
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol {protocol_id} not found"
        )
    
    if protocol.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - protocol belongs to different winery"
        )
    
    # Verify step belongs to protocol
    step = await step_repository.get_by_id(step_id)
    
    if not step or step.protocol_id != protocol_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step {step_id} not found in protocol {protocol_id}"
        )
    
    try:
        update_data = {k: v for k, v in request.model_dump(exclude_unset=True).items()}
        updated_step = await step_repository.update(step_id, update_data)
        
        if not updated_step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to update step {step_id}"
            )
        
        return StepResponse(
            id=updated_step.id,
            protocol_id=updated_step.protocol_id,
            step_order=updated_step.step_order,
            step_type=updated_step.step_type,
            description=updated_step.description,
            expected_day=updated_step.expected_day,
            tolerance_hours=updated_step.tolerance_hours,
            duration_minutes=updated_step.duration_minutes,
            criticality_score=updated_step.criticality_score,
            can_repeat_daily=updated_step.can_repeat_daily,
            depends_on_step_id=updated_step.depends_on_step_id,
            notes=updated_step.notes,
            created_at=updated_step.created_at,
            updated_at=updated_step.updated_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.delete(
    "/{protocol_id}/steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a protocol step",
    description="Deletes a step from a protocol. Only allowed if no completions exist for this step."
)
async def delete_protocol_step(
    protocol_id: Annotated[int, Path(gt=0, description="Protocol ID")],
    step_id: Annotated[int, Path(gt=0, description="Step ID")],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    step_repository: Annotated[IProtocolStepRepository, Depends(get_step_repository)],
    protocol_repository: Annotated[IFermentationProtocolRepository, Depends(get_protocol_repository)]
) -> None:
    """
    Delete a protocol step.
    
    Args:
        protocol_id: ID of the parent protocol
        step_id: ID of the step to delete
        current_user: Authenticated user context
        step_repository: Step repository (injected)
        protocol_repository: Protocol repository (injected)
    
    Raises:
        HTTP 404: Protocol or step not found
        HTTP 403: Protocol belongs to different winery
        HTTP 409: Cannot delete - step has completions
        HTTP 401: Not authenticated
    """
    # Verify protocol exists and belongs to user's winery
    protocol = await protocol_repository.get_by_id(protocol_id)
    
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol {protocol_id} not found"
        )
    
    if protocol.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - protocol belongs to different winery"
        )
    
    # Verify step belongs to protocol
    step = await step_repository.get_by_id(step_id)
    
    if not step or step.protocol_id != protocol_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step {step_id} not found in protocol {protocol_id}"
        )
    
    try:
        await step_repository.delete(step_id)
    except Exception as e:
        if "completion" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete step with existing completions"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete step"
        )


@router.get(
    "/{protocol_id}/steps",
    response_model=StepListResponse,
    summary="List steps in a protocol",
    description="Lists all steps in a protocol, ordered by step_order. Supports pagination."
)
async def list_protocol_steps(
    protocol_id: Annotated[int, Path(gt=0, description="Protocol ID")],
    page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    current_user: Annotated[UserContext, Depends(require_winemaker)] = None,
    step_repository: Annotated[IProtocolStepRepository, Depends(get_step_repository)] = None,
    protocol_repository: Annotated[IFermentationProtocolRepository, Depends(get_protocol_repository)] = None
) -> StepListResponse:
    """
    List all steps in a protocol.
    
    Args:
        protocol_id: ID of the protocol
        page: Page number (1-indexed, default 1)
        page_size: Items per page (default 20, max 100)
        current_user: Authenticated user context
        step_repository: Step repository (injected)
        protocol_repository: Protocol repository (injected)
    
    Returns:
        StepListResponse: List of steps with pagination metadata
    
    Raises:
        HTTP 404: Protocol not found
        HTTP 403: Protocol belongs to different winery
        HTTP 422: Invalid pagination parameters
        HTTP 401: Not authenticated
    """
    # Verify protocol exists and belongs to user's winery
    protocol = await protocol_repository.get_by_id(protocol_id)
    
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol {protocol_id} not found"
        )
    
    if protocol.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - protocol belongs to different winery"
        )
    
    try:
        steps, total_count = await step_repository.list_by_protocol_paginated(
            protocol_id=protocol_id,
            page=page,
            page_size=page_size
        )
        
        items = [
            StepResponse(
                id=s.id,
                protocol_id=s.protocol_id,
                step_order=s.step_order,
                step_type=s.step_type,
                description=s.description,
                expected_day=s.expected_day,
                tolerance_hours=s.tolerance_hours,
                duration_minutes=s.duration_minutes,
                criticality_score=s.criticality_score,
                can_repeat_daily=s.can_repeat_daily,
                depends_on_step_id=s.depends_on_step_id,
                notes=s.notes,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
            for s in steps
        ]
        
        return StepListResponse(
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
