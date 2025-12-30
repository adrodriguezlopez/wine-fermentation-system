"""
Root conftest for fermentation module tests.

This file configures the Python path to allow imports from the workspace root.
Required for Poetry-managed independent module environments (ADR-028).
"""

import sys
from pathlib import Path

# Add workspace root to Python path for cross-module imports
# fermentation/tests/conftest.py -> fermentation/tests -> fermentation -> modules -> src -> workspace_root
workspace_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))
