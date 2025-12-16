"""
Tests for entity builder utilities.

Verifies EntityDefaults, EntityBuilder, and create_test_entity work correctly.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from shared.testing.integration.entity_builders import (
    EntityDefaults,
    EntityBuilder,
    create_test_entity
)


class MockEntity:
    """Mock entity for testing."""
    
    def __init__(self, **kwargs):
        """Initialize with arbitrary fields."""
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestEntityDefaults:
    """Test suite for EntityDefaults."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        defaults = EntityDefaults()
        
        assert defaults.is_deleted is False
        assert defaults.created_at is not None
        assert defaults.updated_at is not None
        assert isinstance(defaults.created_at, datetime)
        assert isinstance(defaults.updated_at, datetime)
    
    def test_custom_is_deleted(self):
        """Test setting custom is_deleted value."""
        defaults = EntityDefaults(is_deleted=True)
        
        assert defaults.is_deleted is True
    
    def test_custom_timestamps(self):
        """Test setting custom timestamp values."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        defaults = EntityDefaults(
            created_at=custom_time,
            updated_at=custom_time
        )
        
        assert defaults.created_at == custom_time
        assert defaults.updated_at == custom_time
    
    def test_timestamps_are_close_to_now(self):
        """Test that auto-generated timestamps are recent."""
        before = datetime.utcnow()
        defaults = EntityDefaults()
        after = datetime.utcnow()
        
        assert before <= defaults.created_at <= after
        assert before <= defaults.updated_at <= after
    
    def test_created_and_updated_are_same_by_default(self):
        """Test that created_at and updated_at are the same when auto-generated."""
        defaults = EntityDefaults()
        
        # Should be very close (same second at least)
        diff = abs((defaults.updated_at - defaults.created_at).total_seconds())
        assert diff < 1  # Less than 1 second apart


class TestEntityBuilder:
    """Test suite for EntityBuilder."""
    
    def test_initialization(self):
        """Test builder initialization."""
        builder = EntityBuilder(MockEntity)
        
        assert builder.entity_class is MockEntity
        assert builder.fields == {}
    
    def test_with_field(self):
        """Test setting a single field."""
        builder = EntityBuilder(MockEntity)
        result = builder.with_field("name", "Test Name")
        
        # Returns self for chaining
        assert result is builder
        assert builder.fields["name"] == "Test Name"
    
    def test_with_multiple_fields_chained(self):
        """Test chaining multiple with_field calls."""
        builder = (
            EntityBuilder(MockEntity)
            .with_field("name", "Test Name")
            .with_field("code", "TEST001")
            .with_field("year", 2024)
        )
        
        assert builder.fields["name"] == "Test Name"
        assert builder.fields["code"] == "TEST001"
        assert builder.fields["year"] == 2024
    
    def test_with_fields_bulk(self):
        """Test setting multiple fields at once."""
        builder = EntityBuilder(MockEntity).with_fields(
            name="Test Name",
            code="TEST001",
            year=2024
        )
        
        assert builder.fields["name"] == "Test Name"
        assert builder.fields["code"] == "TEST001"
        assert builder.fields["year"] == 2024
    
    def test_with_defaults(self):
        """Test applying defaults."""
        defaults = EntityDefaults(is_deleted=False)
        builder = EntityBuilder(MockEntity).with_defaults(defaults)
        
        assert builder.fields["is_deleted"] is False
        assert "created_at" in builder.fields
        assert "updated_at" in builder.fields
    
    def test_with_defaults_doesnt_override(self):
        """Test that defaults don't override explicitly set fields."""
        custom_time = datetime(2020, 1, 1)
        defaults = EntityDefaults()
        
        builder = (
            EntityBuilder(MockEntity)
            .with_field("created_at", custom_time)
            .with_defaults(defaults)
        )
        
        # Should keep the custom value
        assert builder.fields["created_at"] == custom_time
    
    def test_with_unique_code_default_prefix(self):
        """Test unique code generation with default prefix."""
        builder = EntityBuilder(MockEntity).with_unique_code()
        
        code = builder.fields["code"]
        assert code.startswith("TEST-")
        assert len(code) == 13  # "TEST-" + 8 hex chars
    
    def test_with_unique_code_custom_prefix(self):
        """Test unique code generation with custom prefix."""
        builder = EntityBuilder(MockEntity).with_unique_code("WINE")
        
        code = builder.fields["code"]
        assert code.startswith("WINE-")
        assert len(code) == 13  # "WINE-" + 8 hex chars
    
    def test_with_unique_code_generates_different_codes(self):
        """Test that multiple calls generate different codes."""
        builder1 = EntityBuilder(MockEntity).with_unique_code()
        builder2 = EntityBuilder(MockEntity).with_unique_code()
        
        assert builder1.fields["code"] != builder2.fields["code"]
    
    def test_build(self):
        """Test building the entity."""
        entity = (
            EntityBuilder(MockEntity)
            .with_field("name", "Test Name")
            .with_field("code", "TEST001")
            .build()
        )
        
        assert isinstance(entity, MockEntity)
        assert entity.name == "Test Name"
        assert entity.code == "TEST001"
    
    def test_build_with_all_features(self):
        """Test building entity using all builder features."""
        entity = (
            EntityBuilder(MockEntity)
            .with_field("name", "Test Name")
            .with_fields(year=2024, volume=1000)
            .with_unique_code("FERM")
            .with_defaults(EntityDefaults())
            .build()
        )
        
        assert entity.name == "Test Name"
        assert entity.year == 2024
        assert entity.volume == 1000
        assert entity.code.startswith("FERM-")
        assert hasattr(entity, "is_deleted")
        assert hasattr(entity, "created_at")
        assert hasattr(entity, "updated_at")


