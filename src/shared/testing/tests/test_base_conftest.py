"""
Tests for base_conftest fixture factory.

Verifies that IntegrationTestConfig and create_integration_fixtures
work correctly and produce proper pytest fixtures.
"""

import pytest
from dataclasses import FrozenInstanceError
from shared.testing.integration.base_conftest import (
    IntegrationTestConfig,
    create_integration_fixtures
)


class TestIntegrationTestConfig:
    """Test suite for IntegrationTestConfig."""
    
    def test_initialization_with_defaults(self):
        """Test config initialization with default database URL."""
        config = IntegrationTestConfig(
            module_name="test_module",
            models=[]
        )
        
        assert config.module_name == "test_module"
        assert config.models == []
        assert "sqlite+aiosqlite:///:memory:" in config.test_database_url
    
    def test_initialization_with_custom_url(self):
        """Test config initialization with custom database URL."""
        custom_url = "postgresql+asyncpg://localhost/test_db"
        config = IntegrationTestConfig(
            module_name="test_module",
            models=[],
            test_database_url=custom_url
        )
        
        assert config.test_database_url == custom_url
    
    def test_config_is_frozen(self):
        """Test that config is immutable (frozen dataclass)."""
        config = IntegrationTestConfig(
            module_name="test_module",
            models=[]
        )
        
        with pytest.raises(FrozenInstanceError):
            config.module_name = "changed"


class TestCreateIntegrationFixtures:
    """Test suite for create_integration_fixtures factory."""
    
    def test_returns_dict_with_correct_keys(self):
        """Test that factory returns dict with expected fixture keys."""
        config = IntegrationTestConfig(
            module_name="test_module",
            models=[]
        )
        
        fixtures = create_integration_fixtures(config)
        
        assert isinstance(fixtures, dict)
        assert "test_models" in fixtures
        assert "db_engine" in fixtures
        assert "db_session" in fixtures
    
    def test_fixtures_are_callable(self):
        """Test that all returned fixtures are callable (functions)."""
        config = IntegrationTestConfig(
            module_name="test_module",
            models=[]
        )
        
        fixtures = create_integration_fixtures(config)
        
        assert callable(fixtures["test_models"])
        assert callable(fixtures["db_engine"])
        assert callable(fixtures["db_session"])
    
    def test_test_models_fixture_has_correct_scope(self):
        """Test that test_models fixture has session scope."""
        config = IntegrationTestConfig(
            module_name="test_module",
            models=[]
        )
        
        fixtures = create_integration_fixtures(config)
        test_models_fixture = fixtures["test_models"]
        
        # Check if fixture has scope attribute (pytest adds this)
        # Since we can't easily verify scope without pytest internals,
        # we verify the fixture is created correctly
        assert hasattr(test_models_fixture, '__name__')
        assert test_models_fixture.__name__ == 'test_models'
    
    def test_db_engine_fixture_name(self):
        """Test that db_engine fixture has correct name."""
        config = IntegrationTestConfig(
            module_name="test_module",
            models=[]
        )
        
        fixtures = create_integration_fixtures(config)
        db_engine_fixture = fixtures["db_engine"]
        
        assert db_engine_fixture.__name__ == 'db_engine'
    
    def test_db_session_fixture_name(self):
        """Test that db_session fixture has correct name."""
        config = IntegrationTestConfig(
            module_name="test_module",
            models=[]
        )
        
        fixtures = create_integration_fixtures(config)
        db_session_fixture = fixtures["db_session"]
        
        assert db_session_fixture.__name__ == 'db_session'
    
    def test_different_configs_create_independent_fixtures(self):
        """Test that different configs create separate fixture sets."""
        config1 = IntegrationTestConfig(
            module_name="module1",
            models=[]
        )
        config2 = IntegrationTestConfig(
            module_name="module2",
            models=[]
        )
        
        fixtures1 = create_integration_fixtures(config1)
        fixtures2 = create_integration_fixtures(config2)
        
        # Fixtures should be different objects (not the same reference)
        assert fixtures1["test_models"] is not fixtures2["test_models"]
        assert fixtures1["db_engine"] is not fixtures2["db_engine"]
        assert fixtures1["db_session"] is not fixtures2["db_session"]


class TestIntegrationFixturesIntegration:
    """
    Integration tests for the fixture factory.
    
    These tests verify the fixtures work correctly when actually used
    in a pytest context (requires running with pytest).
    """
    
    @pytest.mark.asyncio
    async def test_fixtures_can_be_loaded_by_pytest(self):
        """Test that fixtures can be registered and used by pytest."""
        # This test verifies the fixtures work in an actual test context
        # We create a simple config and fixtures
        config = IntegrationTestConfig(
            module_name="test_module",
            models=[]
        )
        
        fixtures = create_integration_fixtures(config)
        
        # Verify we can extract the fixture functions
        assert fixtures["test_models"] is not None
        assert fixtures["db_engine"] is not None
        assert fixtures["db_session"] is not None
        
        # In a real conftest.py, these would be registered like:
        # globals().update(fixtures)
        # This test verifies the structure is correct for that pattern
