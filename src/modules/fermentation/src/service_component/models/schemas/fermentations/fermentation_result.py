from datetime import datetime
from domain.enums.fermentation_status import FermentationStatus
from .fermentation_base import FermentationBase


class FermentationResult(FermentationBase):
    """Response schema for fermentation data"""

    id: int
    fermented_by_user_id: int
    status: FermentationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
