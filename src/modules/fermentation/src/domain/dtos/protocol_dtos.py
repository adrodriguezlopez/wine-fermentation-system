"""
Protocol Data Transfer Objects.

Pure Python dataclasses for protocol data transfer between layers.
No framework dependencies (no Pydantic, no SQLAlchemy).

DTOs for:
- FermentationProtocol (CRUD operations)
- ProtocolStep (step creation/updates)
- ProtocolExecution (start execution, track status)
- StepCompletion (mark steps completed)

Validation:
- Semantic versioning (regex: ^\d+\.\d+$)
- Positive durations
- Criticality score 0-100
- Skip reason required when skipped
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
import re


def validate_semantic_version(version: str) -> None:
    """Validate version is semantic format (e.g., '1.0', '2.1')."""
    if not re.match(r'^\d+\.\d+$', version):
        raise ValueError(f"Version must be semantic format (e.g., '1.0'). Got: {version}")


def validate_positive_int(value: int, field_name: str) -> None:
    """Validate integer is positive."""
    if value <= 0:
        raise ValueError(f"{field_name} must be positive. Got: {value}")


def validate_score_range(value: float, field_name: str) -> None:
    """Validate value is between 0 and 100."""
    if not (0 <= value <= 100):
        raise ValueError(f"{field_name} must be 0-100. Got: {value}")


# ============================================================================
# Enums (for API request/response serialization)
# ============================================================================

class StepTypeDTO(str, Enum):
    """DTO representation of StepType categories"""
    INITIALIZATION = "INITIALIZATION"
    MONITORING = "MONITORING"
    ADDITIONS = "ADDITIONS"
    CAP_MANAGEMENT = "CAP_MANAGEMENT"
    POST_FERMENTATION = "POST_FERMENTATION"
    QUALITY_CHECK = "QUALITY_CHECK"


class ProtocolExecutionStatusDTO(str, Enum):
    """DTO representation of ProtocolExecutionStatus"""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"


class SkipReasonDTO(str, Enum):
    """DTO representation of SkipReason"""
    EQUIPMENT_MALFUNCTION = "EQUIPMENT_MALFUNCTION"
    WEATHER_CONDITIONS = "WEATHER_CONDITIONS"
    QUALITY_ISSUE = "QUALITY_ISSUE"
    RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"
    OTHER = "OTHER"


# ============================================================================
# Protocol DTOs
# ============================================================================

@dataclass
class ProtocolCreate:
    """
    DTO for creating a new fermentation protocol.
    
    A protocol is a master template defining fermentation steps for a varietal.
    
    Attributes:
        winery_id: Owning winery
        varietal_code: Short code (e.g., "PN", "CS")
        varietal_name: Full name (e.g., "Pinot Noir")
        color: Wine color ("RED", "WHITE", "ROSÉ")
        version: Semantic version (e.g., "1.0", "2.1")
        protocol_name: Human-readable name
        description: Long description
        expected_duration_days: Estimated fermentation duration
    """
    winery_id: int
    varietal_code: str
    varietal_name: str
    color: str
    version: str
    protocol_name: str
    expected_duration_days: int
    created_by_user_id: int
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate protocol creation data."""
        validate_semantic_version(self.version)
        validate_positive_int(self.expected_duration_days, "expected_duration_days")
        
        # Validate color
        if self.color not in ("RED", "WHITE", "ROSÉ"):
            raise ValueError(f"color must be RED, WHITE, or ROSÉ. Got: {self.color}")
        
        # Validate required fields not empty
        if not self.varietal_code.strip():
            raise ValueError("varietal_code cannot be empty")
        if not self.varietal_name.strip():
            raise ValueError("varietal_name cannot be empty")
        if not self.protocol_name.strip():
            raise ValueError("protocol_name cannot be empty")


