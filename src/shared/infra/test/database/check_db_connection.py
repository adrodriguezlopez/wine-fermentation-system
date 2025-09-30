#!/usr/bin/env python3
"""
Database Connection Test

Simple test to verify database connectivity for development.
Tests both development (host) and Docker (container) environments.

Usage:
  # Development mode (host to Docker PostgreSQL)
  python src/shared/infra/test/database/check_db_connection.py

  # Docker mode (container to container)
  docker-compose run --rm fermentation python src/shared/infra/test/database/check_db_connection.py
"""

import sys
import os
import asyncio

# Add project root to Python path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.shared.infra.database import DatabaseConfig
    from sqlalchemy import text
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root and dependencies are installed")
    sys.exit(1)


async def check_database_connection():
    """Check database connectivity and basic functionality."""
    print("🔍 Database Connection Check")
    print("=" * 40)
    
    # Create configuration
    try:
        config = DatabaseConfig()
        print(f"✅ Database URL: {config.url}")
        print(f"✅ Pool size: {config.pool_size}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test connection
    try:
        engine = config.create_engine()
        print(f"✅ Engine created successfully")
        
        async with engine.connect() as conn:
            # Basic connectivity test
            result = await conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            print(f"✅ Connection successful: test query returned {test_value}")
            
            # Database info
            result = await conn.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            print(f"✅ Database: {db_info[0]}, User: {db_info[1]}")
            
            # PostgreSQL version
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL: {version.split(',')[0]}")
            
        await engine.dispose()
        print("✅ Connection closed successfully")
        print("\n🎉 Database connection is working!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        
        # Helpful troubleshooting info
        print("\n🔧 Troubleshooting:")
        print("  • Make sure PostgreSQL Docker container is running: docker-compose up db -d")
        print("  • Check if DATABASE_URL environment variable is set correctly")
        print("  • For development: use port 5433 (localhost:5433)")
        print("  • For Docker: use port 5432 (db:5432)")
        
        return False


def print_environment_info():
    """Print relevant environment information."""
    print("📋 Environment Information:")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Working directory: {os.getcwd()}")
    
    # Check key environment variables
    env_vars = ['DATABASE_URL', 'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_NAME']
    for var in env_vars:
        value = os.getenv(var, 'NOT_SET')
        if 'password' not in var.lower():
            print(f"  {var}: {value}")
        else:
            print(f"  {var}: {'***' if value != 'NOT_SET' else 'NOT_SET'}")
    
    # Detect environment
    is_docker = os.path.exists('/.dockerenv')
    print(f"  Environment: {'Docker Container' if is_docker else 'Host Machine'}")
    print()


if __name__ == "__main__":
    print_environment_info()
    
    try:
        success = asyncio.run(check_database_connection())
        exit_code = 0 if success else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)