# Module Setup Guide

**ADR-028**: Standard procedure for setting up independent module environments

## Overview

All modules in the Wine Fermentation System follow a standardized structure with independent Poetry-managed virtual environments. This enables:
- Independent testing per module
- Clear dependency boundaries
- Microservices-ready architecture
- Simplified CI/CD (test only changed modules)

## Standard Module Structure

```
module_name/
├── pyproject.toml              # Poetry configuration
├── poetry.lock                 # Locked dependency versions
├── .venv/                      # Virtual environment (gitignored)
├── README.md                   # Module documentation
├── tests/
│   ├── conftest.py             # Test configuration (adds workspace root to sys.path)
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests (optional)
└── src/
    ├── domain/                 # Entities, enums, DTOs
    ├── repository_component/   # Data access layer
    ├── service_component/      # Business logic (optional)
    └── api/                    # FastAPI routers (optional)
```

## Quick Start

### Running Tests

```powershell
# Navigate to module directory
cd src/modules/fermentation

# Install dependencies (first time only)
poetry install

# Run all tests
poetry run pytest

# Run unit tests only
poetry run pytest tests/unit/ -v

# Run with coverage
poetry run pytest --cov=src --cov-report=html
```

### Activating Virtual Environment

```powershell
# Option 1: Use poetry shell (recommended)
cd src/modules/fermentation
poetry shell
pytest  # Now runs in module's virtual environment

# Option 2: Use poetry run prefix
cd src/modules/fermentation
poetry run pytest
poetry run python -c "import structlog; print(structlog.__version__)"
```

### Adding Dependencies

```powershell
cd src/modules/fermentation

# Add runtime dependency
poetry add sqlalchemy

# Add dev dependency
poetry add --group dev pytest-mock

# Update lock file (after manual pyproject.toml changes)
poetry lock

# Install updated dependencies
poetry install
```

## Module-Specific Configurations

### Fermentation Module
- **Location**: `src/modules/fermentation/`
- **Tests**: 223 unit tests
- **Dependencies**: FastAPI, SQLAlchemy, structlog, colorama
- **API**: Yes (FastAPI application in `src/api/`)
- **Command**: `cd src/modules/fermentation; poetry run pytest`

### Winery Module
- **Location**: `src/modules/winery/`
- **Tests**: 22 unit tests
- **Dependencies**: SQLAlchemy, structlog, colorama
- **API**: No (repository-only module)
- **Command**: `cd src/modules/winery; poetry run pytest tests/unit/`

### Fruit Origin Module
- **Location**: `src/modules/fruit_origin/`
- **Tests**: 72 unit tests
- **Dependencies**: SQLAlchemy, structlog, colorama
- **API**: No (repository-only module)
- **Command**: `cd src/modules/fruit_origin; poetry run pytest tests/unit/`

## Import Path Resolution

All modules use a `tests/conftest.py` that adds the workspace root to `sys.path`:

```python
# tests/conftest.py
import sys
from pathlib import Path

# Add workspace root to Python path
# tests/conftest.py -> tests -> module -> modules -> src -> wine-fermentation-system
workspace_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))
```

This enables imports like:
- `from src.shared.wine_fermentator_logging import get_logger`
- `from src.modules.fermentation.src.domain.entities import Fermentation`
- `from src.shared.testing.unit import MockSessionManagerBuilder`

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src.shared'`

**Solution**: Ensure `tests/conftest.py` exists and adds workspace root to sys.path:
```python
workspace_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))
```

### Wrong Virtual Environment

**Problem**: Tests pass from workspace root but fail from module directory

**Solution**: Make sure you're using the module's Poetry environment:
```powershell
cd src/modules/winery
poetry install  # Ensure dependencies installed
poetry run pytest  # Use module's .venv
```

### Dependency Not Found

**Problem**: `ImportError: cannot import name 'get_logger' from 'src.shared.wine_fermentator_logging'`

**Solution**: Install missing dependency in the module:
```powershell
cd src/modules/winery
poetry add structlog colorama
poetry install
```

### Poetry Lock File Issues

**Problem**: `poetry install` fails with "lock file is not consistent"

**Solution**: Regenerate lock file:
```powershell
cd src/modules/winery
poetry lock
poetry install
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Module

on: [push, pull_request]

jobs:
  test-fermentation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        run: |
          cd src/modules/fermentation
          poetry install
      
      - name: Run tests
        run: |
          cd src/modules/fermentation
          poetry run pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./src/modules/fermentation/coverage.xml
```

## Standard Dependencies

All modules should include:

### Runtime Dependencies
- `python = "^3.9"`
- `sqlalchemy = "^2.0.20"` (for database access)
- `structlog = "^25.5.0"` (ADR-027 logging)
- `colorama = "^0.4.6"` (ADR-027 console colors)
- `pydantic = "^2.3.0"` (for DTOs)
- `asyncpg = "^0.28.0"` (async PostgreSQL driver)
- `psycopg2-binary = "^2.9.7"` (sync PostgreSQL driver)

### Dev Dependencies
- `pytest = "^7.4.0"`
- `pytest-asyncio = "^0.21.1"`
- `pytest-cov = "^4.1.0"`
- `black = "^23.7.0"`
- `mypy = "^1.5.0"`
- `flake8 = "^6.1.0"`

### API Modules (Fermentation only)
- `fastapi = "^0.103.0"`
- `uvicorn = {extras = ["standard"], version = "^0.23.2"}`

## Best Practices

1. **Always run tests from module directory**: `cd src/modules/winery; poetry run pytest`
2. **Keep dependencies explicit**: Don't rely on parent environments
3. **Use Poetry for all dependency management**: Never use `pip install` directly
4. **Lock dependencies**: Always commit `poetry.lock` to version control
5. **Document module-specific setup**: Update module README with any special requirements
6. **Test independently**: Each module's tests should pass without other modules installed
7. **Keep shared code minimal**: Only put truly shared utilities in `src/shared/`

## Creating a New Module

1. Create module directory structure:
```powershell
mkdir src/modules/new_module
mkdir src/modules/new_module/src
mkdir src/modules/new_module/tests
mkdir src/modules/new_module/tests/unit
```

2. Create `pyproject.toml` (copy from fermentation/winery as template)

3. Create `tests/conftest.py`:
```python
import sys
from pathlib import Path
workspace_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))
```

4. Install dependencies:
```powershell
cd src/modules/new_module
poetry install
```

5. Verify setup:
```powershell
poetry run pytest  # Should pass (even with 0 tests)
poetry run python -c "import structlog"  # Should not error
```

## Related Documentation

- **ADR-027**: Structured Logging & Observability
- **ADR-028**: Module Dependency Management Standardization
- **ADR-011**: Integration Test Infrastructure
- **ADR-002**: Repository Architecture

## Version History

- **Dec 22, 2025**: Created as part of ADR-028 Phase 3
- **Status**: All 3 modules standardized (fermentation, winery, fruit_origin)
- **Test Coverage**: 317/317 unit tests passing across all modules
