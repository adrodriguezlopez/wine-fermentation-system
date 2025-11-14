import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.engine import URL


class DatabaseConfig:
    """
    Database configuration management implementing IDatabaseConfig interface.
    
    Provides async engine creation and configuration for repository infrastructure.
    """
    def __init__(self):
        self.url = self._build_database_url()
        self.echo = os.getenv("DB_ECHO", "False").lower() == "true"
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self._engine = None

    @property
    def async_engine(self) -> AsyncEngine:
        """
        Get the async SQLAlchemy engine.
        
        Returns:
            AsyncEngine: The configured async database engine
            
        Raises:
            DatabaseConfigError: If engine is not properly configured
        """
        if self._engine is None:
            self._engine = self.create_engine()
        return self._engine

    def _is_running_in_docker(self) -> bool:
        """Detect if we're running inside a Docker container."""
        try:
            # Check for Docker-specific files
            return (
                os.path.exists('/.dockerenv') or 
                os.path.exists('/proc/1/cgroup') and 'docker' in open('/proc/1/cgroup').read()
            )
        except:
            return False

    def _build_database_url(self) -> str:
        # Try environment variable first
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            # Convert postgres:// to postgresql+asyncpg:// for async support
            if env_url.startswith("postgres://"):
                env_url = env_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif env_url.startswith("postgresql://"):
                env_url = env_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
            # Smart host resolution for development
            if not self._is_running_in_docker():
                # Development mode: use localhost for host connections
                if "@db:" in env_url:
                    env_url = env_url.replace("@db:", "@localhost:")
                    print(f"🔧 Development mode: Using localhost instead of db service")
                elif "localhost" in env_url:
                    # For Windows Docker Desktop, try 127.0.0.1 for better compatibility
                    env_url = env_url.replace("localhost", "127.0.0.1")
            
            return env_url
        
        # Fallback to individual components
        host = os.getenv("DB_HOST", "localhost")
        
        # Smart host resolution for development vs Docker
        if not self._is_running_in_docker():
            # Development mode: use localhost/127.0.0.1
            if host in ["db", "localhost"]:
                host = "127.0.0.1"
                print(f"🔧 Development mode: Using {host} for database connection")
        
        return URL.create(
            drivername="postgresql+asyncpg",
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            host=host,
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "wine_fermentation"),
        ).render_as_string(hide_password=False)
    
    def create_engine(self) -> AsyncEngine:
        # Build engine kwargs based on database type
        engine_kwargs = {"echo": self.echo}
        
        # SQLite doesn't support pool_size/max_overflow parameters
        if not self.url.startswith("sqlite"):
            engine_kwargs["pool_size"] = self.pool_size
            engine_kwargs["max_overflow"] = self.max_overflow
            # PostgreSQL-specific connection parameters
            engine_kwargs["connect_args"] = {
                "server_settings": {
                    "application_name": "wine_fermentation",
                },
                "timeout": 30,
                "command_timeout": 30,
            }
        
        return create_async_engine(self.url, **engine_kwargs)