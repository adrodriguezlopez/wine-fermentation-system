"""
Wine Fermentation Management Module
---------------------------------
Core module for managing fermentation processes in the wine monitoring system.

This module handles path configuration to ensure proper imports
from shared infrastructure components.
"""

import sys
from pathlib import Path

# Configure project root path once for the entire module
_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

__version__ = "0.1.0"
