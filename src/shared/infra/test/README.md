# Shared Infrastructure Tests

This directory contains test utilities for the shared infrastructure components.

## Database Tests

### `check_db_connection.py`

A standalone script to verify database connectivity for both development and production environments.

**Usage:**

```bash
# From project root - Development mode (host to Docker PostgreSQL)
python src/shared/infra/test/database/check_db_connection.py

# Using Poetry environment (recommended)
cd src/modules/fermentation
poetry run python ../../../../src/shared/infra/test/database/check_db_connection.py

# Docker mode (container to container)
docker-compose run --rm fermentation python src/shared/infra/test/database/check_db_connection.py
```

**Features:**
- Tests both development (localhost:5433) and Docker (db:5432) connectivity
- Displays environment information and configuration
- Validates basic database operations
- Provides troubleshooting guidance on connection failures

**Environment Detection:**
- Automatically detects if running in Docker container or host machine
- Uses appropriate connection settings based on environment
- Supports both `DATABASE_URL` and individual environment variables