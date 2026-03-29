"""
Unit tests for seed_initial_data.py script.

Following TDD approach:
- Phase 1: Write tests (RED) ✅
- Phase 2: Implement script (GREEN)
- Phase 3: Integration test (GREEN)
- Phase 4: Refactor (REFACTOR) — async migration

ADR-018: Seed Script for Initial Data Bootstrap
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# Test: load_seed_config()
# =============================================================================

def test_load_seed_config_success():
    """Test loading valid YAML configuration file."""
    # Arrange
    config_path = "test_seed_config.yaml"
    expected_config = {
        "winery": {
            "code": "TEST-WINERY",
            "name": "Test Winery",
            "location": "Test Location",
            "notes": "Test notes"
        },
        "admin_user": {
            "username": "testadmin",
            "email": "testadmin@example.com",
            "password": "testpass",
            "full_name": "Test Admin"
        }
    }

    from scripts.seed_initial_data import load_seed_config
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value = yaml.dump(expected_config)

        result = load_seed_config(config_path)

        assert result == expected_config
        assert result["winery"]["code"] == "TEST-WINERY"
        assert result["admin_user"]["email"] == "testadmin@example.com"


def test_load_seed_config_file_not_found():
    """Test handling of missing configuration file."""
    config_path = "nonexistent.yaml"

    from scripts.seed_initial_data import load_seed_config
    with pytest.raises(FileNotFoundError):
        load_seed_config(config_path)


# =============================================================================
# Test: create_initial_winery()
# =============================================================================

@pytest.mark.asyncio
async def test_create_initial_winery_new():
    """Test creating winery when it doesn't exist (happy path)."""
    config = {
        "winery": {
            "code": "NEW-WINERY",
            "name": "New Winery",
            "location": "California",
            "notes": "Test winery"
        }
    }

    mock_session = AsyncMock()
    # execute() is awaited; its return value must be a sync MagicMock so
    # result.scalars().first() works without being a coroutine.
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    from scripts.seed_initial_data import create_initial_winery
    result = await create_initial_winery(config, mock_session)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result.code == "NEW-WINERY"
    assert result.name == "New Winery"


@pytest.mark.asyncio
async def test_create_initial_winery_already_exists():
    """Test idempotency - skip creation if winery exists."""
    config = {
        "winery": {
            "code": "EXISTING-WINERY",
            "name": "Existing Winery"
        }
    }

    mock_session = AsyncMock()
    existing_winery = MagicMock(id=1, code="EXISTING-WINERY")
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_winery
    mock_session.execute.return_value = mock_result

    from scripts.seed_initial_data import create_initial_winery
    result = await create_initial_winery(config, mock_session)

    assert result == existing_winery
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_awaited()


# =============================================================================
# Test: create_admin_user()
# =============================================================================

@pytest.mark.asyncio
async def test_create_admin_user_new():
    """Test creating admin user when doesn't exist (happy path)."""
    config = {
        "admin_user": {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin",
            "full_name": "System Admin"
        }
    }
    winery_id = 1

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    from scripts.seed_initial_data import create_admin_user
    result = await create_admin_user(config, winery_id, mock_session)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert result.username == "admin"
    assert result.email == "admin@example.com"


@pytest.mark.asyncio
async def test_create_admin_user_already_exists():
    """Test idempotency - skip creation if admin exists."""
    config = {
        "admin_user": {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin"
        }
    }
    winery_id = 1

    mock_session = AsyncMock()
    existing_user = MagicMock(id=1, email="admin@example.com")
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_user
    mock_session.execute.return_value = mock_result

    from scripts.seed_initial_data import create_admin_user
    result = await create_admin_user(config, winery_id, mock_session)

    assert result == existing_user
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_awaited()


# =============================================================================
# Test: seed_all() - Main Entry Point
# =============================================================================

@pytest.mark.asyncio
async def test_seed_all_success():
    """Test complete seed operation (happy path)."""
    config_path = "test_config.yaml"

    mock_config = {
        "winery": {"code": "TEST", "name": "Test Winery"},
        "admin_user": {"username": "admin", "email": "admin@test.com", "password": "admin"}
    }

    mock_winery = MagicMock(id=1, code="TEST")
    mock_user = MagicMock(id=1, email="admin@test.com")

    # Mock the async context manager returned by get_session()
    mock_session = AsyncMock()
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)

    mock_db_session = MagicMock()
    mock_db_session.get_session.return_value = mock_session_cm
    mock_db_session.close = AsyncMock()

    with patch('scripts.seed_initial_data.load_seed_config', return_value=mock_config), \
         patch('scripts.seed_initial_data.create_initial_winery', return_value=mock_winery), \
         patch('scripts.seed_initial_data.create_admin_user', return_value=mock_user), \
         patch('scripts.seed_initial_data.DatabaseConfig'), \
         patch('scripts.seed_initial_data.DatabaseSession', return_value=mock_db_session):

        from scripts.seed_initial_data import seed_all
        result = await seed_all(config_path)

        assert result is not None
        assert "winery" in result
        assert "admin_user" in result
        assert result["winery"] == mock_winery
        assert result["admin_user"] == mock_user
        mock_db_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_seed_all_idempotent():
    """Test that running seed multiple times is safe (idempotency)."""
    config_path = "test_config.yaml"

    mock_config = {
        "winery": {"code": "EXISTING", "name": "Existing Winery"},
        "admin_user": {"email": "existing@test.com", "username": "admin", "password": "admin"}
    }

    mock_winery = MagicMock(id=1, code="EXISTING")
    mock_user = MagicMock(id=1, email="existing@test.com")

    mock_session = AsyncMock()
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)

    mock_db_session = MagicMock()
    mock_db_session.get_session.return_value = mock_session_cm
    mock_db_session.close = AsyncMock()

    with patch('scripts.seed_initial_data.load_seed_config', return_value=mock_config), \
         patch('scripts.seed_initial_data.create_initial_winery', return_value=mock_winery), \
         patch('scripts.seed_initial_data.create_admin_user', return_value=mock_user), \
         patch('scripts.seed_initial_data.DatabaseConfig'), \
         patch('scripts.seed_initial_data.DatabaseSession', return_value=mock_db_session):

        from scripts.seed_initial_data import seed_all

        result1 = await seed_all(config_path)

        # Reset close mock for second run
        mock_db_session.close.reset_mock()

        result2 = await seed_all(config_path)

        assert result1 is not None
        assert result2 is not None
        assert result1["winery"].id == result2["winery"].id
        assert result1["admin_user"].id == result2["admin_user"].id

