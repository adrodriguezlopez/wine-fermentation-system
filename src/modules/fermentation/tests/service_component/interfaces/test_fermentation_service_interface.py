"""
Test suite for IFermentationService interface contract.
These tests define the expected behavior that any implementation must follow.
"""
import pytest
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

def test_fermentation_service_interface_methods():
    """
    Test to ensure IFermentationService defines EXACTLY the required methods.
    If a new method is added, this test will fail, enforcing TDD and documentation updates.
    """
    try:
        from service_component.interfaces.fermentation_service_interface import IFermentationService
    except ImportError:
        pytest.fail("IFermentationService interface is not defined")

    required_methods = {
        'create_fermentation',
        'get_fermentation',
        'add_sample',
    }

    # Get all abstract methods defined in the interface
    interface_methods = {
        name for name, value in IFermentationService.__dict__.items()
        if getattr(value, "__isabstractmethod__", False)
    }

    missing_methods = required_methods - interface_methods
    extra_methods = interface_methods - required_methods

    assert not missing_methods, f"Missing required methods: {missing_methods}"
    assert not extra_methods, f"Unexpected methods found: {extra_methods}"

def test_fermentation_service_interface_methods():
    """
    Test to ensure IFermentationService defines EXACTLY the required methods.
    If a new method is added, this test will fail, enforcing TDD and documentation updates.
    """
    try:
        from service_component.interfaces.fermentation_service_interface import IFermentationService
    except ImportError:
        pytest.fail("IFermentationService interface is not defined")

    required_methods = {
        'create_fermentation',
        'get_fermentation',
        'add_sample',
    }

    # Get all abstract methods defined in the interface
    interface_methods = {
        name for name, value in IFermentationService.__dict__.items()
        if getattr(value, "__isabstractmethod__", False)
    }

    missing_methods = required_methods - interface_methods
    extra_methods = interface_methods - required_methods

    assert not missing_methods, f"Missing required methods: {missing_methods}"
    assert not extra_methods, f"Unexpected methods found: {extra_methods}"


