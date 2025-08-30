import pytest
import inspect
from service_component.interfaces import IValidationService


def test_validation_service_interface_methods():
    """Test that IValidationService has all expected methods."""
    
    # Expected methods in our current interface
    expected_methods = {
        # High-level workflow methods (async)
        'validate_samples',
        'validate_chronology', 
        
        # Granular validation methods (sync)
        'validate_sample_value',
        'validate_sugar_trend',
        
        # Factory methods
        'success',
        'failure'
    }
    
    # Get actual methods from interface
    actual_methods = set()
    for name, method in inspect.getmembers(IValidationService, predicate=inspect.isfunction):
        if not name.startswith('_'):  # Skip private methods
            actual_methods.add(name)
    
    # Check that all expected methods are present
    missing_methods = expected_methods - actual_methods
    extra_methods = actual_methods - expected_methods
    
    assert not missing_methods, f"Missing required methods: {missing_methods}"
    assert not extra_methods, f"Unexpected methods found: {extra_methods}"


def test_validation_service_interface_is_abstract():
    """Test that IValidationService cannot be instantiated directly."""
    
    with pytest.raises(TypeError):
        IValidationService()


def test_validation_service_interface_methods_are_abstract():
    """Test that all methods in IValidationService are abstract methods."""
    
    # Get all non-private methods
    methods = [name for name, _ in inspect.getmembers(IValidationService, predicate=inspect.isfunction) 
               if not name.startswith('_')]
    
    # Check that each method is marked as abstract
    for method_name in methods:
        method = getattr(IValidationService, method_name)
        assert getattr(method, '__isabstractmethod__', False), f"Method {method_name} should be abstract"