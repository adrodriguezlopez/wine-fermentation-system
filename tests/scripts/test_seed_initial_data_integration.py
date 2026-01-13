"""
Integration test for seed_initial_data.py script.

Tests the complete seed operation with a real (test) database.
Verifies idempotency and data integrity.

ADR-018: Seed Script for Initial Data Bootstrap
"""
import sys
import tempfile
import os
from pathlib import Path
import pytest
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.modules.winery.src.domain.entities.winery import Winery
from src.shared.auth.domain.entities.user import User
from src.shared.auth.domain.enums.user_role import UserRole
from src.shared.infra.orm.base_entity import Base


@pytest.fixture
def test_config_file():
    """Create a temporary test configuration file."""
    test_config = {
        "winery": {
            "code": "TEST-INTEGRATION",
            "name": "Integration Test Winery",
            "location": "Test Location",
            "notes": "Created by integration test"
        },
        "admin_user": {
            "username": "testadmin",
            "email": "testadmin@integration.test",
            "password": "testpass123",
            "full_name": "Integration Test Admin"
        }
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_config, f)
        config_path = f.name
    
    yield config_path
    
    # Cleanup
    os.unlink(config_path)


@pytest.fixture
def test_db():
    """Create a test database in memory."""
    # Use in-memory SQLite for testing
    engine = create_engine('sqlite:///:memory:', echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield engine, SessionLocal
    
    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_seed_all_integration_creates_entities(test_config_file, test_db):
    """Integration test: Verify seed creates winery and admin user."""
    engine, SessionLocal = test_db
    
    # Patch the session in seed script to use our test DB
    import scripts.seed_initial_data as seed_module
    original_session_local = seed_module.SessionLocal
    seed_module.SessionLocal = SessionLocal
    
    try:
        # Act
        result = seed_module.seed_all(test_config_file)
        
        # Assert: Check return value
        assert result is not None
        assert "winery" in result
        assert "admin_user" in result
        
        # Assert: Check winery
        winery = result["winery"]
        assert winery.id is not None
        assert winery.code == "TEST-INTEGRATION"
        assert winery.name == "Integration Test Winery"
        assert winery.location == "Test Location"
        
        # Assert: Check admin user
        admin_user = result["admin_user"]
        assert admin_user.id is not None
        assert admin_user.username == "testadmin"
        assert admin_user.email == "testadmin@integration.test"
        assert admin_user.winery_id == winery.id
        assert admin_user.role == UserRole.ADMIN.value
        assert admin_user.is_active is True
        assert admin_user.password_hash is not None
        assert admin_user.password_hash != "testpass123"  # Should be hashed
        
        # Assert: Verify data persisted to database
        session = SessionLocal()
        try:
            db_winery = session.query(Winery).filter_by(code="TEST-INTEGRATION").first()
            assert db_winery is not None
            assert db_winery.name == "Integration Test Winery"
            
            db_user = session.query(User).filter_by(email="testadmin@integration.test").first()
            assert db_user is not None
            assert db_user.username == "testadmin"
            assert db_user.winery_id == db_winery.id
        finally:
            session.close()
            
    finally:
        # Restore original session
        seed_module.SessionLocal = original_session_local


def test_seed_all_integration_idempotent(test_config_file, test_db):
    """Integration test: Verify seed is idempotent (can run multiple times safely)."""
    engine, SessionLocal = test_db
    
    # Patch the session in seed script to use our test DB
    import scripts.seed_initial_data as seed_module
    original_session_local = seed_module.SessionLocal
    seed_module.SessionLocal = SessionLocal
    
    try:
        # Act: Run seed twice
        result1 = seed_module.seed_all(test_config_file)
        result2 = seed_module.seed_all(test_config_file)
        
        # Assert: Both runs successful
        assert result1 is not None
        assert result2 is not None
        
        # Assert: Same IDs returned (entities not duplicated)
        assert result1["winery"].id == result2["winery"].id
        assert result1["admin_user"].id == result2["admin_user"].id
        
        # Assert: Only one winery and one user in database
        session = SessionLocal()
        try:
            winery_count = session.query(Winery).count()
            user_count = session.query(User).count()
            
            assert winery_count == 1, f"Expected 1 winery, found {winery_count}"
            assert user_count == 1, f"Expected 1 user, found {user_count}"
        finally:
            session.close()
            
    finally:
        # Restore original session
        seed_module.SessionLocal = original_session_local


def test_seed_all_integration_password_hashing(test_config_file, test_db):
    """Integration test: Verify password is properly hashed."""
    engine, SessionLocal = test_db
    
    # Patch the session in seed script to use our test DB
    import scripts.seed_initial_data as seed_module
    original_session_local = seed_module.SessionLocal
    seed_module.SessionLocal = SessionLocal
    
    try:
        # Act
        result = seed_module.seed_all(test_config_file)
        admin_user = result["admin_user"]
        
        # Assert: Password is hashed (bcrypt hash starts with $2b$)
        assert admin_user.password_hash.startswith('$2b$'), \
            "Password should be hashed with bcrypt"
        
        # Assert: Verify hash using passlib
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Verify the hash matches the original password
        is_valid = pwd_context.verify("testpass123", admin_user.password_hash)
        assert is_valid, "Password hash should verify against original password"
        
        # Verify wrong password doesn't match
        is_invalid = pwd_context.verify("wrongpassword", admin_user.password_hash)
        assert not is_invalid, "Wrong password should not verify"
        
    finally:
        # Restore original session
        seed_module.SessionLocal = original_session_local
