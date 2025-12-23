"""
Test configuration for winery module.

Adds workspace root to sys.path to enable imports like:
- from src.shared.wine_fermentator_logging import get_logger
- from src.modules.winery.src.domain.entities.winery import Winery
"""
import sys
from pathlib import Path

# Add workspace root to Python path
# tests/conftest.py -> tests -> winery -> modules -> src -> wine-fermentation-system
workspace_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))