@dataclass
class ProtocolUpdate:
    """
    DTO for updating an existing protocol.
    
    All fields optional for partial updates.
    """
    protocol_name: Optional[str] = None
    description: Optional[str] = None
    expected_duration_days: Optional[int] = None
    is_active: Optional[bool] = None


@dataclass
class ProtocolResponse:
    """
    DTO for protocol API responses.
    
    Attributes:
        id: Protocol ID
        winery_id: Owning winery
        varietal_code: Short code
        varietal_name: Full name
        color: Wine color
        version: Semantic version
        protocol_name: Human-readable name
        description: Long description
        expected_duration_days: Estimated duration
        is_active: Whether protocol is in use
        created_by_user_id: User who created
        created_at: Creation timestamp
        updated_at: Last update timestamp
        step_count: Number of steps in protocol
    """
    id: int
    winery_id: int
    varietal_code: str
    varietal_name: str
    color: str
    version: str
    protocol_name: str
    expected_duration_days: int
    is_active: bool
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    step_count: int = 0


# ============================================================================
# Protocol Step DTOs
# ============================================================================

@dataclass
class StepCreate:
    """
    DTO for adding a step to a protocol.
    
    Attributes:
        protocol_id: Parent protocol
        step_order: Position in protocol (1-indexed)
        step_type: Category (INITIALIZATION, MONITORING, etc.)
        description: Specific step details (e.g., "Yeast Inoculation - Red Star")
        expected_day: Day when step occurs
        tolerance_hours: Hours before/after expected day that step is valid
        duration_minutes: How long step takes
        criticality_score: 0-100 importance score
        can_repeat_daily: Whether step repeats each day
        depends_on_step_id: Optional dependency on previous step
        notes: Additional notes
    """
    protocol_id: int
    step_order: int
    step_type: str  # StepType value
    description: str
    expected_day: int
    tolerance_hours: int
    duration_minutes: int
    criticality_score: float
    can_repeat_daily: bool = False
    depends_on_step_id: Optional[int] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate step creation data."""
        # Validate step type is valid category
        valid_types = {
            "INITIALIZATION", "MONITORING", "ADDITIONS", 
            "CAP_MANAGEMENT", "POST_FERMENTATION", "QUALITY_CHECK"
        }
        if self.step_type not in valid_types:
            raise ValueError(f"step_type must be one of {valid_types}. Got: {self.step_type}")
        
        validate_positive_int(self.step_order, "step_order")
        validate_positive_int(self.duration_minutes, "duration_minutes")
        validate_score_range(self.criticality_score, "criticality_score")
        
        if not self.description.strip():
            raise ValueError("description cannot be empty")


@dataclass
class StepUpdate:
    """DTO for updating a protocol step."""
    description: Optional[str] = None
    expected_day: Optional[int] = None
    tolerance_hours: Optional[int] = None
    duration_minutes: Optional[int] = None
    criticality_score: Optional[float] = None
    can_repeat_daily: Optional[bool] = None
    depends_on_step_id: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class StepResponse:
    """
    DTO for step API responses.
    
    Attributes:
        id: Step ID
        protocol_id: Parent protocol
        step_order: Position in protocol
        step_type: Category
        description: Specific details
        expected_day: Day when step occurs
        tolerance_hours: Valid window before/after
        duration_minutes: Step duration
        criticality_score: Importance (0-100)
        can_repeat_daily: Repeats each day
        depends_on_step_id: Dependency
        notes: Additional notes
        created_at: Creation timestamp
    """
    id: int
    protocol_id: int
    step_order: int
    step_type: str
    description: str
    expected_day: int
    tolerance_hours: int
    duration_minutes: int
    criticality_score: float
    can_repeat_daily: bool
    created_at: datetime
    depends_on_step_id: Optional[int] = None
    notes: Optional[str] = None


# ============================================================================
# Protocol Execution DTOs
# ============================================================================

@dataclass
class ExecutionStart:
    """
    DTO for starting a new protocol execution.
    
    Attributes:
        protocol_id: Protocol to execute
        fermentation_id: Associated fermentation
        start_date: When execution starts (defaults to now)
    """
    protocol_id: int
    fermentation_id: int
    start_date: Optional[datetime] = None


@dataclass
class ExecutionResponse:
    """
    DTO for execution API responses.
    
    Attributes:
        id: Execution ID
        protocol_id: Executed protocol
        fermentation_id: Associated fermentation
        status: Current status (NOT_STARTED, IN_PROGRESS, COMPLETED, PAUSED)
        start_date: When execution started
        compliance_score: 0-100 adherence score
        completed_steps: Count of completed steps
        skipped_critical_steps: Count of skipped critical steps
        created_at: Creation timestamp
        completed_at: When execution finished
        notes: Notes about execution
    """
    id: int
    protocol_id: int
    fermentation_id: int
    status: str  # ProtocolExecutionStatus value
    start_date: datetime
    compliance_score: float
    completed_steps: int
    skipped_critical_steps: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


# ============================================================================
# Step Completion DTOs
# ============================================================================

@dataclass
class CompletionCreate:
    """
    DTO for marking a step as completed.
    
    Attributes:
        execution_id: Parent execution
        step_id: Step being completed
        completed_at: When step was completed
        was_skipped: Whether step was skipped
        skip_reason: Why step was skipped (if applicable)
        skip_notes: Notes about skip
        is_on_schedule: Whether completed on expected day
        days_late: Days past expected date (if late)
        verified_by_user_id: User who verified completion
        notes: Completion notes
    """
    execution_id: int
    step_id: int
    was_skipped: bool = False
    completed_at: Optional[datetime] = None
    is_on_schedule: bool = True
    days_late: int = 0
    skip_reason: Optional[str] = None
    skip_notes: Optional[str] = None
    verified_by_user_id: Optional[int] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate completion data."""
        # Business rule: skip_reason required when was_skipped=true
        if self.was_skipped and not self.skip_reason:
            raise ValueError("skip_reason is required when was_skipped=True")
        
        # Business rule: completed_at required when not skipped
        if not self.was_skipped and not self.completed_at:
            raise ValueError("completed_at is required when was_skipped=False")
        
        # Validate skip reason if provided
        if self.skip_reason:
            valid_reasons = {
                "EQUIPMENT_MALFUNCTION", "WEATHER_CONDITIONS", 
                "QUALITY_ISSUE", "RESOURCE_UNAVAILABLE", "OTHER"
            }
            if self.skip_reason not in valid_reasons:
                raise ValueError(f"skip_reason must be one of {valid_reasons}. Got: {self.skip_reason}")


@dataclass
class CompletionResponse:
    """
    DTO for completion API responses.
    
    Attributes:
        id: Completion ID
        execution_id: Parent execution
        step_id: Completed step
        completed_at: When completed
        was_skipped: If step was skipped
        skip_reason: Skip reason
        skip_notes: Skip notes
        is_on_schedule: On schedule flag
        days_late: Days past expected date
        verified_by_user_id: Verifying user
        created_at: Record creation time
        notes: Completion notes
    """
    id: int
    execution_id: int
    step_id: int
    was_skipped: bool
    is_on_schedule: bool
    days_late: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    skip_reason: Optional[str] = None
    skip_notes: Optional[str] = None
    verified_by_user_id: Optional[int] = None
    notes: Optional[str] = None


# ============================================================================
# Batch/Query DTOs
# ============================================================================

@dataclass
class ProtocolListResponse:
    """Response for listing protocols with pagination."""
    protocols: List[ProtocolResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


@dataclass
class ExecutionListResponse:
    """Response for listing executions with pagination."""
    executions: List[ExecutionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


@dataclass
class ExecutionDetailResponse:
    """Detailed execution response with all steps and completions."""
    execution: ExecutionResponse
    steps: List[StepResponse]
    completions: List[CompletionResponse]
