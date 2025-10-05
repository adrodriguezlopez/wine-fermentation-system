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
        from domain.repositories import IFermentationRepository
    except ImportError:
        pytest.fail("IFermentationRepository interface is not defined")

    required_methods = {
        "create",
        "get_by_id",
        "update_status",
        "get_by_status",
        "get_by_winery",
    }
    
    # NOTE: Sample operations removed (ADR-003: Separation of Concerns)
    # Sample methods now live exclusively in ISampleRepository:
    # - add_sample() → ISampleRepository.upsert_sample()
    # - get_latest_sample() → ISampleRepository.get_latest_sample()
    # This follows Single Responsibility Principle - one repository per aggregate
    
    # NOTE: Sample query methods (get_samples_by_fermentation_id, get_samples_in_timerange)
    # are defined in ISampleRepository, not IFermentationRepository
    # This follows single responsibility principle

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
