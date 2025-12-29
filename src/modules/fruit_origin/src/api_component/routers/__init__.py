"""
API Routers for Fruit Origin module.
"""
from src.modules.fruit_origin.src.api_component.routers.vineyard_router import router as vineyard_router
from src.modules.fruit_origin.src.api_component.routers.harvest_lot_router import router as harvest_lot_router

__all__ = ["vineyard_router", "harvest_lot_router"]
