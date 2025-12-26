"""Repository errors for fruit_origin module.

ADR-026: This module now uses the shared error hierarchy for consistency.
Legacy error names are maintained as aliases for backward compatibility.
"""

# Import from shared ADR-026 error hierarchy
from shared.domain.errors import (
    FruitOriginError,
    VineyardNotFound,
    InvalidHarvestDate,
    HarvestLotAlreadyUsed,
    GrapeVarietyNotFound,
    InvalidGrapePercentage,
)

# Backward compatibility aliases (DEPRECATED - use shared.domain.errors directly)
RepositoryError = FruitOriginError
NotFoundError = VineyardNotFound  # Most common NotFound case
DuplicateCodeError = HarvestLotAlreadyUsed  # Most common duplicate case

# Re-export for convenience
__all__ = [
    "FruitOriginError",
    "VineyardNotFound",
    "InvalidHarvestDate",
    "HarvestLotAlreadyUsed",
    "GrapeVarietyNotFound",
    "InvalidGrapePercentage",
    # Legacy aliases
    "RepositoryError",
    "NotFoundError",
    "DuplicateCodeError",
]
