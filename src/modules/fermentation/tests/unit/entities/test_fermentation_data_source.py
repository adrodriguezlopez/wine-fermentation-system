"""
Unit tests for data_source and imported_at fields in Fermentation entity (ADR-029)

TDD RED phase: Tests written before implementation
"""
import pytest
from datetime import datetime
from src.modules.fermentation.src.domain.enums import DataSource


class TestFermentationDataSourceField:
    """Test suite for Fermentation.data_source field - ADR-029"""
    
    def test_fermentation_has_data_source_field(self):
        """
        TDD RED: Fermentation should have data_source field.
        
        Given: Fermentation entity class
        When: Inspecting class attributes
        Then: Should have data_source field
        """
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
        
        # Check that the class has the attribute defined
        assert hasattr(Fermentation, 'data_source')
    
    def test_fermentation_data_source_defaults_to_system(self):
        """
        TDD RED: Fermentation.data_source should default to SYSTEM.
        
        Given: Fermentation entity mapped column definition
        When: Checking column default value
        Then: Should default to 'system'
        """
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
        
        # Check the mapped column default
        column = Fermentation.__table__.columns['data_source']
        assert column.default.arg == DataSource.SYSTEM.value
    
    def test_fermentation_data_source_can_be_set_to_imported(self):
        """
        TDD RED: Fermentation.data_source can be set to IMPORTED.
        
        Given: Fermentation entity class
        When: Checking data_source column accepts IMPORTED value
        Then: Column should accept string values up to 20 chars
        """
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
        
        # Verify column can store IMPORTED value
        column = Fermentation.__table__.columns['data_source']
        assert column.type.length >= len(DataSource.IMPORTED.value)
    
    def test_fermentation_data_source_can_be_set_to_migrated(self):
        """
        TDD RED: Fermentation.data_source can be set to MIGRATED.
        
        Given: Fermentation entity class
        When: Checking data_source column accepts MIGRATED value
        Then: Column should accept string values up to 20 chars
        """
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
        
        # Verify column can store MIGRATED value
        column = Fermentation.__table__.columns['data_source']
        assert column.type.length >= len(DataSource.MIGRATED.value)


class TestFermentationImportedAtField:
    """Test suite for Fermentation.imported_at field - ADR-029"""
    
    def test_fermentation_has_imported_at_field(self):
        """
        TDD RED: Fermentation should have imported_at field.
        
        Given: Fermentation entity class
        When: Inspecting class attributes
        Then: Should have imported_at field
        """
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
        
        assert hasattr(Fermentation, 'imported_at')
    
    def test_fermentation_imported_at_defaults_to_none(self):
        """
        TDD RED: Fermentation.imported_at should default to None.
        
        Given: Fermentation entity mapped column definition
        When: Checking column nullable and default
        Then: Should be nullable with no default
        """
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
        
        # Check the mapped column is nullable
        column = Fermentation.__table__.columns['imported_at']
        assert column.nullable == True
        assert column.default is None
    
    def test_fermentation_imported_at_can_be_set(self):
        """
        TDD RED: Fermentation.imported_at can be set to a datetime.
        
        Given: Fermentation entity class
        When: Checking imported_at column type
        Then: Should be DateTime type
        """
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
        from sqlalchemy import DateTime
        
        # Check the column type
        column = Fermentation.__table__.columns['imported_at']
        assert isinstance(column.type, DateTime)
    
    def test_fermentation_data_source_column_is_indexed(self):
        """
        TDD RED: Fermentation.data_source should be indexed (ADR-029).
        
        Given: Fermentation entity table definition
        When: Checking data_source column
        Then: Should have index=True
        """
        from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
        
        # Check the column has index
        column = Fermentation.__table__.columns['data_source']
        assert column.index == True
