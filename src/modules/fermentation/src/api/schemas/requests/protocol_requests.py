"""
Protocol API Request Schemas (Phase 2)

Pydantic models for validating incoming requests to protocol endpoints.
Implements semantic versioning, step type validation, and business rules.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ProtocolCreateRequest(BaseModel):
    """Request DTO for creating a new fermentation protocol"""
    
    varietal_code: str = Field(
        ...,
        min_length=1,
        max_length=4,
        description="Varietal code (e.g., 'PN', 'CS')"
    )
    
    varietal_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full varietal name (e.g., 'Pinot Noir')"
    )
    
    color: str = Field(
        ...,
        description="Wine color: RED, WHITE, or ROSÉ"
    )
    
    version: str = Field(
        ...,
        description="Semantic version (e.g., '1.0', '2.1')"
    )
    
    protocol_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable protocol name"
    )
    
    expected_duration_days: int = Field(
        ...,
        gt=0,
        description="Expected fermentation duration in days"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Detailed protocol description"
    )
    
    @field_validator("color")
    @classmethod
    def validate_color(cls, v):
        if v not in ("RED", "WHITE", "ROSÉ"):
            raise ValueError("color must be RED, WHITE, or ROSÉ")
        return v
    
    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        import re
        if not re.match(r"^\d+\.\d+$", v):
            raise ValueError("version must be semantic format (e.g., '1.0')")
        return v


class ProtocolUpdateRequest(BaseModel):
    """Request DTO for updating a protocol"""
    
    protocol_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated protocol name"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Updated description"
    )
    
    expected_duration_days: Optional[int] = Field(
        None,
        gt=0,
        description="Updated expected duration"
    )


class StepCreateRequest(BaseModel):
    """Request DTO for adding a step to a protocol"""
    
    step_order: int = Field(
        ...,
        gt=0,
        description="Position in protocol (1-indexed)"
    )
    
    step_type: str = Field(
        ...,
        description="Step category (INITIALIZATION, MONITORING, ADDITIONS, CAP_MANAGEMENT, POST_FERMENTATION, QUALITY_CHECK)"
    )
    
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Specific step details"
    )
    
    expected_day: int = Field(
        ...,
        ge=0,
        description="Day when step occurs"
    )
    
    tolerance_hours: int = Field(
        ...,
        ge=0,
        description="Hours before/after expected day"
    )
    
    duration_minutes: int = Field(
        ...,
        gt=0,
        description="How long step takes"
    )
    
    criticality_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Importance score 0-100"
    )
    
    can_repeat_daily: bool = Field(
        False,
        description="Whether step repeats each day"
    )
    
    depends_on_step_id: Optional[int] = Field(
        None,
        description="Optional dependency on previous step"
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Additional notes"
    )
    
    @field_validator("step_type")
    @classmethod
    def validate_step_type(cls, v):
        valid_types = {
            "INITIALIZATION", "MONITORING", "ADDITIONS",
            "CAP_MANAGEMENT", "POST_FERMENTATION", "QUALITY_CHECK"
        }
        if v not in valid_types:
            raise ValueError(f"step_type must be one of {valid_types}")
        return v


class StepUpdateRequest(BaseModel):
    """Request DTO for updating a protocol step"""
    
    description: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Updated step details"
    )
    
    expected_day: Optional[int] = Field(
        None,
        ge=0,
        description="Updated day"
    )
    
    tolerance_hours: Optional[int] = Field(
        None,
        ge=0,
        description="Updated tolerance"
    )
    
    duration_minutes: Optional[int] = Field(
        None,
        gt=0,
        description="Updated duration"
    )
    
    criticality_score: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Updated criticality"
    )
    
    can_repeat_daily: Optional[bool] = None
    depends_on_step_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=500)


class ExecutionStartRequest(BaseModel):
    """Request DTO for starting a protocol execution"""
    
    protocol_id: int = Field(
        ...,
        gt=0,
        description="Protocol to execute"
    )
    
    start_date: Optional[datetime] = Field(
        None,
        description="When execution starts"
    )


class ExecutionUpdateRequest(BaseModel):
    """Request DTO for updating protocol execution"""
    
    status: Optional[str] = Field(
        None,
        description="New status (NOT_STARTED, ACTIVE, PAUSED, COMPLETED, ABANDONED)"
    )
    
    compliance_score: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Updated compliance score"
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Execution notes"
    )


class CompletionCreateRequest(BaseModel):
    """Request DTO for marking a step complete or skipped"""
    
    step_id: int = Field(
        ...,
        gt=0,
        description="Step being completed"
    )
    
    was_skipped: bool = Field(
        False,
        description="Whether step was skipped"
    )
    
    completed_at: Optional[datetime] = Field(
        None,
        description="When step was completed (required if not skipped)"
    )
    
    is_on_schedule: bool = Field(
        True,
        description="Whether completed on expected day"
    )
    
    days_late: int = Field(
        0,
        ge=0,
        description="Days past expected date"
    )
    
    skip_reason: Optional[str] = Field(
        None,
        description="Why step was skipped (required if was_skipped=True)"
    )
    
    skip_notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Notes about skip"
    )
    
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Completion notes"
    )
    
    @field_validator("skip_reason")
    @classmethod
    def validate_skip_reason(cls, v, values):
        if values.data.get("was_skipped") and not v:
            raise ValueError("skip_reason is required when was_skipped=True")
        
        if v:
            valid_reasons = {
                "EQUIPMENT_MALFUNCTION", "WEATHER_CONDITIONS",
                "QUALITY_ISSUE", "RESOURCE_UNAVAILABLE", "OTHER"
            }
            if v not in valid_reasons:
                raise ValueError(f"skip_reason must be one of {valid_reasons}")
        return v
    
    @field_validator("completed_at")
    @classmethod
    def validate_completed_at(cls, v, values):
        if not values.data.get("was_skipped") and not v:
            raise ValueError("completed_at is required when was_skipped=False")
        return v
