"""
Step Completions Router - REST API endpoints for step completion tracking

Implements CRUD operations for step completions (audit log) with:
- JWT authentication via require_winemaker
- Multi-tenancy enforcement
- Skip reason tracking
- Audit trail (completed_by_user_id, verified_by_user_id)
- Pagination support
- Request/response validation via DTOs

Following ADR-006 API Layer Design
Following ADR-035 Protocol Data Model Schema
"""

from fastapi import APIRouter, Depends, status, HTTPException, Query, Path
from typing import Annotated

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker

# Request schemas (Pydantic - for validation)
from src.modules.fermentation.src.api.schemas.requests import (
    CompletionCreateRequest,
)

# Response schemas (Pydantic - for serialization)
from src.modules.fermentation.src.api.schemas.responses import (
    CompletionResponse,
    CompletionListResponse,
)

# Domain DTOs (Dataclasses - for business logic)
from src.modules.fermentation.src.domain.dtos import (
    CompletionCreate,
)
from src.modules.fermentation.src.domain.repositories.step_completion_repository_interface import (
    IStepCompletionRepository,
)
from src.modules.fermentation.src.domain.repositories.protocol_execution_repository_interface import (
    IProtocolExecutionRepository,
)
from src.modules.fermentation.src.repository_component.step_completion_repository import (
    StepCompletionRepository,
)
from src.modules.fermentation.src.repository_component.protocol_execution_repository import (
    ProtocolExecutionRepository,
)
from src.modules.fermentation.src.api.dependencies import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession


# Router instance
router = APIRouter(
    prefix="/api/v1",
    tags=["step-completions"]
)


def get_completion_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> IStepCompletionRepository:
    """Dependency: Get step completion repository instance"""
    return StepCompletionRepository(session=session)


def get_execution_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> IProtocolExecutionRepository:
    """Dependency: Get protocol execution repository instance"""
    return ProtocolExecutionRepository(session=session)


@router.post(
    "/executions/{execution_id}/complete",
    response_model=CompletionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Mark a step complete or skipped",
    description="Records completion or skip of a protocol step. Creates audit log entry."
)
async def complete_protocol_step(
    execution_id: Annotated[int, Path(gt=0, description="Execution ID")],
    request: CompletionCreateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    completion_repository: Annotated[IStepCompletionRepository, Depends(get_completion_repository)],
    execution_repository: Annotated[IProtocolExecutionRepository, Depends(get_execution_repository)]
) -> CompletionResponse:
    """
    Record step completion or skip.
    
    Creates a StepCompletion entry (audit log) with:
    - XOR validation: Either completed_at OR was_skipped, never both
    - If skipped: must include skip_reason (5 types)
    - If completed: must include completed_at timestamp
    - Audit trail: tracks completed_by_user_id (winemaker who performed it)
    
    Args:
        execution_id: ID of the protocol execution
        request: Completion data (CompletionCreate DTO)
        current_user: Authenticated user context (for completed_by_user_id)
        completion_repository: Completion repository (injected)
        execution_repository: Execution repository (injected)
    
    Returns:
        CompletionResponse: Created completion record
    
    Raises:
        HTTP 404: Execution not found
        HTTP 403: Execution belongs to different winery
        HTTP 422: Invalid request data
            - Must specify either completed_at OR was_skipped (XOR)
            - If was_skipped=True, skip_reason is required (5 valid types)
            - Skip reason must be one of: EQUIPMENT_FAILURE, CONDITION_NOT_MET,
              FERMENTATION_ENDED, FERMENTATION_FAILED, WINEMAKER_DECISION
            - Criticality validation if applicable
        HTTP 401: Not authenticated
    """
    # Verify execution exists and belongs to user's winery
    execution = await execution_repository.get_by_id(execution_id)
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    # Enforce multi-tenancy
    if execution.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - execution belongs to different winery"
        )
    
    try:
        # Create completion DTO from request
        completion_dto = CompletionCreate(
            execution_id=execution_id,
            step_id=request.step_id,
            was_skipped=request.was_skipped,
            completed_at=request.completed_at,
            is_on_schedule=request.is_on_schedule,
            days_late=request.days_late,
            skip_reason=request.skip_reason,
            skip_notes=request.skip_notes,
            notes=request.notes,
            completed_by_user_id=current_user.user_id
        )
        
        # Create completion
        created_completion = await completion_repository.create(completion_dto)
        
        return CompletionResponse(
            id=created_completion.id,
            execution_id=created_completion.execution_id,
            step_id=created_completion.step_id,
            winery_id=created_completion.winery_id,
            was_skipped=created_completion.was_skipped,
            completed_at=created_completion.completed_at,
            is_on_schedule=created_completion.is_on_schedule,
            days_late=created_completion.days_late,
            skip_reason=created_completion.skip_reason,
            skip_notes=created_completion.skip_notes,
            notes=created_completion.notes,
            created_at=created_completion.created_at,
            updated_at=created_completion.updated_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record step completion"
        )


