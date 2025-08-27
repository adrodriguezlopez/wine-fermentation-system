"""
Test suite for ISampleService interface contract.
These tests define the expected behavior that any implementation must follow.
"""
import pytest


def test_sample_service_interface_methods() -> None:
    """
    Test to ensure ISampleService defines EXACTLY the required methods.
    If a new method is added, this test will fail,
    enforcing TDD and documentation updates.
    """
    try:
        from service_component.interfaces import ISampleService
    except ImportError:
        pytest.fail("ISampleService interface is not defined")

    required_methods = {
        "validate_sample",
        "get_sample",
        "get_samples_in_range",
        "get_latest_sample",
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
