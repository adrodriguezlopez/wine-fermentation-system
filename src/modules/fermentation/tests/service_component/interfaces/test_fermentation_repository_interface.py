"""
Test suite for IFermentationRepository interface contract.
These tests define the expected behavior that any implementation must follow.
"""
import pytest


def test_fermentation_repository_interface_methods() -> None:
    """
    Test to ensure IFermentationRepository defines EXACTLY the required methods
    If a new method is added, this test will fail,
    enforcing TDD and documentation updates.
    """
    try:
        from service_component.interfaces import IFermentationRepository
    except ImportError:
        pytest.fail("IFermentationRepository interface is not defined")

    required_methods = {
        "create",
        "get_by_id",
        "update_status",
        "add_sample",
        "get_samples",
        "get_samples_in_range",
        "get_latest_sample",
        "get_by_status",
        "get_by_winery",
    }

    # Get all abstract methods defined in the interface
    interface_methods = {
        name
        for name, value in IFermentationRepository.__dict__.items()
        if getattr(value, "__isabstractmethod__", False)
    }

    missing_methods = required_methods - interface_methods
    extra_methods = interface_methods - required_methods

    assert not missing_methods, f"Missing required methods: {missing_methods}"
    assert not extra_methods, f"Unexpected methods found: {extra_methods}"