@router.get(
    "/executions/{execution_id}/completions",
    response_model=CompletionListResponse,
    summary="List completions for an execution",
    description="Lists all step completions (audit trail) for a protocol execution with pagination."
)
async def list_execution_completions(
    execution_id: Annotated[int, Path(gt=0, description="Execution ID")],
    page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    current_user: Annotated[UserContext, Depends(require_winemaker)] = None,
    completion_repository: Annotated[IStepCompletionRepository, Depends(get_completion_repository)] = None,
    execution_repository: Annotated[IProtocolExecutionRepository, Depends(get_execution_repository)] = None
) -> CompletionListResponse:
    """
    List all completions for an execution.
    
    Args:
        execution_id: ID of the protocol execution
        page: Page number (1-indexed, default 1)
        page_size: Items per page (default 20, max 100)
        current_user: Authenticated user context
        completion_repository: Completion repository (injected)
        execution_repository: Execution repository (injected)
    
    Returns:
        CompletionListResponse: List of completions with pagination metadata
    
    Raises:
        HTTP 404: Execution not found
        HTTP 403: Execution belongs to different winery
        HTTP 422: Invalid pagination parameters
        HTTP 401: Not authenticated
    """
    # Verify execution exists and belongs to user's winery
    execution = await execution_repository.get_by_id(execution_id)
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    # Enforce multi-tenancy
    if execution.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - execution belongs to different winery"
        )
    
    try:
        completions, total_count = await completion_repository.list_by_execution_paginated(
            execution_id=execution_id,
            page=page,
            page_size=page_size
        )
        
        items = [
            CompletionResponse(
                id=c.id,
                execution_id=c.execution_id,
                step_id=c.step_id,
                winery_id=c.winery_id,
                was_skipped=c.was_skipped,
                completed_at=c.completed_at,
                is_on_schedule=c.is_on_schedule,
                days_late=c.days_late,
                skip_reason=c.skip_reason,
                skip_notes=c.skip_notes,
                notes=c.notes,
                created_at=c.created_at,
                updated_at=c.updated_at
            )
            for c in completions
        ]
        
        return CompletionListResponse(
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


@router.get(
    "/completions/{completion_id}",
    response_model=CompletionResponse,
    summary="Get a specific completion record",
    description="Retrieves details of a specific step completion audit log entry."
)
async def get_step_completion(
    completion_id: Annotated[int, Path(gt=0, description="Completion ID")],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    completion_repository: Annotated[IStepCompletionRepository, Depends(get_completion_repository)],
    execution_repository: Annotated[IProtocolExecutionRepository, Depends(get_execution_repository)]
) -> CompletionResponse:
    """
    Get a specific step completion record.
    
    Args:
        completion_id: ID of the completion record
        current_user: Authenticated user context
        completion_repository: Completion repository (injected)
        execution_repository: Execution repository (injected)
    
    Returns:
        CompletionResponse: Completion details
    
    Raises:
        HTTP 404: Completion not found
        HTTP 403: Execution belongs to different winery
        HTTP 401: Not authenticated
    """
    completion = await completion_repository.get_by_id(completion_id)
    
    if not completion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Completion {completion_id} not found"
        )
    
    # Verify multi-tenancy by checking execution
    execution = await execution_repository.get_by_id(completion.execution_id)
    
    if not execution or execution.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - completion belongs to different winery"
        )
    
    return CompletionResponse(
        id=completion.id,
        execution_id=completion.execution_id,
        step_id=completion.step_id,
        winery_id=completion.winery_id,
        was_skipped=completion.was_skipped,
        completed_at=completion.completed_at,
        is_on_schedule=completion.is_on_schedule,
        days_late=completion.days_late,
        skip_reason=completion.skip_reason,
        skip_notes=completion.skip_notes,
        notes=completion.notes,
        created_at=completion.created_at,
        updated_at=completion.updated_at
    )
