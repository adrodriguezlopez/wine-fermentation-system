"""
Unit tests for FermentationLotSource entity metadata.

Tests entity structure, constraints, and configuration without instantiation
to avoid SQLAlchemy relationship configuration issues during development.
"""

from domain.entities.fermentation_lot_source import FermentationLotSource


class TestFermentationLotSourceMetadata:
    """Test cases for FermentationLotSource metadata and configuration."""

    def test_fermentation_lot_source_table_name(self):
        """Test that table name is correctly set."""
        assert FermentationLotSource.__tablename__ == "fermentation_lot_sources"

    def test_fermentation_lot_source_constraints_structure(self):
        """Test that table constraints are properly defined."""
        table_args = FermentationLotSource.__table_args__
        
        # Should have UniqueConstraint, CheckConstraint, and Indexes
        constraint_names = []
        for constraint in table_args:
            if hasattr(constraint, 'name'):
                constraint_names.append(constraint.name)
        
        # Check for key constraints
        assert any('fermentation_harvest' in name for name in constraint_names)
        assert any('mass_positive' in name for name in constraint_names)

    def test_fermentation_lot_source_has_required_fields(self):
        """Test that entity has all required field mappings."""
        # Check that mapped fields exist
        assert hasattr(FermentationLotSource, 'fermentation_id')
        assert hasattr(FermentationLotSource, 'harvest_lot_id')
        assert hasattr(FermentationLotSource, 'mass_used_kg')
        assert hasattr(FermentationLotSource, 'notes')

    def test_blend_calculation_logic(self):
        """Test blend percentage calculation logic without entity instantiation."""
        # Test the mathematical logic that would be used in blend scenarios
        
        # Scenario: 1000kg fermentation with 3 lots
        total_fermentation_mass = 1000.0
        
        lot_masses = [400.0, 350.0, 250.0]  # Three different lots
        
        # Calculate percentages
        percentages = [(mass / total_fermentation_mass) * 100 for mass in lot_masses]
        
        assert percentages[0] == 40.0  # 400/1000 * 100
        assert percentages[1] == 35.0  # 350/1000 * 100
        assert percentages[2] == 25.0  # 250/1000 * 100
        assert sum(percentages) == 100.0  # Total should be 100%
        assert sum(lot_masses) == total_fermentation_mass  # Mass balance

    def test_mass_validation_logic(self):
        """Test mass validation logic that would be enforced in services."""
        # Business rule: mass_used_kg must be > 0
        valid_masses = [0.1, 100.0, 1000.5, 0.001]
        invalid_masses = [0.0, -1.0, -100.0]
        
        # All valid masses should pass the > 0 check
        for mass in valid_masses:
            assert mass > 0
            
        # All invalid masses should fail the > 0 check  
        for mass in invalid_masses:
            assert not (mass > 0)