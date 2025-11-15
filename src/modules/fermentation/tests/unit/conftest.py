"""
Shared test fixtures and configuration for unit tests.
Organized by functional areas rather than technical layers.
"""

import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_timestamp():
    """Fixture providing a standard timestamp for test samples."""
    return datetime.now()


@pytest.fixture
def fermentation_id():
    """Fixture providing a standard fermentation ID for tests."""
    return 12345


@pytest.fixture
def winery_id():
    """Fixture providing a standard winery ID for tests."""
    return 67890


@pytest.fixture
def valid_measurements():
    """Fixture providing valid sample measurements for tests."""
    return {
        "glucose": 12.5,
        "ethanol": 8.2,
        "temperature": 18.5
    }


@pytest.fixture
def chronological_timestamps():
    """Fixture providing a series of chronological timestamps."""
    base_time = datetime.now() - timedelta(days=7)
    return [
        base_time + timedelta(hours=i * 6) 
        for i in range(10)
    ]


@pytest.fixture
def database_config():
    """Fixture providing database configuration for tests."""
    import os
    from unittest.mock import patch
    
    # Use test database URL for development (port 5433)
    test_env = {
        'DATABASE_URL': 'postgresql://postgres:postgres@localhost:5433/wine_fermentation_test',
        'DB_ECHO': 'false',
        'DB_POOL_SIZE': '5',
        'DB_MAX_OVERFLOW': '10'
    }
    
    with patch.dict(os.environ, test_env):
        from src.shared.infra.database import DatabaseConfig
        yield DatabaseConfig()
