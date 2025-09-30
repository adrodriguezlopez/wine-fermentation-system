#!/usr/bin/env python3
"""Test database connection from within Docker container using internal networking."""

import sys
import os
import asyncio

# Add paths
sys.path.insert(0, '/app/src')  # Docker internal path
sys.path.insert(0, '/app')      # Docker app root

# Add fallback for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'modules', 'fermentation', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from shared.infra.database import DatabaseConfig
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Available paths:")
    for path in sys.path:
        print(f"  - {path}")
    sys.exit(1)


async def docker_internal_test():
    """Test database connection using Docker internal networking."""
    print("🐳 Docker Internal Networking Test")
    print("=" * 50)
    
    # Check environment variables
    db_url = os.getenv('DATABASE_URL', 'NOT_SET')
    print(f"📋 DATABASE_URL: {db_url}")
    
    if db_url == 'NOT_SET':
        print("⚠️  DATABASE_URL not set, using fallback configuration")
        # Set the internal Docker URL manually for testing
        os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@db:5432/wine_fermentation'
        print(f"📋 Using fallback: {os.environ['DATABASE_URL']}")
    
    # Test configuration
    try:
        config = DatabaseConfig()
        print(f"✅ Database URL: {config.url}")
        print(f"✅ Pool size: {config.pool_size}")
        print(f"✅ Max overflow: {config.max_overflow}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test engine creation
    try:
        engine = config.create_engine()
        print(f"✅ Engine created: {type(engine).__name__}")
    except Exception as e:
        print(f"❌ Engine creation failed: {e}")
        return False
    
    # Test connection with Docker internal networking
    print("\n🔗 Testing Docker Internal Connection...")
    try:
        async def test_connection():
            async with engine.connect() as conn:
                print("✅ Connection established to PostgreSQL via Docker network")
                
                # Test basic query
                result = await conn.execute("SELECT 1 as test, 'Docker networking works!' as message")
                row = result.fetchone()
                print(f"✅ Test query result: {row.test}")
                print(f"✅ Message: {row.message}")
                
                # Test database info
                result2 = await conn.execute("SELECT current_database(), current_user, version()")
                db_info = result2.fetchone()
                print(f"✅ Database: {db_info[0]}")
                print(f"✅ User: {db_info[1]}")
                print(f"✅ PostgreSQL version: {db_info[2][:50]}...")
                
                # Test application-specific query
                result3 = await conn.execute("SELECT NOW() as server_time")
                time_info = result3.fetchone()
                print(f"✅ Server time: {time_info.server_time}")
        
        await asyncio.wait_for(test_connection(), timeout=15.0)
        
    except asyncio.TimeoutError:
        print("❌ Connection timed out after 15 seconds")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False
    finally:
        await engine.dispose()
        print("✅ Engine disposed")
    
    print("\n🎉 Docker internal networking test successful!")
    return True


if __name__ == "__main__":
    print("🐳 Running database test with Docker internal networking...")
    print(f"📂 Python version: {sys.version}")
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"📂 Available environment variables:")
    for key in ['DATABASE_URL', 'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_NAME']:
        value = os.getenv(key, 'NOT_SET')
        print(f"    {key}: {value}")
    
    try:
        success = asyncio.run(docker_internal_test())
        if success:
            print("\n✅ SUCCESS: Phase 1, Step 1.1 is working with Docker internal networking!")
        else:
            print("\n❌ FAILURE: Connection issues detected")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)