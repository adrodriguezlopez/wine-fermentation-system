"""
Unit tests for repository error classes.

Testing basic error hierarchy, message handling, and error chaining.
Following TDD approach - test first, implement as needed.
"""

import pytest
import sys
from pathlib import Path
import importlib.util

# Helper para cargar el módulo errors directamente del archivo
def get_errors_module():
    """Load errors module directly from file."""
    errors_file = Path(__file__).parent.parent.parent.parent / "src" / "repository_component" / "errors.py"
    spec = importlib.util.spec_from_file_location("errors", errors_file)
    errors_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(errors_module)
    return errors_module

# Cargar el módulo una vez para el archivo
errors = get_errors_module()


class TestRepositoryErrorHierarchy:
    """Test the basic error class hierarchy and inheritance."""
    
    def test_repository_error_is_base_exception(self):
        """Test that RepositoryError inherits from Exception."""
        error = errors.RepositoryError("test message")
        assert isinstance(error, Exception)
        assert str(error) == "test message"
    
    def test_repository_error_with_original_error(self):
        """Test RepositoryError can chain original exceptions."""
        original = ValueError("original error")
        error = errors.RepositoryError("wrapped error", original)
        
        assert str(error) == "wrapped error"
        assert error.original_error is original
    
    def test_entity_not_found_error_inheritance(self):
        """Test EntityNotFoundError inherits from RepositoryError."""
        error = errors.EntityNotFoundError("Entity not found")
        assert isinstance(error, errors.RepositoryError)
        assert isinstance(error, Exception)
        assert str(error) == "Entity not found"
    
    def test_duplicate_entity_error_inheritance(self):
        """Test DuplicateEntityError inherits from RepositoryError."""
        error = errors.DuplicateEntityError("Entity already exists")
        assert isinstance(error, errors.RepositoryError)
        assert str(error) == "Entity already exists"
    
    def test_referential_integrity_error_inheritance(self):
        """Test ReferentialIntegrityError inherits from RepositoryError."""
        error = errors.ReferentialIntegrityError("Foreign key violation")
        assert isinstance(error, errors.RepositoryError)
        assert str(error) == "Foreign key violation"
    
    def test_database_connection_error_inheritance(self):
        """Test DatabaseConnectionError inherits from RepositoryError."""
        error = errors.DatabaseConnectionError("Connection failed")
        assert isinstance(error, errors.RepositoryError)
        assert str(error) == "Connection failed"
    
    def test_concurrent_modification_error_inheritance(self):
        """Test ConcurrentModificationError inherits from RepositoryError."""
        error = errors.ConcurrentModificationError("Concurrent modification")
        assert isinstance(error, errors.RepositoryError)
        assert str(error) == "Concurrent modification"
    
    def test_retryable_concurrency_error_inheritance(self):
        """Test RetryableConcurrencyError inherits from RepositoryError."""
        error = errors.RetryableConcurrencyError("Deadlock detected")
        assert isinstance(error, errors.RepositoryError)
        assert str(error) == "Deadlock detected"


class TestOptimisticLockError:
    """Test OptimisticLockError with version tracking."""
    
    def test_optimistic_lock_error_basic(self):
        """Test basic OptimisticLockError creation."""
        error = errors.OptimisticLockError("Version mismatch", 5, 7)
        
        assert isinstance(error, errors.RepositoryError)
        assert str(error) == "Version mismatch"
        assert error.expected_version == 5
        assert error.actual_version == 7
    
    def test_optimistic_lock_error_version_access(self):
        """Test version information is accessible."""
        error = errors.OptimisticLockError("Conflict detected", 10, 15)
        
        # Should be able to access version information for conflict resolution
        assert error.expected_version == 10
        assert error.actual_version == 15
        
        # Should still be a proper exception
        assert isinstance(error, Exception)
    
    def test_optimistic_lock_error_with_string_versions(self):
        """Test OptimisticLockError handles different version types."""
        # Should work with any comparable types, not just ints
        error = errors.OptimisticLockError("Version conflict", "v1.0", "v1.5")
        
        assert error.expected_version == "v1.0"
        assert error.actual_version == "v1.5"


class TestErrorChaining:
    """Test original error preservation and chaining."""
    
    def test_error_chaining_with_none(self):
        """Test error creation without original error."""
        error = errors.RepositoryError("Simple error")
        assert error.original_error is None
    
    def test_error_chaining_with_exception(self):
        """Test error chaining preserves original exception."""
        original = ValueError("Database constraint failed")
        error = errors.DuplicateEntityError("User already exists", original)
        
        assert error.original_error is original
        assert isinstance(error.original_error, ValueError)
        assert str(error.original_error) == "Database constraint failed"
    
    def test_error_chaining_multiple_levels(self):
        """Test multiple levels of error chaining."""
        database_error = ConnectionError("Network timeout")
        wrapped_error = errors.DatabaseConnectionError("DB connection lost", database_error)
        final_error = errors.RepositoryError("Operation failed", wrapped_error)
        
        assert final_error.original_error is wrapped_error
        assert wrapped_error.original_error is database_error
        assert isinstance(database_error, ConnectionError)
    
    def test_subclass_errors_with_chaining(self):
        """Test all error subclasses support error chaining."""
        original = RuntimeError("Original error")
        
        errors_to_test = [
            errors.EntityNotFoundError("Not found", original),
            errors.DuplicateEntityError("Duplicate", original), 
            errors.ReferentialIntegrityError("Integrity", original),
            errors.DatabaseConnectionError("Connection", original),
            errors.ConcurrentModificationError("Concurrent", original),
            errors.RetryableConcurrencyError("Retryable", original)
        ]
        
        for error in errors_to_test:
            assert error.original_error is original
            assert isinstance(error, errors.RepositoryError)


class TestErrorMessages:
    """Test error message handling and formatting."""
    
    def test_empty_message(self):
        """Test error with empty message."""
        error = errors.RepositoryError("")
        assert str(error) == ""
    
    def test_none_message_handling(self):
        """Test error behavior with None message."""
        # Should this raise an error or handle gracefully?
        # Let's test current behavior first
        try:
            error = errors.RepositoryError(None)
            # If this doesn't raise, check what str() returns
            message = str(error)
        except TypeError:
            # If it raises TypeError, that's also valid behavior
            pytest.skip("RepositoryError doesn't accept None message")
    
    def test_multiline_message(self):
        """Test error with multiline message."""
        message = "Line 1\nLine 2\nLine 3"
        error = errors.RepositoryError(message)
        assert str(error) == message
    
    def test_unicode_message(self):
        """Test error with unicode characters."""
        message = "Error: código de recipiente duplicado 🍷"
        error = errors.DuplicateEntityError(message)
        assert str(error) == message
