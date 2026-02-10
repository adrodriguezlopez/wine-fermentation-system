"""
Protocol Step Type Enumerations

Defines all possible fermentation step types that can appear in a protocol.
Based on Napa Valley winemaking best practices.
"""

from enum import Enum


class StepType(str, Enum):
    """All possible fermentation protocol step types"""
    
    # Initialization
    YEAST_INOCULATION = "YEAST_INOCULATION"
    COLD_SOAK = "COLD_SOAK"
    
    # Monitoring
    TEMPERATURE_CHECK = "TEMPERATURE_CHECK"
    H2S_CHECK = "H2S_CHECK"
    BRIX_READING = "BRIX_READING"
    VISUAL_INSPECTION = "VISUAL_INSPECTION"
    
    # Additions
    DAP_ADDITION = "DAP_ADDITION"
    NUTRIENT_ADDITION = "NUTRIENT_ADDITION"
    SO2_ADDITION = "SO2_ADDITION"
    MLF_INOCULATION = "MLF_INOCULATION"
    
    # Cap Management
    PUNCH_DOWN = "PUNCH_DOWN"
    PUMP_OVER = "PUMP_OVER"
    
    # Post-Fermentation
    PRESSING = "PRESSING"
    EXTENDED_MACERATION = "EXTENDED_MACERATION"
    SETTLING = "SETTLING"
    RACKING = "RACKING"
    FILTERING = "FILTERING"
    CLARIFICATION = "CLARIFICATION"
    
    # Tasting/Quality
    CATA_TASTING = "CATA_TASTING"


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
