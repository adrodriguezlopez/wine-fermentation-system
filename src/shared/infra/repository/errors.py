"""
Repository Error Infrastructure
================================
Canonical error types and SQLAlchemy error mapper shared by all repositories.

All concrete module repositories (fermentation, fruit_origin, winery, etc.)
import and re-export these types so callers can use either the shared path or
the module-local path interchangeably.
"""

from typing import Optional


class RepositoryError(Exception):
    """Base repository error."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class EntityNotFoundError(RepositoryError):
    """Entity not found in repository."""
    pass


class DuplicateEntityError(RepositoryError):
    """Entity already exists (unique constraint violation)."""
    pass


class ReferentialIntegrityError(RepositoryError):
    """Foreign key constraint violation."""
    pass


class OptimisticLockError(RepositoryError):
    """Optimistic locking conflict during update."""

    def __init__(self, message: str, expected_version: int, actual_version: int):
        super().__init__(message)
        self.expected_version = expected_version
        self.actual_version = actual_version


class ConcurrentModificationError(RepositoryError):
    """Concurrent modification detected."""
    pass


class DatabaseConnectionError(RepositoryError):
    """Database connection issues."""
    pass


class RetryableConcurrencyError(RepositoryError):
    """Retryable concurrency error (deadlock, serialization failure)."""
    pass


def map_database_error(error: Exception) -> RepositoryError:
    """
    Map SQLAlchemy/PostgreSQL errors to repository-specific errors.

    PostgreSQL SQLSTATE codes:
    - 23505: unique_violation
    - 23503: foreign_key_violation
    - 40001: serialization_failure
    - 40P01: deadlock_detected

    Returns the original error unchanged if it is already a RepositoryError.
    """
    if isinstance(error, RepositoryError):
        return error

    error_str = str(error)

    try:
        from sqlalchemy.exc import IntegrityError, OperationalError

        if isinstance(error, IntegrityError):
            if "23505" in error_str:  # unique_violation
                return DuplicateEntityError(f"Entity already exists: {error_str}", error)
            elif "23503" in error_str:  # foreign_key_violation
                return ReferentialIntegrityError(
                    f"Foreign key constraint violated: {error_str}", error
                )

        elif isinstance(error, OperationalError):
            if "40001" in error_str:  # serialization_failure
                return RetryableConcurrencyError(
                    f"Serialization failure: {error_str}", error
                )
            elif "40P01" in error_str:  # deadlock_detected
                return RetryableConcurrencyError(
                    f"Deadlock detected: {error_str}", error
                )
            else:
                return DatabaseConnectionError(
                    f"Database operation failed: {error_str}", error
                )

    except ImportError:
        pass

    return RepositoryError(f"Database error: {error_str}", error)


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
