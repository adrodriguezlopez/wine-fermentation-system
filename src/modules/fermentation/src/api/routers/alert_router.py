"""
Protocol Alert Router - REST API endpoints for protocol execution alerts (ADR-040).

Endpoints:
    GET  /api/v1/executions/{execution_id}/alerts          → list alerts (filterable)
    POST /api/v1/executions/{execution_id}/alerts/check    → trigger alert check
    POST /api/v1/alerts/{alert_id}/acknowledge             → acknowledge an alert
    POST /api/v1/alerts/{alert_id}/dismiss                 → dismiss an alert

Following ADR-006 API Layer Design and ADR-040 Notifications & Alerts.
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker
from src.modules.fermentation.src.api.dependencies import get_db_session
from src.modules.fermentation.src.api.schemas.responses import AlertResponse, AlertListResponse
from src.modules.fermentation.src.domain.entities.protocol_alert import ProtocolAlert
from src.modules.fermentation.src.repository_component.protocol_alert_repository import ProtocolAlertRepository
from src.modules.fermentation.src.repository_component.protocol_execution_repository import ProtocolExecutionRepository

router = APIRouter(
    prefix="/api/v1",
    tags=["protocol-alerts"],
)


def get_alert_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> ProtocolAlertRepository:
    """Dependency: ProtocolAlertRepository connected to current DB session."""
    return ProtocolAlertRepository(session=session)


def get_execution_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> ProtocolExecutionRepository:
    """Dependency: ProtocolExecutionRepository for access control checks."""
    return ProtocolExecutionRepository(session=session)


@router.get(
    "/executions/{execution_id}/alerts",
    response_model=AlertListResponse,
    status_code=status.HTTP_200_OK,
    summary="List alerts for a protocol execution",
    description=(
        "Returns alerts for a protocol execution, optionally filtered by status or type. "
        "Includes pending count for badge display. Requires WINEMAKER or ADMIN role."
    ),
)
async def list_execution_alerts(
    execution_id: Annotated[int, Path(gt=0, description="Protocol execution ID")],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    alert_repo: Annotated[ProtocolAlertRepository, Depends(get_alert_repository)],
    execution_repo: Annotated[ProtocolExecutionRepository, Depends(get_execution_repository)],
    status_filter: Annotated[
        Optional[str],
        Query(description="Filter by status: PENDING | SENT | ACKNOWLEDGED | DISMISSED")
    ] = None,
    alert_type: Annotated[
        Optional[str],
        Query(description="Filter by alert type, e.g. STEP_OVERDUE")
    ] = None,
    skip: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max items")] = 50,
) -> AlertListResponse:
    """
    List alerts for a protocol execution with multi-tenancy enforcement.

    Raises:
        HTTP 404: Execution not found
        HTTP 403: Execution belongs to a different winery
    """
    execution = await execution_repo.get_by_id(execution_id)
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol execution {execution_id} not found",
        )
    if execution.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: execution belongs to a different winery",
        )

    alerts = await alert_repo.get_by_execution(
        execution_id=execution_id,
        status=status_filter,
        alert_type=alert_type,
        skip=skip,
        limit=limit,
    )
    pending_count = await alert_repo.count_pending(execution_id)

    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in alerts],
        total=len(alerts),
        pending_count=pending_count,
    )


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Acknowledge a protocol alert",
    description=(
        "Marks the alert as acknowledged by the winemaker. "
        "409 if already acknowledged or dismissed. Requires WINEMAKER or ADMIN role."
    ),
)
async def acknowledge_alert(
    alert_id: Annotated[int, Path(gt=0, description="Alert ID")],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    alert_repo: Annotated[ProtocolAlertRepository, Depends(get_alert_repository)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AlertResponse:
    """
    Acknowledge a protocol alert.

    Raises:
        HTTP 404: Alert not found
        HTTP 403: Alert belongs to a different winery
        HTTP 409: Already acknowledged or dismissed
    """
    alert = await alert_repo.get_by_id(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )
    if alert.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: alert belongs to a different winery",
        )
    if alert.status in ("ACKNOWLEDGED", "DISMISSED"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Alert {alert_id} is already {alert.status.lower()}",
        )

    alert.acknowledge()
    session.add(alert)
    await session.commit()
    await session.refresh(alert)

    return AlertResponse.model_validate(alert)


@router.post(
    "/alerts/{alert_id}/dismiss",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Dismiss a protocol alert",
    description=(
        "Marks the alert as dismissed (won't appear in pending counts). "
        "409 if already acknowledged or dismissed. Requires WINEMAKER or ADMIN role."
    ),
)
async def dismiss_alert(
    alert_id: Annotated[int, Path(gt=0, description="Alert ID")],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    alert_repo: Annotated[ProtocolAlertRepository, Depends(get_alert_repository)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AlertResponse:
    """
    Dismiss a protocol alert.

    Raises:
        HTTP 404: Alert not found
        HTTP 403: Alert belongs to a different winery
        HTTP 409: Already acknowledged or dismissed
    """
    alert = await alert_repo.get_by_id(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )
    if alert.winery_id != current_user.winery_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: alert belongs to a different winery",
        )
    if alert.status in ("ACKNOWLEDGED", "DISMISSED"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Alert {alert_id} is already {alert.status.lower()}",
        )

    alert.dismiss()
    session.add(alert)
    await session.commit()
    await session.refresh(alert)

    return AlertResponse.model_validate(alert)
