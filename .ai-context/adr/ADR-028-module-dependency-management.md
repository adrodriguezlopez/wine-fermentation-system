# ADR-028: Module Dependency Management Standardization

**Status:**  **IMPLEMENTED** (All 4 Phases Complete)  
**Date:** December 22-23, 2025  
**Authors:** Development Team  
**Related ADRs:** 
- ADR-011 (Integration Tests)
- ADR-027 (Structured Logging)
- ADR-002 (Repository Architecture)
- ADR-006 (API Layer Design)

> ** Context Files:**
> - [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md) - Module design principles
> - [Module Setup Guide](../module-setup-guide.md) - Developer reference

---

## Context

The Wine Fermentation System had **inconsistent dependency management** across modules:

-  **Fermentation Module**: Has `pyproject.toml` + `poetry.lock`  Self-contained with own virtual environment
-  **Winery Module**: No `pyproject.toml`  Depends on fermentation's environment or workspace-level dependencies
-  **Fruit Origin Module**: Has `pyproject.toml` + `poetry.lock` but **outdated/incomplete**
-  **Shared Module**: Has `pyproject.toml` but missing auth/testing dependencies

This inconsistency caused:
1. **Integration test failures** when running from different contexts
2. **Import path confusion** (`shared.testing` vs `src.shared.testing`)
3. **Dependency version conflicts** between modules
4. **Difficult local development** (which environment to use?)
5. **CI/CD complexity** (multiple environment configurations)

**Discovered During:** ADR-027 Phase 4 - Testing API layer integration revealed winery/fruit_origin/shared cant run tests independently.

**Real-world impact:**
```
Developer: "Run the winery tests"
CI: ImportError: No module named structlog
Developer: "But it works in fermentation's venv!"
```

---

## Decision

1. **Standardize all modules with independent Poetry environments**
   - Each module has its own `pyproject.toml` + `poetry.lock`
   - Each module has its own `.venv/` virtual environment
   - No shared/workspace-level dependencies

2. **Use conftest.py pattern for import path resolution**
   - Each module's `tests/conftest.py` adds workspace root to `sys.path`
   - Enables `from src.shared.X` and `from src.modules.Y` imports
   - Avoids circular dependency issues from installing shared as editable package

3. **Standard module structure:**
   ```
   module_name/
    pyproject.toml              # Poetry config with all dependencies
    poetry.lock                 # Locked versions (committed to git)
    .venv/                      # Virtual environment (gitignored)
    src/                        # Module source code
    tests/
        conftest.py             # Adds workspace root to sys.path
        unit/                   # Unit tests
        integration/            # Integration tests
   ```

4. **Developer workflow:**
   ```bash
   cd src/modules/<module_name>
   poetry install
   poetry run pytest tests/unit/
   ```

5. **For shared module: Use package-relative imports**
   - Inside shared: `from testing.integration import X` (not `from shared.testing.integration`)
   - Outside shared: `from src.shared.testing.integration import X`

---

## Implementation Notes

### File Structure
```
src/modules/fermentation/
 pyproject.toml               Complete
 poetry.lock                  223 tests passing
 .venv/

src/modules/winery/
 pyproject.toml               Created (Phase 1)
 poetry.lock                  22 tests passing
 .venv/
 tests/conftest.py            Workspace path resolution

src/modules/fruit_origin/
 pyproject.toml               Updated (Phase 2)
 poetry.lock                  72 tests passing
 .venv/
 tests/conftest.py            Workspace path resolution

src/shared/
 pyproject.toml               Enhanced (Phase 4)
 poetry.lock                  215 tests passing
 .venv/
 auth/tests/conftest.py       Path resolution
 testing/tests/conftest.py    Path resolution
 infra/test/conftest.py       Path resolution
```

### Component Responsibilities

**pyproject.toml (each module):**
- Define all direct dependencies (sqlalchemy, structlog, fastapi, etc.)
- Configure pytest with asyncio_mode, testpaths, markers
- Expose packages for import

**conftest.py (tests/ directory):**
```python
import sys
from pathlib import Path

# Add workspace root to Python path (5 levels up from conftest.py)
workspace_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))
```

**Import Pattern:**
- From winery tests: `from src.shared.wine_fermentator_logging import get_logger` 
- From shared tests: `from testing.integration.session_manager import TestSessionManager` 

---

## Architectural Considerations

> **Default:** This project follows [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)

### conftest.py vs Editable Shared Package

**Decision:** Use conftest.py approach (not editable package)
- **Trade-off:** Each module needs conftest.py (5 lines duplication)
- **Justification:** Editable shared package causes circular import issues in shared's internal tests
- **Alternative rejected:** `poetry add -e ../../shared`  Breaks shared module's own tests

### Module Independence vs Code Sharing

**Decision:** Modules remain independent but share `src/shared/` code via imports
- **Pattern:** Shared code accessed via absolute imports (`from src.shared.X`)
- **No duplication:** Shared code exists once in `src/shared/`
- **Microservices ready:** Each module can be deployed separately

---

## Consequences

### Benefits 

1. **Module Independence** - Each module tests/runs independently
2. **Clear Dependencies** - Explicit pyproject.toml per module
3. **ADR-027 Logging Support** - All modules have structlog/colorama installed
4. **Developer Experience** - Simple workflow: `cd module  poetry install  poetry run pytest`
5. **Microservices Ready** - Each module can be deployed as separate service
6. **CI/CD Simplification** - Test only changed modules, parallel execution

