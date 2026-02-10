"""
Tests for Protocol Enums

Tests enum values without any database or entity dependencies.
"""

import pytest
from src.modules.fermentation.src.domain.enums.step_type import (
    StepType, 
    ProtocolExecutionStatus, 
    SkipReason
)


class TestStepTypeEnum:
    """Test StepType enum values."""
    
    def test_step_type_has_yeast_inoculation(self):
        """Verify YEAST_INOCULATION is in StepType."""
        assert hasattr(StepType, 'YEAST_INOCULATION')
        assert StepType.YEAST_INOCULATION.value == 'YEAST_INOCULATION'
    
    def test_step_type_has_all_expected_values(self):
        """Verify StepType enum has all expected step types."""
        expected_types = {
            'YEAST_INOCULATION',
            'COLD_SOAK',
            'TEMPERATURE_CHECK',
            'H2S_CHECK',
            'BRIX_READING',
            'VISUAL_INSPECTION',
            'DAP_ADDITION',
            'NUTRIENT_ADDITION',
            'SO2_ADDITION',
            'MLF_INOCULATION',
            'PUNCH_DOWN',
            'PUMP_OVER',
            'PRESSING',
            'EXTENDED_MACERATION',
            'SETTLING',
            'RACKING',
            'FILTERING',
            'CLARIFICATION',
            'CATA_TASTING'
        }
        
        enum_values = {e.name for e in StepType}
        assert enum_values == expected_types, f"Missing or extra types: {enum_values.symmetric_difference(expected_types)}"
    
    def test_step_type_count(self):
        """Verify StepType has exactly 19 values."""
        assert len(list(StepType)) == 19


class TestProtocolExecutionStatusEnum:
    """Test ProtocolExecutionStatus enum values."""
    
    def test_execution_status_has_not_started(self):
        """Verify NOT_STARTED is in ProtocolExecutionStatus."""
        assert hasattr(ProtocolExecutionStatus, 'NOT_STARTED')
    
    def test_execution_status_has_active(self):
        """Verify ACTIVE is in ProtocolExecutionStatus."""
        assert hasattr(ProtocolExecutionStatus, 'ACTIVE')
    
    def test_execution_status_has_paused(self):
        """Verify PAUSED is in ProtocolExecutionStatus."""
        assert hasattr(ProtocolExecutionStatus, 'PAUSED')
    
    def test_execution_status_has_completed(self):
        """Verify COMPLETED is in ProtocolExecutionStatus."""
        assert hasattr(ProtocolExecutionStatus, 'COMPLETED')
    
    def test_execution_status_has_abandoned(self):
        """Verify ABANDONED is in ProtocolExecutionStatus."""
        assert hasattr(ProtocolExecutionStatus, 'ABANDONED')
    
    def test_execution_status_has_all_expected_values(self):
        """Verify ProtocolExecutionStatus enum has all expected statuses."""
        expected_statuses = {
            'NOT_STARTED',
            'ACTIVE',
            'PAUSED',
            'COMPLETED',
            'ABANDONED'
        }
        
        enum_values = {e.name for e in ProtocolExecutionStatus}
        assert enum_values == expected_statuses
    
    def test_execution_status_count(self):
        """Verify ProtocolExecutionStatus has exactly 5 values."""
        assert len(list(ProtocolExecutionStatus)) == 5


class TestSkipReasonEnum:
    """Test SkipReason enum values."""
    
    def test_skip_reason_has_equipment_failure(self):
        """Verify EQUIPMENT_FAILURE is in SkipReason."""
        assert hasattr(SkipReason, 'EQUIPMENT_FAILURE')
    
    def test_skip_reason_has_condition_not_met(self):
        """Verify CONDITION_NOT_MET is in SkipReason."""
        assert hasattr(SkipReason, 'CONDITION_NOT_MET')
    
    def test_skip_reason_has_all_expected_values(self):
        """Verify SkipReason enum has all expected skip reasons."""
        expected_reasons = {
            'EQUIPMENT_FAILURE',
            'CONDITION_NOT_MET',
            'FERMENTATION_ENDED',
            'FERMENTATION_FAILED',
            'WINEMAKER_DECISION',
            'REPLACED_BY_ALTERNATIVE',
            'OTHER'
        }
        
        enum_values = {e.name for e in SkipReason}
        assert enum_values == expected_reasons
    
    def test_skip_reason_count(self):
        """Verify SkipReason has exactly 7 values."""
        assert len(list(SkipReason)) == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
