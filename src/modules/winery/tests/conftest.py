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

# Pre-import SQLAlchemy entities to ensure mapper registry is populated
# This prevents "failed to locate a name" errors when SQLAlchemy configures relationships
# Import order matters: base entities first, then entities with relationships
try:
    # Import entities that are referenced in relationships but might not be loaded yet
    from src.shared.auth.domain.entities.user import User
    from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource
    from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
    from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
except ImportError:
    # If imports fail, tests will handle it gracefully
    pass
