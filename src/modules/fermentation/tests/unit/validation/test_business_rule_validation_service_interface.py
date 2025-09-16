import pytest
import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from service_component.interfaces import IBusinessRuleValidationService

def test_business_rule_validation_service_interface_methods():
    """Test that IBusinessRuleValidationService has all expected methods."""
    
    # Expected methods in our current interface
    expected_methods = {
        'validate_sugar_trend',
        'validate_temperature_range'
    }
    
    # Get actual methods from interface
    actual_methods = set()
    for name, method in inspect.getmembers(IBusinessRuleValidationService, predicate=inspect.isfunction):
        if not name.startswith('_'):  # Skip private methods
            actual_methods.add(name)
    
    # Check that all expected methods are present
    missing_methods = expected_methods - actual_methods
    extra_methods = actual_methods - expected_methods
    
    assert not missing_methods, f"Missing required methods: {missing_methods}"
    assert not extra_methods, f"Unexpected methods found: {extra_methods}"