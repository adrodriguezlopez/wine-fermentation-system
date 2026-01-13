"""
API Router for Historical Data endpoints.

Provides REST API for querying historical fermentation data, extracting patterns,
and managing ETL imports.

Related ADR: ADR-032 (Historical Data API Layer)
"""
from typing import Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import JSONResponse

from src.shared.wine_fermentator_logging import get_logger
from src.modules.fermentation.src.service_component.services.historical.historical_data_service import HistoricalDataService
from src.modules.fermentation.src.api_component.historical.schemas.requests.historical_requests import (
    HistoricalFermentationQueryRequest,
    PatternExtractionRequest
)
from src.modules.fermentation.src.api_component.historical.schemas.responses.historical_responses import (
    HistoricalFermentationResponse,
    PaginatedHistoricalFermentationsResponse,
    HistoricalSampleResponse,
    PatternResponse,
    StatisticsResponse,
    ImportJobResponse,
    ImportTriggerResponse
)
from src.modules.fermentation.src.service_component.errors import NotFoundError

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/fermentation/historical",
    tags=["Historical Data"]
)


def get_winery_id(x_winery_id: int = Header(..., alias="X-Winery-ID")) -> int:
    """Extract winery ID from request header.
    
    TODO: This should be replaced with proper authentication/authorization
    middleware that extracts winery_id from JWT token claims.
    """
    return x_winery_id


def get_historical_data_service() -> HistoricalDataService:
    """Dependency injection for HistoricalDataService.
    
    TODO: Implement proper dependency injection with repository instances.
    This is a placeholder that will be replaced with actual DI container.
    """
    # This will be replaced with proper DI in integration
    raise NotImplementedError("Service dependency injection not yet configured")


