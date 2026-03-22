"""
Action Router — REST API for WinemakerAction (ADR-041).

Endpoints:
    POST   /api/v1/fermentations/{fermentation_id}/actions        → record action
    GET    /api/v1/fermentations/{fermentation_id}/actions        → list by fermentation
    GET    /api/v1/executions/{execution_id}/actions              → list by execution
    GET    /api/v1/actions/{action_id}                            → get single action
    PATCH  /api/v1/actions/{action_id}/outcome                    → update outcome
    DELETE /api/v1/actions/{action_id}                            → delete (admin)
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker, require_admin
from src.modules.fermentation.src.api.dependencies import get_db_session
from src.modules.fermentation.src.api.schemas.action_schemas import (
    ActionCreateRequest,
    ActionOutcomeUpdateRequest,
    ActionResponse,
    ActionListResponse,
)
from src.modules.fermentation.src.service_component.services.action_service import (
    ActionService,
    ActionNotFoundError,
)

router = APIRouter(prefix="/api/v1", tags=["winemaker-actions"])


def _get_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ActionService:
    return ActionService(session=session)


# =============================================================================
# POST /fermentations/{fermentation_id}/actions
# =============================================================================

@router.post(
    "/fermentations/{fermentation_id}/actions",
    response_model=ActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a winemaker action",
    description=(
        "Records a corrective or proactive action taken during fermentation. "
        "If alert_id is provided, the linked alert is automatically acknowledged."
    ),
)
async def record_action(
    fermentation_id: Annotated[int, Path(gt=0)],
    body: ActionCreateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[ActionService, Depends(_get_service)],
) -> ActionResponse:
    action = await service.record_action(
        winery_id=current_user.winery_id,
        taken_by_user_id=current_user.user_id,
        action_type=body.action_type.value,
        description=body.description,
        taken_at=body.taken_at,
        fermentation_id=fermentation_id,
        execution_id=body.execution_id,
        step_id=body.step_id,
        alert_id=body.alert_id,
        recommendation_id=body.recommendation_id,
    )
    return ActionResponse.model_validate(action)


# =============================================================================
# GET /fermentations/{fermentation_id}/actions
# =============================================================================

@router.get(
    "/fermentations/{fermentation_id}/actions",
    response_model=ActionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List actions for a fermentation",
)
async def list_fermentation_actions(
    fermentation_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[ActionService, Depends(_get_service)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ActionListResponse:
    items, total = await service.get_actions_for_fermentation(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id,
        skip=skip,
        limit=limit,
    )
    return ActionListResponse(
        items=[ActionResponse.model_validate(a) for a in items],
        total=total,
        skip=skip,
        limit=limit,
    )


# =============================================================================
# GET /executions/{execution_id}/actions
# =============================================================================

@router.get(
    "/executions/{execution_id}/actions",
    response_model=ActionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List actions for a protocol execution",
)
async def list_execution_actions(
    execution_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[ActionService, Depends(_get_service)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ActionListResponse:
    items, total = await service.get_actions_for_execution(
        execution_id=execution_id,
        winery_id=current_user.winery_id,
        skip=skip,
        limit=limit,
    )
    return ActionListResponse(
        items=[ActionResponse.model_validate(a) for a in items],
        total=total,
        skip=skip,
        limit=limit,
    )


# =============================================================================
# GET /actions/{action_id}
# =============================================================================

@router.get(
    "/actions/{action_id}",
    response_model=ActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single winemaker action",
)
async def get_action(
    action_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[ActionService, Depends(_get_service)],
) -> ActionResponse:
    try:
        action = await service.get_action(
            action_id=action_id,
            winery_id=current_user.winery_id,
        )
    except ActionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Action {action_id} not found")
    return ActionResponse.model_validate(action)


# =============================================================================
# PATCH /actions/{action_id}/outcome
# =============================================================================

@router.patch(
    "/actions/{action_id}/outcome",
    response_model=ActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update the outcome of an action",
    description="Record the winemaker's post-action observation (RESOLVED, NO_EFFECT, WORSENED).",
)
async def update_outcome(
    action_id: Annotated[int, Path(gt=0)],
    body: ActionOutcomeUpdateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[ActionService, Depends(_get_service)],
) -> ActionResponse:
    try:
        action = await service.update_outcome(
            action_id=action_id,
            winery_id=current_user.winery_id,
            outcome=body.outcome.value,
            outcome_notes=body.outcome_notes,
        )
    except ActionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Action {action_id} not found")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=str(exc))
    return ActionResponse.model_validate(action)


# =============================================================================
# DELETE /actions/{action_id}
# =============================================================================

@router.delete(
    "/actions/{action_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a winemaker action (admin only)",
)
async def delete_action(
    action_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserContext, Depends(require_admin)],
    service: Annotated[ActionService, Depends(_get_service)],
) -> None:
    try:
        await service.delete_action(
            action_id=action_id,
            winery_id=current_user.winery_id,
        )
    except ActionNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Action {action_id} not found")
