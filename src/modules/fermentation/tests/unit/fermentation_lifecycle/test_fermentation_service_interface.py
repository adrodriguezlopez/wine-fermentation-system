"""
Test suite for IFermentationService interface contract.
These tests define the expected behavior that any implementation must follow.

Updated: 2025-10-11
Following Clean Architecture and ADR-003 Separation of Concerns.
"""
import pytest


def test_fermentation_service_interface_methods() -> None:
    """
    Test to ensure IFermentationService defines EXACTLY the required methods.
    If a new method is added, this test will fail,
    enforcing TDD and documentation updates.
    
    Expected methods (8):
    - create_fermentation: Create with validation
    - get_fermentation: Get by ID
    - get_fermentations_by_winery: List with filters
    - update_fermentation: Update fermentation data
    - update_status: Status transitions
    - complete_fermentation: Complete with validation
    - soft_delete: Soft delete
    - validate_creation_data: Pre-validation (dry-run)
    
    NOTE: add_sample is NOT here - it belongs to ISampleService (ADR-003)
    """
    try:
        from service_component.interfaces import IFermentationService
    except ImportError:
        pytest.fail("IFermentationService interface is not defined")

    required_methods = {
        "create_fermentation",
        "get_fermentation",
        "get_fermentations_by_winery",
        "update_fermentation",
        "update_status",
        "complete_fermentation",
        "soft_delete",
        "validate_creation_data",
    }

    # Get all abstract methods defined in the interface
    interface_methods = {
        name
        for name, value in IFermentationService.__dict__.items()
        if getattr(value, "__isabstractmethod__", False)
    }

    missing_methods = required_methods - interface_methods
    extra_methods = interface_methods - required_methods

    assert not missing_methods, f"Missing required methods: {missing_methods}"
    assert not extra_methods, f"Unexpected methods found: {extra_methods}"
