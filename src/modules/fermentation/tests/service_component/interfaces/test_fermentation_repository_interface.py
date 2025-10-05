"""
Unit tests for IFermentationRepository interface contract.
Tests that the interface defines proper contracts for TDD implementation.
"""

import pytest
import inspect
import sys
from pathlib import Path

# Configure path to access src module
_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Load interface module directly to avoid domain entity imports that use SQLAlchemy
interface_file = Path("C:/dev/wine-fermentation-system/src/modules/fermentation/src/domain/repositories/fermentation_repository_interface.py")

import importlib.util
spec = importlib.util.spec_from_file_location(
    "fermentation_repository_interface",
    str(interface_file)  # Convert to string for importlib
)
interface_module = importlib.util.module_from_spec(spec)
sys.modules["fermentation_repository_interface"] = interface_module
spec.loader.exec_module(interface_module)

# Import from loaded module
IFermentationRepository = interface_module.IFermentationRepository


class TestFermentationRepositoryInterface:
    """Test that IFermentationRepository defines proper contracts."""

    def test_interface_defines_all_required_methods(self):
        """Test that IFermentationRepository defines all expected abstract methods."""
        expected_methods = [
            'create',
            'get_by_id',
            'update_status',
            'add_sample',
            'get_samples',
            'get_samples_in_range',
            'get_latest_sample',
            'get_by_status',
            'get_by_winery',
            'get_fermentation_temperature_range',
        ]

        for method_name in expected_methods:
            assert hasattr(IFermentationRepository, method_name), f"Missing method: {method_name}"
            assert callable(getattr(IFermentationRepository, method_name)), f"Method not callable: {method_name}"

    def test_interface_is_abstract(self):
        """Test that IFermentationRepository cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            IFermentationRepository()

    def test_all_methods_are_async(self):
        """Test that all interface methods are async."""
        for name, method in inspect.getmembers(IFermentationRepository, predicate=inspect.isfunction):
            if not name.startswith('_'):  # Skip private methods
                assert inspect.iscoroutinefunction(method), f"Method {name} should be async"

    def test_interface_has_proper_inheritance(self):
        """Test that IFermentationRepository inherits from ABC."""
        from abc import ABC
        assert issubclass(IFermentationRepository, ABC), "Should inherit from ABC"

    def test_methods_have_abstract_decorator(self):
        """Test that all methods are properly marked as abstract."""
        for name, method in inspect.getmembers(IFermentationRepository, predicate=inspect.isfunction):
            if not name.startswith('_'):
                # Check if method has __isabstractmethod__ attribute
                assert hasattr(method, '__isabstractmethod__'), f"Method {name} should be abstract"
                assert method.__isabstractmethod__, f"Method {name} should be abstract"