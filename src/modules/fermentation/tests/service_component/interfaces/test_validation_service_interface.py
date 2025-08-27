"""
Test suite for IValidationService interface contract.
These tests define the expected behavior that any implementation must follow.
"""
import pytest
from datetime import datetime
from typing import List, Dict, Any

def test_validation_service_interface_methods():
    """
    Test to ensure IValidationService defines EXACTLY the required methods.
    If a new method is added, this test will fail, enforcing TDD and documentation updates.
    """
    try:
        from service_component.interfaces.validation_service_interface import IValidationService
    except ImportError:
        pytest.fail("IValidationService interface is not defined")

    required_methods = {
        'validate_measurements',
        'validate_chronology',
        'validate_trend',
        'check_anomalies'
    }

    # Get all abstract methods defined in the interface
    interface_methods = {
        name for name, value in IValidationService.__dict__.items()
        if getattr(value, "__isabstractmethod__", False)
    }

    missing_methods = required_methods - interface_methods
    extra_methods = interface_methods - required_methods

    assert not missing_methods, f"Missing required methods: {missing_methods}"
    assert not extra_methods, f"Unexpected methods found: {extra_methods}"
