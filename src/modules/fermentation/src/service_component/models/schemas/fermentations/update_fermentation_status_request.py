from pydantic import BaseModel
from ...enums import FermentationStatus

class UpdateFermentationStatusRequest(BaseModel):
    """Request schema for updating fermentation status"""
    status: FermentationStatus