@router.get(
    "",
    response_model=PaginatedHistoricalFermentationsResponse,
    status_code=status.HTTP_200_OK,
    summary="List historical fermentations",
    description="Query historical fermentation data with optional filters and pagination"
)
async def list_historical_fermentations(
    winery_id: int = Depends(get_winery_id),
    start_date_from: Optional[date] = Query(None, description="Filter by start date (from)"),
    start_date_to: Optional[date] = Query(None, description="Filter by start date (to)"),
    fruit_origin_id: Optional[int] = Query(None, description="Filter by fruit origin"),
    status: Optional[str] = Query(None, description="Filter by fermentation status"),
    limit: int = Query(100, ge=1, le=1000, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> PaginatedHistoricalFermentationsResponse:
    """List historical fermentations with filters and pagination."""
    logger.info(
        "Listing historical fermentations",
        extra={
            "winery_id": winery_id,
            "filters": {
                "start_date_from": start_date_from,
                "start_date_to": start_date_to,
                "fruit_origin_id": fruit_origin_id,
                "status": status
            },
            "limit": limit,
            "offset": offset
        }
    )
    
    # Build filters dict
    filters = {}
    if start_date_from:
        filters["start_date_from"] = start_date_from
    if start_date_to:
        filters["start_date_to"] = start_date_to
    if fruit_origin_id:
        filters["fruit_origin_id"] = fruit_origin_id
    if status:
        filters["status"] = status
    
    try:
        # Get fermentations from service
        fermentations = await service.get_historical_fermentations(
            winery_id=winery_id,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        # Convert to response DTOs
        items = [HistoricalFermentationResponse.from_entity(f) for f in fermentations]
        
        # For now, total equals the returned count (pagination TODO: add total count to service)
        # In production, service should return (items, total_count) tuple
        total = len(items) + offset  # Approximate
        
        logger.info(
            "Retrieved historical fermentations",
            extra={"winery_id": winery_id, "count": len(items), "total": total}
        )
        
        return PaginatedHistoricalFermentationsResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(
            "Error listing historical fermentations",
            extra={"winery_id": winery_id, "error": str(e)},
            exc_info=True
        )
        from fastapi import status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve historical fermentations"
        )


@router.get(
    "/import",
    response_model=list[ImportJobResponse],
    status_code=status.HTTP_200_OK,
    summary="List import jobs",
    description="Retrieve a list of ETL import jobs for the winery"
)
async def list_import_jobs(
    winery_id: int = Depends(get_winery_id),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset")
) -> list[ImportJobResponse]:
    """List ETL import jobs with pagination.
    
    NOTE: This is a placeholder endpoint. Actual ETL implementation will be
    added in future phases (ADR-031 ETL Pipeline Integration).
    """
    logger.info(
        "Listing import jobs",
        extra={"winery_id": winery_id, "limit": limit, "offset": offset}
    )
    
    # TODO: Implement actual job listing
    # For now, return empty list
    return []


@router.get(
    "/{fermentation_id}",
    response_model=HistoricalFermentationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get historical fermentation by ID",
    description="Retrieve a single historical fermentation by its ID"
)
async def get_historical_fermentation(
    fermentation_id: int,
    winery_id: int = Depends(get_winery_id),
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> HistoricalFermentationResponse:
    """Get a single historical fermentation by ID."""
    logger.info(
        "Getting historical fermentation",
        extra={"winery_id": winery_id, "fermentation_id": fermentation_id}
    )
    
    try:
        fermentation = await service.get_historical_fermentation_by_id(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        logger.info(
            "Retrieved historical fermentation",
            extra={"winery_id": winery_id, "fermentation_id": fermentation_id}
        )
        
        return HistoricalFermentationResponse.from_entity(fermentation)
        
    except NotFoundError as e:
        logger.warning(
            "Historical fermentation not found",
            extra={"winery_id": winery_id, "fermentation_id": fermentation_id}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Error getting historical fermentation",
            extra={"winery_id": winery_id, "fermentation_id": fermentation_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve historical fermentation"
        )


@router.get(
    "/{fermentation_id}/samples",
    response_model=list[HistoricalSampleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get samples for historical fermentation",
    description="Retrieve all samples associated with a historical fermentation"
)
async def get_fermentation_samples(
    fermentation_id: int,
    winery_id: int = Depends(get_winery_id),
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> list[HistoricalSampleResponse]:
    """Get all samples for a historical fermentation."""
    logger.info(
        "Getting fermentation samples",
        extra={"winery_id": winery_id, "fermentation_id": fermentation_id}
    )
    
    try:
        samples = await service.get_fermentation_samples(
            fermentation_id=fermentation_id,
            winery_id=winery_id
        )
        
        logger.info(
            "Retrieved fermentation samples",
            extra={
                "winery_id": winery_id,
                "fermentation_id": fermentation_id,
                "count": len(samples)
            }
        )
        
        return [HistoricalSampleResponse.from_entity(s) for s in samples]
        
    except NotFoundError as e:
        logger.warning(
            "Historical fermentation not found for samples",
            extra={"winery_id": winery_id, "fermentation_id": fermentation_id}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Error getting fermentation samples",
            extra={"winery_id": winery_id, "fermentation_id": fermentation_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve fermentation samples"
        )


@router.get(
    "/patterns/extract",
    response_model=PatternResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract patterns from historical data",
    description="Analyze historical fermentation data to extract patterns for the Analysis Engine (ADR-020)"
)
async def extract_patterns(
    winery_id: int = Depends(get_winery_id),
    fruit_origin_id: Optional[int] = Query(None, description="Filter by fruit origin"),
    start_date: Optional[date] = Query(None, description="Start date for analysis range"),
    end_date: Optional[date] = Query(None, description="End date for analysis range"),
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> PatternResponse:
    """Extract aggregated patterns from historical fermentation data.
    
    This endpoint is designed for the Analysis Engine to consume historical
    patterns for predictive modeling and recommendations.
    """
    logger.info(
        "Extracting patterns from historical data",
        extra={
            "winery_id": winery_id,
            "fruit_origin_id": fruit_origin_id,
            "date_range": {"start": start_date, "end": end_date}
        }
    )
    
    try:
        # Build date range filter as tuple for service
        date_range = None
        if start_date and end_date:
            date_range = (start_date, end_date)
        
        # Extract patterns from service
        patterns_dict = await service.extract_patterns(
            winery_id=winery_id,
            fruit_origin_id=fruit_origin_id,
            date_range=date_range
        )
        
        logger.info(
            "Extracted patterns from historical data",
            extra={
                "winery_id": winery_id,
                "total_fermentations": patterns_dict.get("total_fermentations", 0)
            }
        )
        
        # Convert dict to Pydantic response
        return PatternResponse(**patterns_dict)
        
    except Exception as e:
        logger.error(
            "Error extracting patterns",
            extra={"winery_id": winery_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract patterns from historical data"
        )


@router.get(
    "/statistics/dashboard",
    response_model=StatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard statistics",
    description="Retrieve aggregated statistics from historical data for dashboard display"
)
async def get_dashboard_statistics(
    winery_id: int = Depends(get_winery_id),
    service: HistoricalDataService = Depends(get_historical_data_service)
) -> StatisticsResponse:
    """Get aggregated statistics for dashboard display.
    
    TODO: This endpoint needs a dedicated service method for dashboard-specific
    metrics. For now, it reuses extract_patterns() which may not have all needed fields.
    """
    logger.info(
        "Getting dashboard statistics",
        extra={"winery_id": winery_id}
    )
    
    try:
        # Reuse pattern extraction for now
        # TODO: Create dedicated get_statistics() method in service
        patterns_dict = await service.extract_patterns(
            winery_id=winery_id,
            fruit_origin_id=None,
            date_range=None
        )
        
        # Map to StatisticsResponse (simplified for now)
        stats = StatisticsResponse(
            total_fermentations=patterns_dict.get("total_fermentations", 0),
            avg_duration_days=patterns_dict.get("avg_duration_days"),
            success_rate=patterns_dict.get("success_rate", 0.0),
            total_volume_liters=None,  # TODO: Calculate from fermentation data
            most_common_yeast=None  # TODO: Query most common yeast strain
        )
        
        logger.info(
            "Retrieved dashboard statistics",
            extra={"winery_id": winery_id, "total_fermentations": stats.total_fermentations}
        )
        
        return stats
        
    except Exception as e:
        logger.error(
            "Error getting dashboard statistics",
            extra={"winery_id": winery_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )


@router.post(
    "/import",
    response_model=ImportTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger ETL import job",
    description="Start a new ETL import job to load historical data from external sources"
)
async def trigger_import(
    winery_id: int = Depends(get_winery_id)
) -> ImportTriggerResponse:
    """Trigger a new ETL import job.
    
    NOTE: This is a placeholder endpoint. Actual ETL implementation will be
    added in future phases (ADR-031 ETL Pipeline Integration).
    """
    logger.info(
        "Triggering ETL import job",
        extra={"winery_id": winery_id}
    )
    
    # TODO: Implement actual ETL job triggering
    # For now, return a mock response
    return ImportTriggerResponse(
        job_id=999,
        status="pending",
        message="ETL import functionality not yet implemented (ADR-031)"
    )


@router.get(
    "/import/{job_id}",
    response_model=ImportJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get import job status",
    description="Retrieve the status and progress of an ETL import job"
)
async def get_import_job_status(
    job_id: int,
    winery_id: int = Depends(get_winery_id)
) -> ImportJobResponse:
    """Get the status of an ETL import job.
    
    NOTE: This is a placeholder endpoint. Actual ETL implementation will be
    added in future phases (ADR-031 ETL Pipeline Integration).
    """
    logger.info(
        "Getting import job status",
        extra={"winery_id": winery_id, "job_id": job_id}
    )
    
    # TODO: Implement actual job status retrieval
    # For now, return a mock response
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="ETL import functionality not yet implemented (ADR-031)"
    )
