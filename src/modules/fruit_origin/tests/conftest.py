"""
Pytest configuration for fruit_origin module tests.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Add workspace root src to path for cross-module imports
workspace_src = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(workspace_src))
