# Test Organization - Functional Structure

## Overview
Tests are organized by **functionality** rather than by technical layers. This approach makes it easier to understand what aspects of the system are being tested and allows for better test maintenance.

## Structure

```
tests/
└── unit/                          # All unit tests
    ├── conftest.py                # Shared fixtures and configuration
    ├── validation/                # Data validation functionality
    │   ├── test_validation_service.py           # ValidationService implementation tests
    │   └── test_validation_service_interface.py # IValidationService contract tests
    ├── sample_management/         # Sample collection and retrieval
    │   └── test_sample_service_interface.py     # ISampleService contract tests
    ├── fermentation_lifecycle/    # Fermentation process management
    │   └── test_fermentation_service_interface.py # IFermentationService contract tests
    ├── analysis_engine/          # Data analysis and predictions
    │   └── test_analysis_engine_client_interface.py # IAnalysisEngineClient contract tests
    └── repositories/             # Data persistence contracts
        ├── test_fermentation_repository_interface.py # IFermentationRepository tests
        └── test_sample_repository_interface.py       # ISampleRepository tests
```

## Running Tests

### By Functionality
```bash
# Test all validation functionality
poetry run pytest tests/unit/validation/ -v

# Test sample management
poetry run pytest tests/unit/sample_management/ -v

# Test fermentation lifecycle
poetry run pytest tests/unit/fermentation_lifecycle/ -v

# Test analysis engine integration
poetry run pytest tests/unit/analysis_engine/ -v

# Test repository contracts
poetry run pytest tests/unit/repositories/ -v
```

### All Unit Tests
```bash
poetry run pytest tests/unit/ -v
```

### With Coverage
```bash
poetry run pytest --cov=src tests/unit/
```

## Test Types

**Interface/Contract Tests**: Verify that interfaces define the expected methods and signatures. These are important for maintaining API contracts.

**Implementation Tests**: Test concrete class behavior. Currently only `ValidationService` has implementation tests.

## Future Integration Tests
When you have multiple components working together, create:
```
tests/
├── unit/           # Current structure
└── integration/    # Future integration tests
    ├── end_to_end_fermentation_workflow/
    ├── repository_service_integration/
    └── external_analysis_engine_integration/
```

## Migration Complete
✅ Old structure (`tests/service_component/`) can be removed
✅ All tests moved to functional organization
✅ Import paths updated for new structure
✅ Shared fixtures available in `tests/unit/conftest.py`

## ⚠️ Important: Running All Tests

**Current Status**: The module has **182 tests total** (173 unit + 9 integration).

### ✅ Recommended: Run Separately

Due to SQLAlchemy mapper registry conflicts, unit and integration tests **must** be run in separate pytest sessions:

```powershell
# Run unit tests (173 tests)
poetry run pytest tests/unit/

# Run integration tests (9 tests)
poetry run pytest tests/integration/

# Run both sequentially (recommended)
poetry run pytest tests/unit/ --tb=no -q; poetry run pytest tests/integration/ --tb=no -q
```

### ❌ Will Fail: Running Together

```powershell
# This will fail with SQLAlchemy mapper errors
poetry run pytest tests/
```

**Why**: When pytest collects both suites, the global SQLAlchemy `mapper_registry` gets configured twice. The `extend_existing=True` allows table re-registration, but causes mapper conflicts with inherited entities (`SugarSample`, `DensitySample`, etc inherit from `BaseSample`).

**Error**: `"Mapper[SugarSample(samples)] could not assemble any primary key columns for mapped table 'samples'"`

### Solution

Keep test execution separate. Integration tests are isolated in `tests/integration/` and work perfectly when run alone or after unit tests in a separate process.

