"""
Unit tests for seed_initial_data.py script.

Following TDD approach:
- Phase 1: Write tests (RED) ✅
- Phase 2: Implement script (GREEN)
- Phase 3: Integration test (GREEN)
- Phase 4: Refactor (REFACTOR)

ADR-018: Seed Script for Initial Data Bootstrap
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock
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
    
    # Mock file operations
    from scripts.seed_initial_data import load_seed_config
    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value = yaml.dump(expected_config)
        
        # Act
        result = load_seed_config(config_path)
        
        # Assert
        assert result == expected_config
        assert result["winery"]["code"] == "TEST-WINERY"
        assert result["admin_user"]["email"] == "testadmin@example.com"


def test_load_seed_config_file_not_found():
    """Test handling of missing configuration file."""
    # Arrange
    config_path = "nonexistent.yaml"
    
    # Act & Assert
    from scripts.seed_initial_data import load_seed_config
    with pytest.raises(FileNotFoundError):
        load_seed_config(config_path)


# =============================================================================
# Test: create_initial_winery()
# =============================================================================

def test_create_initial_winery_new():
    """Test creating winery when it doesn't exist (happy path)."""
    # Arrange
    config = {
        "winery": {
            "code": "NEW-WINERY",
            "name": "New Winery",
            "location": "California",
            "notes": "Test winery"
        }
    }
    
    mock_session = Mock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = None  # Doesn't exist
    
    # Act
    from scripts.seed_initial_data import create_initial_winery
    result = create_initial_winery(config, mock_session)
    
    # Assert
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert result.code == "NEW-WINERY"
    assert result.name == "New Winery"


def test_create_initial_winery_already_exists():
    """Test idempotency - skip creation if winery exists."""
    # Arrange
    config = {
        "winery": {
            "code": "EXISTING-WINERY",
            "name": "Existing Winery"
        }
    }
    
    mock_session = Mock()
    existing_winery = Mock(id=1, code="EXISTING-WINERY")
    mock_session.query.return_value.filter_by.return_value.first.return_value = existing_winery
    
    # Act
    from scripts.seed_initial_data import create_initial_winery
    result = create_initial_winery(config, mock_session)
    
    # Assert
    assert result == existing_winery
    mock_session.add.assert_not_called()  # Idempotent - don't create
    mock_session.commit.assert_not_called()


# =============================================================================
# Test: create_admin_user()
# =============================================================================

def test_create_admin_user_new():
    """Test creating admin user when doesn't exist (happy path)."""
    # Arrange
    config = {
        "admin_user": {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin",
            "full_name": "System Admin"
        }
    }
    winery_id = 1
    
    mock_session = Mock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = None  # Doesn't exist
    
    # Act
    from scripts.seed_initial_data import create_admin_user
    result = create_admin_user(config, winery_id, mock_session)
    
    # Assert
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert result.username == "admin"
    assert result.email == "admin@example.com"


def test_create_admin_user_already_exists():
    """Test idempotency - skip creation if admin exists."""
    # Arrange
    config = {
        "admin_user": {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin"
        }
    }
    winery_id = 1
    
    mock_session = Mock()
    existing_user = Mock(id=1, email="admin@example.com")
    mock_session.query.return_value.filter_by.return_value.first.return_value = existing_user
    
    # Act
    from scripts.seed_initial_data import create_admin_user
    result = create_admin_user(config, winery_id, mock_session)
    
    # Assert
    assert result == existing_user
    mock_session.add.assert_not_called()  # Idempotent - don't create
    mock_session.commit.assert_not_called()


# =============================================================================
# Test: seed_all() - Main Entry Point
# =============================================================================

def test_seed_all_success():
    """Test complete seed operation (happy path)."""
    # Arrange
    config_path = "test_config.yaml"
    
    # Mock dependencies
    mock_config = {
        "winery": {"code": "TEST", "name": "Test Winery"},
        "admin_user": {"username": "admin", "email": "admin@test.com", "password": "admin"}
    }
    
    mock_winery = Mock(id=1, code="TEST")
    mock_user = Mock(id=1, email="admin@test.com")
    
    # Act & Assert
    with patch('scripts.seed_initial_data.load_seed_config', return_value=mock_config), \
         patch('scripts.seed_initial_data.create_initial_winery', return_value=mock_winery), \
         patch('scripts.seed_initial_data.create_admin_user', return_value=mock_user), \
         patch('scripts.seed_initial_data.SessionLocal') as mock_session_local:
        
        # Configure mock session
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        from scripts.seed_initial_data import seed_all
        result = seed_all(config_path)
        
        # Assert successful completion
        assert result is not None
        assert "winery" in result
        assert "admin_user" in result
        assert result["winery"] == mock_winery
        assert result["admin_user"] == mock_user
        mock_session.close.assert_called_once()


def test_seed_all_idempotent():
    """Test that running seed multiple times is safe (idempotency)."""
    # Arrange
    config_path = "test_config.yaml"
    
    mock_config = {
        "winery": {"code": "EXISTING", "name": "Existing Winery"},
        "admin_user": {"email": "existing@test.com", "username": "admin", "password": "admin"}
    }
    
    # Both already exist
    mock_winery = Mock(id=1, code="EXISTING")
    mock_user = Mock(id=1, email="existing@test.com")
    
    # Act & Assert - Run twice, should not error
    with patch('scripts.seed_initial_data.load_seed_config', return_value=mock_config), \
         patch('scripts.seed_initial_data.create_initial_winery', return_value=mock_winery), \
         patch('scripts.seed_initial_data.create_admin_user', return_value=mock_user), \
         patch('scripts.seed_initial_data.SessionLocal') as mock_session_local:
        
        # Configure mock session
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        from scripts.seed_initial_data import seed_all
        
        # First run
        result1 = seed_all(config_path)
        assert result1 is not None
        
        # Reset mocks
        mock_session_local.reset_mock()
        mock_session.reset_mock()
        
        # Second run - should not error
        result2 = seed_all(config_path)
        assert result2 is not None
        
        # Both return same entities (idempotent)
        assert result1["winery"].id == result2["winery"].id
        assert result1["admin_user"].id == result2["admin_user"].id