class TestCreateTestEntity:
    """Test suite for create_test_entity helper."""
    
    @pytest.mark.asyncio
    async def test_creates_and_adds_entity(self):
        """Test that entity is created and added to session."""
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        
        entity = await create_test_entity(
            mock_session,
            MockEntity,
            name="Test Entity"
        )
        
        assert isinstance(entity, MockEntity)
        assert entity.name == "Test Entity"
        mock_session.add.assert_called_once_with(entity)
    
    @pytest.mark.asyncio
    async def test_flushes_session(self):
        """Test that session is flushed to assign ID."""
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        
        await create_test_entity(
            mock_session,
            MockEntity,
            name="Test Entity"
        )
        
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_with_multiple_fields(self):
        """Test creating entity with multiple fields."""
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        
        entity = await create_test_entity(
            mock_session,
            MockEntity,
            name="Test Entity",
            code="TEST001",
            year=2024,
            is_deleted=False
        )
        
        assert entity.name == "Test Entity"
        assert entity.code == "TEST001"
        assert entity.year == 2024
        assert entity.is_deleted is False
    
    @pytest.mark.asyncio
    async def test_returns_entity(self):
        """Test that the created entity is returned."""
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        
        entity = await create_test_entity(
            mock_session,
            MockEntity,
            name="Test Entity"
        )
        
        # Should return the entity that was created
        assert entity is not None
        assert isinstance(entity, MockEntity)
    
    @pytest.mark.asyncio
    async def test_entity_available_after_flush(self):
        """Test that entity is available after flush (simulates ID assignment)."""
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        
        entity = await create_test_entity(
            mock_session,
            MockEntity,
            name="Test Entity"
        )
        
        # Entity should be available for further operations
        assert entity is not None
        mock_session.add.assert_called_once()


class TestEntityBuildersIntegration:
    """Integration tests combining multiple entity builder features."""
    
    def test_builder_and_defaults_together(self):
        """Test using EntityBuilder with EntityDefaults."""
        defaults = EntityDefaults(is_deleted=False)
        
        entity = (
            EntityBuilder(MockEntity)
            .with_field("name", "Integration Test")
            .with_defaults(defaults)
            .build()
        )
        
        assert entity.name == "Integration Test"
        assert entity.is_deleted is False
        assert hasattr(entity, "created_at")
    
    def test_complex_entity_creation(self):
        """Test creating a complex entity with all features."""
        custom_time = datetime(2024, 1, 1)
        defaults = EntityDefaults(
            is_deleted=False,
            created_at=custom_time
        )
        
        entity = (
            EntityBuilder(MockEntity)
            .with_field("name", "Complex Entity")
            .with_fields(year=2024, volume=5000)
            .with_unique_code("COMPLEX")
            .with_defaults(defaults)
            .build()
        )
        
        # All fields should be present
        assert entity.name == "Complex Entity"
        assert entity.year == 2024
        assert entity.volume == 5000
        assert entity.code.startswith("COMPLEX-")
        assert entity.is_deleted is False
        assert entity.created_at == custom_time
        assert hasattr(entity, "updated_at")
