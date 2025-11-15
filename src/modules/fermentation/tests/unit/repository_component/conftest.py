"""
Pytest configuration for repository unit tests.

This conftest provides fixtures to handle SQLAlchemy MetaData cleanup
between tests to avoid "Table already defined" errors.
"""

import pytest


@pytest.fixture
def reset_sqlalchemy_metadata():
    """
    Clean up SQLAlchemy MetaData between tests.
    
    This prevents "Table 'X' is already defined for this MetaData instance" errors
    that occur when running multiple tests that import SQLAlchemy entities.
    
    NOTE: autouse=False by default. Only integration tests should NOT use this,
    as they need a stable registry throughout the session.
    """
    # Before test runs
    yield
    
    # After test completes - clean up any imported modules
    # This forces reimport on next test, resetting MetaData
    import sys
    modules_to_remove = [
        key for key in sys.modules.keys()
        if key.startswith('src.modules.fermentation.src.domain.entities')
    ]
    for module in modules_to_remove:
        del sys.modules[module]
