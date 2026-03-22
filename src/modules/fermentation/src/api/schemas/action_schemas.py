"""
Request / Response schemas for WinemakerAction (ADR-041).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from src.modules.fermentation.src.domain.enums.step_type import ActionType, ActionOutcome


# =============================================================================
# Request schemas
# =============================================================================

class ActionCreateRequest(BaseModel):
    """Payload for POST /fermentations/{ferm_id}/actions."""

    action_type: ActionType = Field(
        ..., description="Category of action taken"
    )
    description: str = Field(
        ..., min_length=1, max_length=2000,
        description="Free-text description of what the winemaker did"
    )
    taken_at: datetime = Field(
        ..., description="When the action was physically taken (may be in the past)"
    )

    # Optional contextual links
    execution_id: Optional[int] = Field(
        None, gt=0, description="Protocol execution this action relates to"
    )
    step_id: Optional[int] = Field(
        None, gt=0, description="Specific protocol step this action targets"
    )
    alert_id: Optional[int] = Field(
        None, gt=0,
        description="Alert that triggered this action (auto-acknowledges the alert)"
    )
    recommendation_id: Optional[int] = Field(
        None, gt=0, description="Analysis recommendation that prompted this action"
    )


class ActionOutcomeUpdateRequest(BaseModel):
    """Payload for PATCH /actions/{action_id}/outcome."""

    outcome: ActionOutcome = Field(
        ..., description="Observed result after taking the action"
    )
    outcome_notes: Optional[str] = Field(
        None, max_length=2000,
        description="Additional observations about the outcome"
    )


# =============================================================================
# Response schemas
# =============================================================================

class ActionResponse(BaseModel):
    """Single WinemakerAction serialised for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    winery_id: int
    taken_by_user_id: int

    action_type: str
    description: str
    taken_at: datetime

    fermentation_id: Optional[int] = None
    execution_id: Optional[int] = None
    step_id: Optional[int] = None
    alert_id: Optional[int] = None
    recommendation_id: Optional[int] = None

    outcome: str
    outcome_notes: Optional[str] = None
    outcome_recorded_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime


class ActionListResponse(BaseModel):
    """Paginated list of WinemakerAction entries."""

    items: List[ActionResponse]
    total: int
    skip: int
    limit: int
