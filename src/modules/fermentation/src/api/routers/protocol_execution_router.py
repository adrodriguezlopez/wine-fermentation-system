"""
Protocol Executions Router - REST API endpoints for protocol execution management

Implements CRUD operations for protocol executions (tracking protocol adherence per fermentation) with:
- JWT authentication via require_winemaker
- Multi-tenancy enforcement
- Execution status lifecycle tracking
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
    ExecutionStartRequest,
    ExecutionUpdateRequest,
)

# Response schemas (Pydantic - for serialization)
from src.modules.fermentation.src.api.schemas.responses import (
    ExecutionResponse,
    ExecutionListResponse,
)

# Domain DTOs (Dataclasses - for business logic)
from src.modules.fermentation.src.domain.dtos import (
    ExecutionStart,
    ExecutionUpdate,
)
from src.modules.fermentation.src.domain.repositories.protocol_execution_repository_interface import (
    IProtocolExecutionRepository,
)
from src.modules.fermentation.src.repository_component.protocol_execution_repository import (
    ProtocolExecutionRepository,
)
from src.modules.fermentation.src.api.dependencies import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession


# Router instance
router = APIRouter(
    prefix="/api/v1",
    tags=["protocol-executions"]
)


def get_execution_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> IProtocolExecutionRepository:
    """Dependency: Get protocol execution repository instance"""
    return ProtocolExecutionRepository(session=session)


@router.post(
    "/fermentations/{fermentation_id}/execute",
    response_model=ExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start protocol execution for a fermentation",
    description="Creates a ProtocolExecution to start tracking protocol adherence for a specific fermentation."
)
async def start_protocol_execution(
    fermentation_id: Annotated[int, Path(gt=0, description="Fermentation ID")],
    request: ExecutionStartRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    execution_repository: Annotated[IProtocolExecutionRepository, Depends(get_execution_repository)]
) -> ExecutionResponse:
    """
    Start protocol execution for a fermentation.
    
    Creates a ProtocolExecution that links a fermentation to a protocol template,
    initializing step tracking and compliance scoring.
    
    Args:
        fermentation_id: ID of the fermentation to track
        request: Execution start data (ExecutionStart DTO)
        current_user: Authenticated user context
        execution_repository: Execution repository (injected)
    
    Returns:
        ExecutionResponse: Created execution with ID and initial status (NOT_STARTED)
    
    Raises:
        HTTP 404: Fermentation or protocol not found
        HTTP 403: Fermentation belongs to different winery
        HTTP 422: Invalid request data
        HTTP 409: Fermentation already has an active execution
        HTTP 401: Not authenticated
    """
    try:
        # Create execution DTO from request
        execution_dto = ExecutionStart(
            protocol_id=request.protocol_id,
            fermentation_id=fermentation_id,
            start_date=request.start_date
        )
        
        # Create execution
        created_execution = await execution_repository.create(execution_dto)
        
        return ExecutionResponse(
            id=created_execution.id,
            fermentation_id=created_execution.fermentation_id,
            protocol_id=created_execution.protocol_id,
            winery_id=created_execution.winery_id,
            status=created_execution.status,
            start_date=created_execution.start_date,
            completion_percentage=created_execution.completion_percentage,
            compliance_score=created_execution.compliance_score,
            notes=created_execution.notes,
            created_at=created_execution.created_at,
            updated_at=created_execution.updated_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        if "unique" in str(e).lower() or "already" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Fermentation already has an active execution"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start protocol execution"
        )


@router.patch(
    "/executions/{execution_id}",
    response_model=ExecutionResponse,
    summary="Update protocol execution status",
    description="Updates execution status (ACTIVE, PAUSED, COMPLETED, ABANDONED) or compliance score."
)
async def update_protocol_execution(
    execution_id: Annotated[int, Path(gt=0, description="Execution ID")],
    request: ExecutionUpdateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    execution_repository: Annotated[IProtocolExecutionRepository, Depends(get_execution_repository)]
) -> ExecutionResponse:
    """
    Update a protocol execution.
    
    Args:
        execution_id: ID of the execution to update
        request: Update data (ExecutionUpdate DTO)
        current_user: Authenticated user context
        execution_repository: Execution repository (injected)
    
    Returns:
        ExecutionResponse: Updated execution
    
    Raises:
        HTTP 404: Execution not found
        HTTP 403: Execution belongs to different winery
        HTTP 422: Invalid update data (invalid status, score out of range)
        HTTP 401: Not authenticated
    """
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
        update_data = {k: v for k, v in request.model_dump(exclude_unset=True).items()}
        updated_execution = await execution_repository.update(execution_id, update_data)
        
        if not updated_execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to update execution {execution_id}"
            )
        
        return ExecutionResponse(
            id=updated_execution.id,
            fermentation_id=updated_execution.fermentation_id,
            protocol_id=updated_execution.protocol_id,
            winery_id=updated_execution.winery_id,
            status=updated_execution.status,
            start_date=updated_execution.start_date,
            completion_percentage=updated_execution.completion_percentage,
            compliance_score=updated_execution.compliance_score,
            notes=updated_execution.notes,
            created_at=updated_execution.created_at,
            updated_at=updated_execution.updated_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionResponse,
    summary="Get protocol execution details",
    description="Retrieves detailed execution information including all associated step completions."
)
async def get_protocol_execution(
    execution_id: Annotated[int, Path(gt=0, description="Execution ID")],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    execution_repository: Annotated[IProtocolExecutionRepository, Depends(get_execution_repository)]
) -> ExecutionResponse:
    """
    Get protocol execution details.
    
    Args:
        execution_id: ID of the execution to retrieve
        current_user: Authenticated user context
        execution_repository: Execution repository (injected)
    
    Returns:
        ExecutionResponse: Detailed execution information
    
    Raises:
        HTTP 404: Execution not found
        HTTP 403: Execution belongs to different winery
        HTTP 401: Not authenticated
    """
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
    
    # Return response
    return ExecutionResponse(
        id=execution.id,
        fermentation_id=execution.fermentation_id,
        protocol_id=execution.protocol_id,
        winery_id=execution.winery_id,
        status=execution.status,
        start_date=execution.start_date,
        completion_percentage=execution.completion_percentage,
        compliance_score=execution.compliance_score,
        notes=execution.notes,
        created_at=execution.created_at,
        updated_at=execution.updated_at
    )


@router.get(
    "/executions",
    response_model=ExecutionListResponse,
    summary="List protocol executions with pagination",
    description="Lists all executions for the user's winery with pagination support."
)
async def list_protocol_executions(
    page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    current_user: Annotated[UserContext, Depends(require_winemaker)] = None,
    execution_repository: Annotated[IProtocolExecutionRepository, Depends(get_execution_repository)] = None
) -> ExecutionListResponse:
    """
    List all protocol executions for the authenticated user's winery.
    
    Args:
        page: Page number (1-indexed, default 1)
        page_size: Items per page (default 20, max 100)
        current_user: Authenticated user context
        execution_repository: Execution repository (injected)
    
    Returns:
        ExecutionListResponse: List of executions with pagination metadata
    
    Raises:
        HTTP 422: Invalid pagination parameters
        HTTP 401: Not authenticated
    """
    try:
        executions, total_count = await execution_repository.list_by_winery_paginated(
            winery_id=current_user.winery_id,
            page=page,
            page_size=page_size
        )
        
        items = [
            ExecutionResponse(
                id=e.id,
                fermentation_id=e.fermentation_id,
                protocol_id=e.protocol_id,
                winery_id=e.winery_id,
                status=e.status,
                start_date=e.start_date,
                completion_percentage=e.completion_percentage,
                compliance_score=e.compliance_score,
                notes=e.notes,
                created_at=e.created_at,
                updated_at=e.updated_at
            )
            for e in executions
        ]
        
        return ExecutionListResponse(
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
