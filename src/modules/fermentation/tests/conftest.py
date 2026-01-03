"""
Root conftest for fermentation module tests.

This file configures the Python path to allow imports from the workspace root.
Required for Poetry-managed independent module environments (ADR-028).
"""

import sys
from pathlib import Path
import pytest

# Add workspace root to Python path for cross-module imports
# fermentation/tests/conftest.py -> fermentation/tests -> fermentation -> modules -> src -> workspace_root
workspace_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))


@pytest.fixture(scope="function")
def event_loop():
    """
    Create a new event loop for each test function.
    
    This prevents "Event loop is closed" errors when running many tests together.
    Using function scope ensures each test gets a fresh event loop.
    """
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
