"""
Unit tests for DataSource enum (ADR-029)

TDD RED phase: Tests written before implementation
"""
import pytest
from enum import Enum


class TestDataSourceEnum:
    """Test suite for DataSource enum - ADR-029"""
    
    def test_data_source_enum_exists(self):
        """
        TDD RED: DataSource enum should exist in domain.
        
        Given: Fermentation domain module
        When: Importing DataSource enum
        Then: Import should succeed
        """
        from src.modules.fermentation.src.domain.enums import DataSource
        
        assert DataSource is not None
        assert issubclass(DataSource, Enum)
    
    def test_data_source_has_system_value(self):
        """
        TDD RED: DataSource should have SYSTEM value.
        
        Given: DataSource enum
        When: Accessing SYSTEM member
        Then: Value should be 'system'
        """
        from src.modules.fermentation.src.domain.enums import DataSource
        
        assert hasattr(DataSource, 'SYSTEM')
        assert DataSource.SYSTEM.value == 'system'
    
    def test_data_source_has_imported_value(self):
        """
        TDD RED: DataSource should have IMPORTED value.
        
        Given: DataSource enum
        When: Accessing IMPORTED member
        Then: Value should be 'imported'
        """
        from src.modules.fermentation.src.domain.enums import DataSource
        
        assert hasattr(DataSource, 'IMPORTED')
        assert DataSource.IMPORTED.value == 'imported'
    
    def test_data_source_has_migrated_value(self):
        """
        TDD RED: DataSource should have MIGRATED value.
        
        Given: DataSource enum
        When: Accessing MIGRATED member
        Then: Value should be 'migrated'
        """
        from src.modules.fermentation.src.domain.enums import DataSource
        
        assert hasattr(DataSource, 'MIGRATED')
        assert DataSource.MIGRATED.value == 'migrated'
    
    def test_data_source_is_string_enum(self):
        """
        TDD RED: DataSource should be a string enum for ORM compatibility.
        
        Given: DataSource enum
        When: Checking inheritance
        Then: Should inherit from str
        """
        from src.modules.fermentation.src.domain.enums import DataSource
        
        # Check that values are strings
        assert isinstance(DataSource.SYSTEM.value, str)
        assert isinstance(DataSource.IMPORTED.value, str)
        assert isinstance(DataSource.MIGRATED.value, str)
    
    def test_data_source_only_has_three_values(self):
        """
        TDD RED: DataSource should only have exactly 3 values.
        
        Given: DataSource enum
        When: Counting members
        Then: Should have exactly 3 members
        """
        from src.modules.fermentation.src.domain.enums import DataSource
        
        assert len(DataSource) == 3
        assert set(DataSource) == {
            DataSource.SYSTEM,
            DataSource.IMPORTED,
            DataSource.MIGRATED
        }
