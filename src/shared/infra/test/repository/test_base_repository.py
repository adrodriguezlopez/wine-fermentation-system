import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import select, text

from src.shared.infra.interfaces.session_manager import ISessionManager


class TestBaseRepository:
    """Test suite for BaseRepository class."""

    # Grupo 1: Inicialización y Dependency Injection
    @pytest.mark.asyncio
    async def test_base_repository_requires_session_manager(self):
        """BaseRepository should require ISessionManager for initialization (Dependency Inversion)."""
        from src.shared.infra.repository.base_repository import BaseRepository

        # Should raise TypeError when no session_manager provided
        with pytest.raises(TypeError, match="missing.*session_manager"):
            BaseRepository()

    @pytest.mark.asyncio
    async def test_base_repository_validates_session_manager_interface(self):
        """BaseRepository should reject objects that don't implement ISessionManager."""
        from src.shared.infra.repository.base_repository import BaseRepository

        # Object that doesn't implement ISessionManager (missing required methods)
        class InvalidSessionManager:
            pass

        invalid_session_manager = InvalidSessionManager()

        # Should raise TypeError for invalid interface
        with pytest.raises(TypeError, match="ISessionManager"):
            BaseRepository(session_manager=invalid_session_manager)

    @pytest.mark.asyncio
    async def test_base_repository_stores_session_manager_reference(self):
        """BaseRepository should store session_manager reference correctly."""
        from src.shared.infra.repository.base_repository import BaseRepository

        mock_session_manager = Mock(spec=ISessionManager)
        repository = BaseRepository(session_manager=mock_session_manager)

        assert repository.session_manager is mock_session_manager

    # Grupo 2: Session Management (Core Infrastructure)
    @pytest.mark.asyncio
    async def test_get_session_delegates_to_session_manager(self):
        """get_session should delegate to the session manager."""
        from src.shared.infra.repository.base_repository import BaseRepository

        mock_session_manager = Mock(spec=ISessionManager)
        mock_context_manager = Mock()
        mock_session_manager.get_session = AsyncMock(return_value=mock_context_manager)

        repository = BaseRepository(session_manager=mock_session_manager)
        result = await repository.get_session()

        mock_session_manager.get_session.assert_called_once()
        assert result is mock_context_manager

    @pytest.mark.asyncio
    async def test_get_session_returns_context_manager(self):
        """get_session should return an AsyncContextManager."""
        from src.shared.infra.repository.base_repository import BaseRepository
        from typing import AsyncContextManager

        mock_session_manager = Mock(spec=ISessionManager)
        mock_context_manager = Mock(spec=AsyncContextManager)
        mock_session_manager.get_session = AsyncMock(return_value=mock_context_manager)

        repository = BaseRepository(session_manager=mock_session_manager)
        result = await repository.get_session()

        assert result is mock_context_manager

    @pytest.mark.asyncio
    async def test_repository_close_cleanup(self):
        """close should delegate to the session manager."""
        from src.shared.infra.repository.base_repository import BaseRepository

        mock_session_manager = Mock(spec=ISessionManager)
        mock_session_manager.close = AsyncMock()

        repository = BaseRepository(session_manager=mock_session_manager)
        await repository.close()

        mock_session_manager.close.assert_called_once()

    # Grupo 3: Error Mapping (Integration con errors.py)
    @pytest.mark.asyncio
    async def test_map_database_error_integrity_violation(self):
        """BaseRepository should handle IntegrityError with unique violation."""
        from src.shared.infra.repository.base_repository import BaseRepository
        from src.modules.fermentation.src.repository_component.errors import DuplicateEntityError

        repository = BaseRepository(session_manager=Mock(spec=ISessionManager))

        # Create IntegrityError with unique violation SQLSTATE
        integrity_error = IntegrityError(
            statement="INSERT INTO test",
            params=None,
            orig=Exception("23505: unique_violation")
        )

        async def failing_operation():
            raise integrity_error

        # Should map to DuplicateEntityError
        with pytest.raises(DuplicateEntityError) as exc_info:
            await repository.execute_with_error_mapping(failing_operation)

        assert "Entity already exists" in str(exc_info.value)
        assert exc_info.value.original_error is integrity_error

    @pytest.mark.asyncio
    async def test_map_database_error_foreign_key_violation(self):
        """BaseRepository should handle IntegrityError with foreign key violation."""
        from src.shared.infra.repository.base_repository import BaseRepository
        from src.modules.fermentation.src.repository_component.errors import ReferentialIntegrityError

        repository = BaseRepository(session_manager=Mock(spec=ISessionManager))

        # Create IntegrityError with foreign key violation SQLSTATE
        integrity_error = IntegrityError(
            statement="INSERT INTO test",
            params=None,
            orig=Exception("23503: foreign_key_violation")
        )

        async def failing_operation():
            raise integrity_error

        # Should map to ReferentialIntegrityError
        with pytest.raises(ReferentialIntegrityError) as exc_info:
            await repository.execute_with_error_mapping(failing_operation)

        assert "Foreign key constraint violated" in str(exc_info.value)
        assert exc_info.value.original_error is integrity_error

    @pytest.mark.asyncio
    async def test_map_database_error_unknown_exception(self):
        """BaseRepository should handle unknown exceptions with generic RepositoryError."""
        from src.shared.infra.repository.base_repository import BaseRepository
        from src.modules.fermentation.src.repository_component.errors import RepositoryError

        repository = BaseRepository(session_manager=Mock(spec=ISessionManager))

        original_error = ValueError("Some unknown error")

        async def failing_operation():
            raise original_error

        # Should map to generic RepositoryError
        with pytest.raises(RepositoryError) as exc_info:
            await repository.execute_with_error_mapping(failing_operation)

        assert "Database error" in str(exc_info.value)
        assert exc_info.value.original_error is original_error

    @pytest.mark.asyncio
    async def test_execute_with_error_mapping_wraps_operations(self):
        """execute_with_error_mapping should wrap operations and map errors."""
        from src.shared.infra.repository.base_repository import BaseRepository

        repository = BaseRepository(session_manager=Mock(spec=ISessionManager))

        # Successful operation should return result
        async def successful_operation():
            return "success"

        result = await repository.execute_with_error_mapping(successful_operation)
        assert result == "success"

    # Grupo 4: Multi-tenant Scoping (Seguridad)
    @pytest.mark.asyncio
    async def test_scope_query_by_winery_id_adds_filter(self):
        """scope_query_by_winery_id should add winery_id filter to queries."""
        from src.shared.infra.repository.base_repository import BaseRepository

        repository = BaseRepository(session_manager=Mock(spec=ISessionManager))

        # Mock query object
        mock_query = Mock()
        mock_query.where = Mock(return_value=mock_query)
        mock_query.params = Mock(return_value=mock_query)

        result = repository.scope_query_by_winery_id(mock_query, winery_id=123)

        # Verify the query was modified with winery_id filter
        mock_query.where.assert_called_once()
        mock_query.params.assert_called_once_with(winery_id=123)
        assert result is mock_query

    @pytest.mark.asyncio
    async def test_scope_query_by_winery_id_validates_input(self):
        """scope_query_by_winery_id should validate winery_id input."""
        from src.shared.infra.repository.base_repository import BaseRepository

        repository = BaseRepository(session_manager=Mock(spec=ISessionManager))
        mock_query = Mock()

        # Invalid winery_id values should raise ValueError
        with pytest.raises(ValueError, match="winery_id must be a positive integer"):
            repository.scope_query_by_winery_id(mock_query, winery_id=0)

        with pytest.raises(ValueError, match="winery_id must be a positive integer"):
            repository.scope_query_by_winery_id(mock_query, winery_id=-1)

        with pytest.raises(ValueError, match="winery_id must be a positive integer"):
            repository.scope_query_by_winery_id(mock_query, winery_id="123")

    @pytest.mark.asyncio
    async def test_scope_query_preserves_existing_filters(self):
        """scope_query_by_winery_id should preserve existing query filters."""
        from src.shared.infra.repository.base_repository import BaseRepository

        repository = BaseRepository(session_manager=Mock(spec=ISessionManager))

        # Mock query with existing filters
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_query.where = Mock(return_value=mock_filtered_query)
        mock_filtered_query.params = Mock(return_value=mock_filtered_query)

        result = repository.scope_query_by_winery_id(mock_query, winery_id=456)

        # Verify the method returns the filtered query (preserving existing filters)
        assert result is mock_filtered_query

    # Grupo 5: Soft Delete Support
    @pytest.mark.asyncio
    async def test_apply_soft_delete_filter_excludes_deleted(self):
        """apply_soft_delete_filter should exclude soft-deleted records by default."""
        from src.shared.infra.repository.base_repository import BaseRepository

        repository = BaseRepository(session_manager=Mock(spec=ISessionManager))

        # Mock query
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_query.where = Mock(return_value=mock_filtered_query)

        result = repository.apply_soft_delete_filter(mock_query)

        # Should apply filter to exclude deleted records
        mock_query.where.assert_called_once()
        assert result is mock_filtered_query

    @pytest.mark.asyncio
    async def test_apply_soft_delete_filter_optional_for_entities(self):
        """apply_soft_delete_filter should be optional and work with include_deleted."""
        from src.shared.infra.repository.base_repository import BaseRepository

        repository = BaseRepository(session_manager=Mock(spec=ISessionManager))

        # Mock query
        mock_query = Mock()

        # When include_deleted=True, should not apply filter
        result = repository.apply_soft_delete_filter(mock_query, include_deleted=True)

        # Should return original query without filtering
        mock_query.where.assert_not_called()
        assert result is mock_query

    @pytest.mark.asyncio
    async def test_soft_delete_with_winery_scoping_combined(self):
        """Soft delete and winery scoping should work together."""
        from src.shared.infra.repository.base_repository import BaseRepository

        repository = BaseRepository(session_manager=Mock(spec=ISessionManager))

        # Mock query
        mock_query = Mock()

        # Apply winery scoping first
        scoped_query = repository.scope_query_by_winery_id(mock_query, winery_id=789)

        # Then apply soft delete filter
        final_query = repository.apply_soft_delete_filter(scoped_query)

        # Both methods should have been called
        mock_query.where.assert_called()  # Called by scope_query_by_winery_id
        assert final_query is not mock_query  # Should be a filtered query