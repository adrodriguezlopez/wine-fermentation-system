"""
Test configuration for shared infra tests.

Adds workspace root to sys.path to enable imports.
"""
import sys
from pathlib import Path

# Add workspace root to Python path
workspace_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))

# Add src/shared to path
shared_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(shared_root))
