"""
Request DTOs for Winery API.
"""
from src.modules.winery.src.api_component.schemas.requests.winery_requests import (
    WineryCreateRequest,
    WineryUpdateRequest
)

__all__ = ["WineryCreateRequest", "WineryUpdateRequest"]
