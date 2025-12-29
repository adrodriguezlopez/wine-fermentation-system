"""
Error Handlers for Fruit Origin API

Maps domain exceptions to HTTP responses.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi import FastAPI

from src.shared.domain.errors import (
    VineyardNotFound,
    VineyardHasActiveLotsError,
    VineyardBlockNotFound,
    HarvestLotNotFound,
    DuplicateCodeError,
)


def register_error_handlers(app: FastAPI) -> None:
    """
    Register exception handlers with FastAPI app.
    
    Maps domain errors to appropriate HTTP status codes:
    - NotFound errors → 404
    - Duplicate errors → 409 Conflict
    - Business rule violations → 409 Conflict
    - Invalid data → 400 Bad Request
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(VineyardNotFound)
    async def vineyard_not_found_handler(
        request: Request, 
        exc: VineyardNotFound
    ) -> JSONResponse:
        """Handle vineyard not found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "error_type": "VineyardNotFound"}
        )
    
    @app.exception_handler(VineyardBlockNotFound)
    async def vineyard_block_not_found_handler(
        request: Request,
        exc: VineyardBlockNotFound
    ) -> JSONResponse:
        """Handle vineyard block not found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "error_type": "VineyardBlockNotFound"}
        )
    
    @app.exception_handler(HarvestLotNotFound)
    async def harvest_lot_not_found_handler(
        request: Request,
        exc: HarvestLotNotFound
    ) -> JSONResponse:
        """Handle harvest lot not found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "error_type": "HarvestLotNotFound"}
        )
    
    @app.exception_handler(DuplicateCodeError)
    async def duplicate_code_handler(
        request: Request,
        exc: DuplicateCodeError
    ) -> JSONResponse:
        """Handle duplicate code errors."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc), "error_type": "DuplicateCodeError"}
        )
    
    @app.exception_handler(VineyardHasActiveLotsError)
    async def vineyard_has_active_lots_handler(
        request: Request,
        exc: VineyardHasActiveLotsError
    ) -> JSONResponse:
        """Handle vineyard with active lots deletion attempts."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": str(exc),
                "error_type": "VineyardHasActiveLotsError"
            }
        )
