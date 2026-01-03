"""
Unit tests for data_source and imported_at fields in BaseSample entity (ADR-029)

TDD RED phase: Tests written before implementation
"""
import pytest
from datetime import datetime
from src.modules.fermentation.src.domain.enums import DataSource


class TestBaseSampleDataSourceField:
    """Test suite for BaseSample.data_source field - ADR-029"""
    
    def test_base_sample_has_data_source_field(self):
        """
        TDD RED: BaseSample should have data_source field.
        
        Given: BaseSample entity class
        When: Inspecting class attributes
        Then: Should have data_source field
        """
        from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
        
        # Check that the class has the attribute defined
        assert hasattr(BaseSample, 'data_source')
    
    def test_base_sample_data_source_defaults_to_system(self):
        """
        TDD RED: BaseSample.data_source should default to SYSTEM.
        
        Given: BaseSample entity mapped column definition
        When: Checking column default value
        Then: Should default to 'system'
        """
        from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
        
        # Check the mapped column default
        column = BaseSample.__table__.columns['data_source']
        assert column.default.arg == DataSource.SYSTEM.value
    
    def test_base_sample_data_source_can_be_set_to_imported(self):
        """
        TDD RED: BaseSample.data_source can be set to IMPORTED.
        
        Given: BaseSample entity class
        When: Checking data_source column accepts IMPORTED value
        Then: Column should accept string values up to 20 chars
        """
        from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
        
        # Verify column can store IMPORTED value
        column = BaseSample.__table__.columns['data_source']
        assert column.type.length >= len(DataSource.IMPORTED.value)
    
    def test_base_sample_data_source_can_be_set_to_migrated(self):
        """
        TDD RED: BaseSample.data_source can be set to MIGRATED.
        
        Given: BaseSample entity class
        When: Checking data_source column accepts MIGRATED value
        Then: Column should accept string values up to 20 chars
        """
        from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
        
        # Verify column can store MIGRATED value
        column = BaseSample.__table__.columns['data_source']
        assert column.type.length >= len(DataSource.MIGRATED.value)


class TestBaseSampleImportedAtField:
    """Test suite for BaseSample.imported_at field - ADR-029"""
    
    def test_base_sample_has_imported_at_field(self):
        """
        TDD RED: BaseSample should have imported_at field.
        
        Given: BaseSample entity class
        When: Inspecting class attributes
        Then: Should have imported_at field
        """
        from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
        
        assert hasattr(BaseSample, 'imported_at')
    
    def test_base_sample_imported_at_defaults_to_none(self):
        """
        TDD RED: BaseSample.imported_at should default to None.
        
        Given: BaseSample entity mapped column definition
        When: Checking column nullable and default
        Then: Should be nullable with no default
        """
        from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
        
        # Check the mapped column is nullable
        column = BaseSample.__table__.columns['imported_at']
        assert column.nullable == True
        assert column.default is None
    
    def test_base_sample_imported_at_can_be_set(self):
        """
        TDD RED: BaseSample.imported_at can be set to a datetime.
        
        Given: BaseSample entity class
        When: Checking imported_at column type
        Then: Should be DateTime type
        """
        from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
        from sqlalchemy import DateTime
        
        # Check the column type
        column = BaseSample.__table__.columns['imported_at']
        assert isinstance(column.type, DateTime)
    
    def test_base_sample_data_source_column_is_indexed(self):
        """
        TDD RED: BaseSample.data_source should be indexed (ADR-029).
        
        Given: BaseSample entity table definition
        When: Checking data_source column
        Then: Should have index=True
        """
        from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
        
        # Check the column has index
        column = BaseSample.__table__.columns['data_source']
        assert column.index == True
