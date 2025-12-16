"""
Integration testing infrastructure.

Provides shared fixtures, utilities, and helpers for integration tests
across all modules.

Key Components:
- IntegrationTestConfig: Configuration for module test setup
- create_integration_fixtures(): Factory for standard test fixtures
- TestSessionManager: Repository-compatible session wrapper
- create_repository_fixture(): Dynamic repository fixture creation
- EntityBuilder: Fluent API for test entity creation
"""

from .base_conftest import IntegrationTestConfig, create_integration_fixtures
from .session_manager import TestSessionManager
from .fixtures import create_repository_fixture
from .entity_builders import EntityBuilder, EntityDefaults, create_test_entity

__all__ = [
    "IntegrationTestConfig",
    "create_integration_fixtures",
    "TestSessionManager",
    "create_repository_fixture",
    "EntityBuilder",
    "EntityDefaults",
    "create_test_entity",
]
