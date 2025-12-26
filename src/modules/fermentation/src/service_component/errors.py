"""
Service layer exceptions for fermentation module.

ADR-026: These exceptions now inherit from the shared domain error hierarchy
for consistent error handling across all modules with RFC 7807 format.

Legacy exceptions are aliased for backward compatibility during migration.
"""

# Import shared domain errors (ADR-026)
from shared.domain.errors import (
    FermentationError,
    FermentationNotFound,
    InvalidFermentationState,
    FermentationAlreadyCompleted,
    SampleNotFound,
    InvalidSampleDate,
    InvalidSampleValue
)

# Backward compatibility aliases (DEPRECATED - will be removed in Phase 4)
ServiceError = FermentationError
NotFoundError = FermentationNotFound  # Generic not found -> specific fermentation not found
ValidationError = InvalidFermentationState  # Validation errors -> invalid state
DuplicateError = FermentationAlreadyCompleted  # For now, conflicts map to "already completed"
BusinessRuleViolation = InvalidFermentationState  # Business rules -> invalid state

# Re-export new errors for direct use
__all__ = [
    # New ADR-026 errors (preferred)
    'FermentationError',
    'FermentationNotFound',
    'InvalidFermentationState',
    'FermentationAlreadyCompleted',
    'SampleNotFound',
    'InvalidSampleDate',
    'InvalidSampleValue',
    # Legacy aliases (deprecated)
    'ServiceError',
    'NotFoundError',
    'ValidationError',
    'DuplicateError',
    'BusinessRuleViolation',
]
