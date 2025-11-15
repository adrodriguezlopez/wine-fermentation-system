"""
Unit tests for ISampleService interface - sample management functionality.
Tests define the expected behavior for sample collection and retrieval operations.

Updated: 2025-10-11
Following Clean Architecture and ADR-003 Separation of Concerns.
"""
import pytest
import sys
from pathlib import Path

# Add src to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))


def test_sample_service_interface_methods() -> None:
    """
    Test to ensure ISampleService defines EXACTLY the required methods.
    If a new method is added, this test will fail,
    enforcing TDD and documentation updates.
    
    Expected methods (7):
    - add_sample: Add sample with full validation
    - get_sample: Get specific sample by ID
    - get_samples_by_fermentation: List all samples for fermentation
    - get_latest_sample: Get most recent sample (optionally by type)
    - get_samples_in_timerange: Get samples in date range
    - validate_sample_data: Pre-validation (dry-run)
    - delete_sample: Soft delete sample
    
    NOTE: Following ADR-003, sample operations are separate from fermentation operations.
    """
    try:
        from service_component.interfaces import ISampleService
    except ImportError:
        pytest.fail("ISampleService interface is not defined")

    required_methods = {
        "add_sample",
        "get_sample",
        "get_samples_by_fermentation",
        "get_latest_sample",
        "get_samples_in_timerange",
        "validate_sample_data",
        "delete_sample",
    }

    # Get all abstract methods defined in the interface
    interface_methods = {
        name
        for name, value in ISampleService.__dict__.items()
        if getattr(value, "__isabstractmethod__", False)
    }

    missing_methods = required_methods - interface_methods
    extra_methods = interface_methods - required_methods

    assert not missing_methods, f"Missing required methods: {missing_methods}"
    assert not extra_methods, f"Unexpected methods found: {extra_methods}"
