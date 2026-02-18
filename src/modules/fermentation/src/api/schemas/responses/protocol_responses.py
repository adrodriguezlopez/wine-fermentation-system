"""
Protocol API Response Schemas (Phase 2)

Pydantic models for serializing protocol responses with proper
pagination, status information, and nested structures.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class StepResponse(BaseModel):
    """Response DTO for a protocol step"""
    
    id: int = Field(..., description="Step ID")
    protocol_id: int = Field(..., description="Parent protocol ID")
    step_order: int = Field(..., description="Order in protocol")
    step_type: str = Field(..., description="Step category")
    description: str = Field(..., description="Step details")
    expected_day: int = Field(..., description="Expected day")
    tolerance_hours: int = Field(..., description="Time tolerance")
    duration_minutes: int = Field(..., description="Step duration")
    criticality_score: float = Field(..., description="Importance 0-100")
    can_repeat_daily: bool = Field(..., description="Repeatable daily")
    depends_on_step_id: Optional[int] = Field(None, description="Dependency")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class StepListResponse(BaseModel):
    """Paginated list of protocol steps"""
    
    items: List[StepResponse] = Field(..., description="Step list")
    total_count: int = Field(..., ge=0, description="Total steps")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total pages")


class ProtocolResponse(BaseModel):
    """Response DTO for a protocol"""
    
    id: int = Field(..., description="Protocol ID")
    winery_id: int = Field(..., description="Winery ID")
    varietal_code: str = Field(..., description="Varietal code")
    varietal_name: str = Field(..., description="Varietal name")
    color: str = Field(..., description="Wine color")
    version: str = Field(..., description="Semantic version")
    protocol_name: str = Field(..., description="Protocol name")
    is_active: bool = Field(..., description="Active status")
    expected_duration_days: int = Field(..., description="Expected duration")
    description: Optional[str] = Field(None, description="Protocol description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ProtocolListResponse(BaseModel):
    """Paginated list of protocols"""
    
    items: List[ProtocolResponse] = Field(..., description="Protocol list")
    total_count: int = Field(..., ge=0, description="Total protocols")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total pages")


class ExecutionResponse(BaseModel):
    """Response DTO for a protocol execution"""
    
    id: int = Field(..., description="Execution ID")
    fermentation_id: int = Field(..., description="Fermentation ID")
    protocol_id: int = Field(..., description="Protocol ID")
    winery_id: int = Field(..., description="Winery ID")
    status: str = Field(..., description="Execution status")
    start_date: datetime = Field(..., description="Start date")
    completion_percentage: float = Field(..., ge=0, le=100, description="Progress")
    compliance_score: float = Field(..., ge=0, le=100, description="Compliance")
    notes: Optional[str] = Field(None, description="Execution notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    """Paginated list of protocol executions"""
    
    items: List[ExecutionResponse] = Field(..., description="Execution list")
    total_count: int = Field(..., ge=0, description="Total executions")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total pages")


class CompletionResponse(BaseModel):
    """Response DTO for a step completion record"""
    
    id: int = Field(..., description="Completion ID")
    execution_id: int = Field(..., description="Execution ID")
    step_id: int = Field(..., description="Step ID")
    winery_id: int = Field(..., description="Winery ID")
    was_skipped: bool = Field(..., description="Skip status")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    is_on_schedule: bool = Field(..., description="Schedule compliance")
    days_late: int = Field(..., ge=0, description="Days past due")
    skip_reason: Optional[str] = Field(None, description="Skip reason if applicable")
    skip_notes: Optional[str] = Field(None, description="Skip notes")
    notes: Optional[str] = Field(None, description="Completion notes")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class CompletionListResponse(BaseModel):
    """Paginated list of step completions"""
    
    items: List[CompletionResponse] = Field(..., description="Completion list")
    total_count: int = Field(..., ge=0, description="Total completions")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total pages")
