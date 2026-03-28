"""
Advisory Router - REST API endpoints for managing Protocol Advisories (ADR-037).

Endpoints:
    GET    /api/v1/fermentations/{fermentation_id}/advisories  → list advisories for a fermentation
    POST   /api/v1/advisories/{advisory_id}/acknowledge        → acknowledge an advisory

Protocol Advisories are generated automatically by the Analysis Engine when anomalies
indicate that the active protocol should be adjusted (step acceleration, skipping, or
addition). The winemaker acknowledges them to confirm the suggestion has been reviewed.

Following ADR-006 API Layer Design, ADR-020 Analysis Engine Architecture, and
ADR-037 Protocol↔Analysis Integration.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker
from src.shared.infra.database.fastapi_session import get_db_session

from src.modules.analysis_engine.src.api.dependencies import get_protocol_advisory_repository
from src.modules.analysis_engine.src.api.error_handlers import handle_service_errors
from src.modules.analysis_engine.src.api.schemas.responses.analysis_responses import (
    ProtocolAdvisoryResponse,
    ProtocolAdvisoryListResponse,
)
from src.modules.analysis_engine.src.repository_component.repositories.protocol_advisory_repository import (
    ProtocolAdvisoryRepository,
)

router = APIRouter(tags=["protocol-advisories"])


@router.get(
    "/fermentations/{fermentation_id}/advisories",
    response_model=ProtocolAdvisoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List protocol advisories for a fermentation",
    description=(
        "Returns all protocol advisories generated for a fermentation, with optional "
        "filtering by acknowledgement status. Advisories are ordered newest-first. "
        "Requires WINEMAKER or ADMIN role."
    ),
)
@handle_service_errors
async def list_advisories(
    fermentation_id: Annotated[UUID, Path(description="Fermentation UUID")],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    repo: Annotated[ProtocolAdvisoryRepository, Depends(get_protocol_advisory_repository)],
    include_acknowledged: Annotated[
        bool,
        Query(description="Include already-acknowledged advisories (default: true)")
    ] = True,
    skip: Annotated[int, Query(description="Pagination offset", ge=0)] = 0,
    limit: Annotated[int, Query(description="Maximum items to return", ge=1, le=100)] = 50,
) -> ProtocolAdvisoryListResponse:
    """
    List protocol advisories for a fermentation.

    Args:
        fermentation_id: UUID of the fermentation to query
        current_user: Authenticated user context
        repo: Protocol advisory repository
        include_acknowledged: Whether to include already-acknowledged advisories
        skip: Pagination offset
        limit: Maximum items per page

    Returns:
        ProtocolAdvisoryListResponse: Paginated list with unacknowledged count

    Raises:
        HTTP 401: Not authenticated
        HTTP 403: Insufficient permissions
    """
    advisories = await repo.get_by_fermentation_id(
        fermentation_id=fermentation_id,
        include_acknowledged=include_acknowledged,
        skip=skip,
        limit=limit,
    )
    unacknowledged_count = await repo.count_unacknowledged(fermentation_id)

    return ProtocolAdvisoryListResponse(
        items=[ProtocolAdvisoryResponse.model_validate(a) for a in advisories],
        total=len(advisories),
        unacknowledged_count=unacknowledged_count,
    )


@router.post(
    "/advisories/{advisory_id}/acknowledge",
    response_model=ProtocolAdvisoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Acknowledge a protocol advisory",
    description=(
        "The winemaker confirms they have reviewed this advisory. "
        "Records the acknowledgement timestamp. "
        "Requires WINEMAKER or ADMIN role."
    ),
)
@handle_service_errors
async def acknowledge_advisory(
    advisory_id: Annotated[UUID, Path(description="Advisory UUID to acknowledge")],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    repo: Annotated[ProtocolAdvisoryRepository, Depends(get_protocol_advisory_repository)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProtocolAdvisoryResponse:
    """
    Acknowledge a protocol advisory.

    Records the winemaker's confirmation that they have reviewed the advisory.
    Once acknowledged, the advisory will no longer appear in the pending count.

    Args:
        advisory_id: UUID of the advisory to acknowledge
        current_user: Authenticated user context
        repo: Protocol advisory repository
        session: Database session (for commit after entity mutation)

    Returns:
        ProtocolAdvisoryResponse: Updated advisory with is_acknowledged=True

    Raises:
        HTTP 401: Not authenticated
        HTTP 403: Insufficient permissions
        HTTP 404: Advisory not found
        HTTP 409: Advisory already acknowledged
    """
    advisory = await repo.get_by_id(advisory_id)

    if advisory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol advisory {advisory_id} not found",
        )

    if advisory.is_acknowledged:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Protocol advisory {advisory_id} has already been acknowledged",
        )

    # Acknowledge the advisory (sets is_acknowledged=True and acknowledged_at=now)
    advisory.acknowledge()

    # Persist the change
    session.add(advisory)
    await session.commit()
    await session.refresh(advisory)

    return ProtocolAdvisoryResponse.model_validate(advisory)
