"""
Root-level conftest for project-wide tests (tests/ directory).

Adds the workspace root to sys.path so tests can use absolute imports like:
    from src.modules.fermentation.src... import ...
    from src.shared... import ...
"""
import sys
from pathlib import Path

# workspace_root = .../wine-fermentation-system
workspace_root = Path(__file__).parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))
