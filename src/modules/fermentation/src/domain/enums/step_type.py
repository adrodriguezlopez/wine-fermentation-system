"""
Protocol Step Type Enumerations

Defines fermentation step categories for protocols.

DESIGN NOTE (Feb 10, 2026):
- StepType enum contains CATEGORIES of work, not specific steps
- Specific step details (yeast type, nutrient brand, etc.) go in ProtocolStep.description
- This allows flexibility: add new steps without modifying the enum
- Example: Both "Red Star Premier" and "EC-1118" yeasts use INITIALIZATION category
"""

from enum import Enum


class StepType(str, Enum):
    """Categories of fermentation protocol work"""
    
    # Pre-fermentation setup (cold soak, inoculation, etc.)
    INITIALIZATION = "INITIALIZATION"
    
    # Observation & measurement (temperature, brix, H2S checks, visual inspection)
    MONITORING = "MONITORING"
    
    # Nutrient & SO2 additions (DAP, MLF, other additions)
    ADDITIONS = "ADDITIONS"
    
    # Cap management during active fermentation (punch down, pump over)
    CAP_MANAGEMENT = "CAP_MANAGEMENT"
    
    # Post-fermentation processing (pressing, racking, filtering, settling, clarification, extended maceration)
    POST_FERMENTATION = "POST_FERMENTATION"
    
    # Tasting & quality analysis
    QUALITY_CHECK = "QUALITY_CHECK"


class ProtocolExecutionStatus(str, Enum):
    """Status of a protocol execution for a specific fermentation"""
    
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class SkipReason(str, Enum):
    """Reasons why a protocol step was skipped"""
    
    EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE"
    CONDITION_NOT_MET = "CONDITION_NOT_MET"
    FERMENTATION_ENDED = "FERMENTATION_ENDED"
    FERMENTATION_FAILED = "FERMENTATION_FAILED"
    WINEMAKER_DECISION = "WINEMAKER_DECISION"
    REPLACED_BY_ALTERNATIVE = "REPLACED_BY_ALTERNATIVE"
    OTHER = "OTHER"
