from pydantic import BaseModel
from ....models.enums.fermentation_status import FermentationStatus


class UpdateFermentationStatusRequest(BaseModel):
    """Request schema for updating fermentation status"""

    status: FermentationStatus
