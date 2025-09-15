from pydantic import BaseModel
from domain.enums.fermentation_status import FermentationStatus


class UpdateFermentationStatusRequest(BaseModel):
    """Request schema for updating fermentation status"""

    status: FermentationStatus
