"""
Dependency injection for Winery API.
"""
from src.modules.winery.src.api_component.dependencies.services import get_winery_service

__all__ = ["get_winery_service"]
