"""
Winery API Component - FastAPI routes and schemas.

This component provides HTTP REST API endpoints for winery management.
"""
from src.modules.winery.src.api_component.routers.winery_router import router as winery_router

__all__ = ["winery_router"]
