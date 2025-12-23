"""
Test configuration for shared module.

Adds workspace root to sys.path to enable imports like:
- from src.shared.testing import X
- from shared.testing import Y (when running from shared context)
"""
import sys
from pathlib import Path

# Add workspace root to Python path
# This file is at: src/shared/testing/tests/conftest.py
# Need to go up to: workspace root
workspace_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))

# Also add src/shared to path for relative imports within shared
shared_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(shared_root))
