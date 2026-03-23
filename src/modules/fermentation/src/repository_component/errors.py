"""
Repository Error Infrastructure
================================
Re-exports canonical error types from src.shared.infra.repository.errors.

All error classes are defined once in the shared package. This module
re-exports them so existing imports (src.modules.fermentation.src.repository_component.errors.*)
continue to work without change.
"""

from src.shared.infra.repository.errors import (
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
    ReferentialIntegrityError,
    OptimisticLockError,
    ConcurrentModificationError,
    DatabaseConnectionError,
    RetryableConcurrencyError,
    map_database_error,
)

__all__ = [
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "ReferentialIntegrityError",
    "OptimisticLockError",
    "ConcurrentModificationError",
    "DatabaseConnectionError",
    "RetryableConcurrencyError",
    "map_database_error",
]
