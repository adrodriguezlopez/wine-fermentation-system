"""
Seed Initial Data Bootstrap Script

ADR-018: Seed Script for Initial Data Bootstrap

This script creates minimal required entities:
- 1 Winery (multi-tenancy root)
- 1 Admin User (system access)

Features:
- Idempotent: Safe to run multiple times
- YAML configuration: scripts/seed_config.yaml
- Check-then-insert pattern: Skip if exists

Usage:
    python -m scripts.seed_initial_data
    python -m scripts.seed_initial_data --config custom_config.yaml

WARNING: Default credentials are "admin"/"admin" - CHANGE IN PRODUCTION!
"""
import asyncio
import sys
import argparse
from pathlib import Path
from typing import Dict, Any
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.modules.winery.src.domain.entities.winery import Winery
from src.shared.auth.domain.entities.user import User
from src.shared.auth.domain.enums.user_role import UserRole
from src.shared.infra.database import DatabaseConfig, DatabaseSession
from src.shared.wine_fermentator_logging import get_logger
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

logger = get_logger(__name__)


# =============================================================================
# Configuration Loading
# =============================================================================

def load_seed_config(config_path: str) -> Dict[str, Any]:
    """
    Load seed configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Dict with winery and admin_user configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config is invalid YAML
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.error("Configuration file not found", config_path=config_path)
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    logger.info("Loading seed configuration", config_path=config_path)
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required sections
    if 'winery' not in config:
        raise ValueError("Missing 'winery' section in config")
    if 'admin_user' not in config:
        raise ValueError("Missing 'admin_user' section in config")
    
    logger.info("Configuration loaded successfully")
    return config


# =============================================================================
# Winery Creation
# =============================================================================

async def create_initial_winery(config: Dict[str, Any], session: AsyncSession) -> Winery:
    """
    Create initial winery if it doesn't exist (idempotent).
    
    Args:
        config: Full configuration dict with 'winery' section
        session: Async database session
        
    Returns:
        Winery entity (existing or newly created)
    """
    winery_config = config['winery']
    winery_code = winery_config['code']
    
    logger.info("Checking if winery exists", winery_code=winery_code)
    
    # Check if winery already exists (idempotent)
    result = await session.execute(select(Winery).filter_by(code=winery_code))
    existing_winery = result.scalars().first()
    if existing_winery:
        logger.info(
            "Winery already exists - skipping creation",
            winery_id=existing_winery.id,
            winery_code=winery_code
        )
        return existing_winery
    
    # Create new winery
    logger.info("Creating new winery", winery_code=winery_code)
    
    winery = Winery(
        code=winery_config['code'],
        name=winery_config['name'],
        location=winery_config.get('location'),
        notes=winery_config.get('notes')
    )
    
    session.add(winery)
    await session.commit()
    await session.refresh(winery)
    
    logger.info(
        "Winery created successfully",
        winery_id=winery.id,
        winery_code=winery.code,
        winery_name=winery.name
    )
    
    return winery


# =============================================================================
# User Creation
# =============================================================================

async def create_admin_user(config: Dict[str, Any], winery_id: int, session: AsyncSession) -> User:
    """
    Create admin user if doesn't exist (idempotent).
    
    Args:
        config: Full configuration dict with 'admin_user' section
        winery_id: ID of winery to associate user with
        session: Async database session
        
    Returns:
        User entity (existing or newly created)
    """
    user_config = config['admin_user']
    email = user_config['email']
    
    logger.info("Checking if admin user exists", email=email)
    
    # Check if user already exists (idempotent)
    result = await session.execute(select(User).filter_by(email=email))
    existing_user = result.scalars().first()
    if existing_user:
        logger.info(
            "Admin user already exists - skipping creation",
            user_id=existing_user.id,
            email=email
        )
        return existing_user
    
    # Create new admin user
    logger.info("Creating new admin user", email=email)
    
    # Hash password
    password_hash = hash_password(user_config['password'])
    
    user = User(
        username=user_config['username'],
        email=email,
        password_hash=password_hash,
        full_name=user_config.get('full_name', 'System Administrator'),
        winery_id=winery_id,
        role=UserRole.ADMIN.value,  # Use enum value
        is_active=True
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    logger.info(
        "Admin user created successfully",
        user_id=user.id,
        email=user.email,
        role=user.role
    )
    
    return user


# =============================================================================
# Main Orchestration
# =============================================================================

async def seed_all(config_path: str = "scripts/seed_config.yaml") -> Dict[str, Any]:
    """
    Main entry point for seeding initial data.
    
    Creates minimal required entities:
    - 1 Winery (multi-tenancy root)
    - 1 Admin User (system access)
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Dict with created entities: {'winery': Winery, 'admin_user': User}
    """
    logger.info("=" * 80)
    logger.info("Starting seed script - ADR-018")
    logger.info("=" * 80)
    
    # Load configuration
    config = load_seed_config(config_path)
    
    # Print security warning
    if config['admin_user']['password'] == 'admin':
        logger.warning("")
        logger.warning("⚠️  SECURITY WARNING ⚠️")
        logger.warning("Default password 'admin' detected!")
        logger.warning("CHANGE THIS PASSWORD IMMEDIATELY in production!")
        logger.warning("")
    
    # Build async session using shared DatabaseConfig + DatabaseSession
    db_config = DatabaseConfig()
    db_session = DatabaseSession(db_config)
    
    try:
        async with db_session.get_session() as session:
            # Create winery
            winery = await create_initial_winery(config, session)
            
            # Create admin user
            admin_user = await create_admin_user(config, winery.id, session)
        
        logger.info("=" * 80)
        logger.info("Seed script completed successfully!")
        logger.info(f"Winery ID: {winery.id}, Code: {winery.code}")
        logger.info(f"Admin User ID: {admin_user.id}, Email: {admin_user.email}")
        logger.info("=" * 80)
        
        return {
            'winery': winery,
            'admin_user': admin_user
        }
        
    except Exception as e:
        logger.error("Seed script failed", error=str(e), error_type=type(e).__name__)
        raise
    finally:
        await db_session.close()


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Seed initial data for wine fermentation system (ADR-018)"
    )
    parser.add_argument(
        '--config',
        default='scripts/seed_config.yaml',
        help='Path to seed configuration YAML file (default: scripts/seed_config.yaml)'
    )
    
    args = parser.parse_args()
    
    try:
        result = asyncio.run(seed_all(args.config))
        print(f"\n✅ Success! Created winery '{result['winery'].name}' and admin user '{result['admin_user'].email}'")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