### Trade-offs 

1. **Multiple Environments** - Need to manage 4 virtual environments (~300MB each)
2. **Dependency Synchronization** - Need to keep SQLAlchemy/FastAPI versions aligned across modules
3. **Initial Migration Effort** - 6 hours to standardize all modules

### Limitations 

1. **Not a monorepo tool** - This is lightweight approach, not Nx/Turborepo
2. **Manual version sync** - No automatic dependency version alignment
3. **Disk space** - ~1.2GB for all 4 module environments

---

## TDD Plan

**Phase 1: Winery Module (22 tests)**
- Create pyproject.toml  `poetry install` succeeds
- Create conftest.py  Imports work
- Run tests  22/22 passing independently

**Phase 2: Fruit Origin Module (72 tests)**
- Update pyproject.toml  Fix TOML syntax errors
- Update conftest.py  Match winery pattern
- Run tests  72/72 passing independently

**Phase 3: Documentation (Manual verification)**
- Create module-setup-guide.md  Covers all 3 modules
- Verify workflows  All commands work as documented

**Phase 4: Shared Module (215 tests)**
- Enhance pyproject.toml  Add auth/testing dependencies
- Create 3 conftest.py files  One per test directory
- Update imports  Remove `shared.` prefix in internal tests
- Run tests  163 auth + 52 testing passing independently

**Total: 532 automated tests passing**

---

## Quick Reference

**Adding a New Module:**
1. Create `pyproject.toml` with dependencies
2. Run `poetry install`
3. Create `tests/conftest.py` with workspace path resolution
4. Verify tests: `poetry run pytest tests/unit/`

**Standard Import Pattern:**
```python
# From any module (winery, fruit_origin, fermentation):
from src.shared.wine_fermentator_logging import get_logger
from src.modules.winery.src.domain.entities import Winery

# From within shared module tests:
from testing.integration.session_manager import TestSessionManager
from auth.domain.user import User
```

**Testing a Module:**
```bash
cd src/modules/<module_name>
poetry install                   # First time only
poetry run pytest tests/unit/    # Run tests
```

---

## API Examples

### conftest.py Pattern
```python
# tests/conftest.py (in each module)
import sys
from pathlib import Path

# Add workspace root to Python path
workspace_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))
```

### pyproject.toml Template
```toml
[tool.poetry]
name = "module-name"
version = "0.1.0"
packages = [
    { include = "domain", from = "src" },
    { include = "repository_component", from = "src" },
]

[tool.poetry.dependencies]
python = "^3.9"
sqlalchemy = "^2.0.20"
structlog = "^25.5.0"
colorama = "^0.4.6"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"

[tool.pytest.ini_options]
asyncio_mode = "strict"
testpaths = ["tests"]
python_files = ["test_*.py"]
```

---

## Acceptance Criteria

### Phase 1: Winery Module 
- [x] Create pyproject.toml with all dependencies
- [x] Run `poetry install`  30+ packages installed
- [x] Create tests/conftest.py for workspace path
- [x] Update imports in repository/entities
- [x] Verify 22/22 tests passing independently

### Phase 2: Fruit Origin Module 
- [x] Update pyproject.toml (remove shared editable)
- [x] Fix TOML syntax errors (duplicates)
- [x] Update tests/conftest.py pattern
- [x] Run `poetry lock` and `poetry install`
- [x] Verify 72/72 tests passing independently

### Phase 3: Documentation 
- [x] Create module-setup-guide.md (~400 lines)
- [x] Document standard structure
- [x] Provide CI/CD integration examples
- [x] Create troubleshooting guide
- [x] Update ADR-INDEX

### Phase 4: Shared Module 
- [x] Enhance pyproject.toml with auth/API dependencies
- [x] Install 34 packages via poetry install
- [x] Create 3 conftest.py files (auth, testing, infra)
- [x] Update imports to package-relative (remove `shared.` prefix)
- [x] Verify 163 auth + 52 testing tests passing

---

## Implementation Timeline

| Phase | Duration | Tests | Status |
|-------|----------|-------|--------|
| Phase 1: Winery | 2 hours | 22 tests |  Complete |
| Phase 2: Fruit Origin | 1.5 hours | 72 tests |  Complete |
| Phase 3: Documentation | 2.5 hours | Manual |  Complete |
| Phase 4: Shared | 2 hours | 215 tests |  Complete |

**Total Duration:** 8 hours (Dec 22-23, 2025)  
**Total Tests:** 532 automated tests  
**Status:** Production ready 

---

## Status

 **IMPLEMENTED** - All 4 phases complete (December 23, 2025)

**Production Readiness:**
-  532/532 tests passing across all modules
-  Each module runs independently
-  Comprehensive documentation (module-setup-guide.md)
-  Zero regressions
-  Microservices deployment ready

**Module Status:**
-  Fermentation: 223 tests passing
-  Winery: 22 tests passing
-  Fruit Origin: 72 tests passing
-  Shared Auth: 163 tests passing
-  Shared Testing: 52 tests passing

**Lessons Learned:**
1. Editable shared package doesnt scale (circular imports)
2. conftest.py approach is simpler and more maintainable
3. Import path consistency is critical across all modules
4. TOML validation important (watch for duplicates)

**Next Steps for Deployment:**
- Each module can now be containerized independently
- Separate Dockerfiles per module
- Deploy as microservices to different services
- Scale independently based on load
