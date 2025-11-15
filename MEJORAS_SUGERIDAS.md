# 🚀 Plan de Mejoras - Wine Fermentation System

**Fecha de creación:** 2025-11-14  
**Basado en:** Evaluación de Arquitectura y Calidad de Código  
**Estado del proyecto:** Excelente (A - 88/100)  
**Branch:** `feature/fermentation-api-layer`

---

## 📊 Resumen de Evaluación

| Categoría | Calificación Actual | Objetivo |
|-----------|---------------------|----------|
| Arquitectura | A+ (95/100) | A+ (98/100) |
| Principios SOLID | A (90/100) | A+ (95/100) |
| Calidad de Código | A- (85/100) | A (90/100) |
| Testing | A (90/100) | A+ (95/100) |
| Documentación | A+ (95/100) | A+ (98/100) |
| Mantenibilidad | A (88/100) | A+ (95/100) |

**Calificación objetivo:** A+ (93/100)

---

## 🔴 PRIORIDAD ALTA (1-2 semanas)

### Mejora #1: Exception Handler Global en FastAPI

**Problema identificado:**
- Código duplicado en 3 endpoints (create, get, list)
- 50+ líneas de try/except repetidas
- Dificulta mantenimiento y consistencia

**Código actual (duplicado):**
```python
# fermentation_router.py (líneas ~76-95)
try:
    created_fermentation = await service.create_fermentation(...)
    return FermentationResponse.from_entity(created_fermentation)
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except (DuplicateError, BusinessRuleViolation) as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail=f"...")
```

**Solución propuesta:**

**Archivo nuevo:** `src/modules/fermentation/src/api/exception_handlers.py`
```python
"""
Global exception handlers for FastAPI application.

Centralizes error mapping from domain/service exceptions to HTTP responses.
Following ADR-006 API Layer Design.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.modules.fermentation.src.service_component.errors import (
    ValidationError,
    NotFoundError,
    DuplicateError,
    BusinessRuleViolation
)


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle ValidationError from service layer."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "type": "validation_error"}
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError from service layer."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "type": "value_error"}
    )


async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle NotFoundError from service layer."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "type": "not_found"}
    )


async def duplicate_error_handler(request: Request, exc: DuplicateError) -> JSONResponse:
    """Handle DuplicateError from service layer."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "type": "duplicate_error"}
    )


async def business_rule_violation_handler(request: Request, exc: BusinessRuleViolation) -> JSONResponse:
    """Handle BusinessRuleViolation from service layer."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "type": "business_rule_violation"}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions (500 Internal Server Error)."""
    # TODO: Log to monitoring system (Sentry, Datadog, etc.)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "type": "internal_server_error"
        }
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app.
    
    Usage:
        from fastapi import FastAPI
        from api.exception_handlers import register_exception_handlers
        
        app = FastAPI()
        register_exception_handlers(app)
    """
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(DuplicateError, duplicate_error_handler)
    app.add_exception_handler(BusinessRuleViolation, business_rule_violation_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
```

**Actualizar:** `fermentation_router.py` (simplificar endpoints)
```python
# ANTES (líneas 52-110):
async def create_fermentation(...):
    try:
        # 50+ líneas de try/except
    except ValidationError as e:
        raise HTTPException(...)
    # ... más excepciones

# DESPUÉS:
async def create_fermentation(
    request: FermentationCreateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[IFermentationService, Depends(get_fermentation_service)]
) -> FermentationResponse:
    """
    Create a new fermentation.
    
    Exception handling delegated to global handlers.
    """
    create_dto = FermentationCreate(
        fermented_by_user_id=current_user.user_id,
        vintage_year=request.vintage_year,
        yeast_strain=request.yeast_strain,
        vessel_code=request.vessel_code,
        input_mass_kg=request.input_mass_kg,
        initial_sugar_brix=request.initial_sugar_brix,
        initial_density=request.initial_density,
        start_date=request.start_date
    )
    
    # Exceptions propagate to global handlers
    created_fermentation = await service.create_fermentation(
        winery_id=current_user.winery_id,
        user_id=current_user.user_id,
        data=create_dto
    )
    
    return FermentationResponse.from_entity(created_fermentation)
```

**Tests:** `tests/api/test_exception_handlers.py`
```python
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.fermentation.src.api.exception_handlers import register_exception_handlers
from src.modules.fermentation.src.service_component.errors import (
    ValidationError, NotFoundError, DuplicateError
)


@pytest.fixture
def app():
    app = FastAPI()
    register_exception_handlers(app)
    
    @app.get("/test/validation")
    async def test_validation():
        raise ValidationError("Validation failed")
    
    @app.get("/test/not-found")
    async def test_not_found():
        raise NotFoundError("Resource not found")
    
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_validation_error_returns_400(client):
    response = client.get("/test/validation")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Validation failed",
        "type": "validation_error"
    }


def test_not_found_error_returns_404(client):
    response = client.get("/test/not-found")
    assert response.status_code == 404
    assert response.json()["type"] == "not_found"
```

**Beneficios:**
- ✅ Elimina 50+ líneas de código duplicado
- ✅ Centraliza error mapping (Single Responsibility)
- ✅ Facilita agregar logging/monitoring
- ✅ Respuestas de error consistentes
- ✅ Tipo de error en JSON (`type` field)

**Estimación:** 2-3 horas  
**Impacto:** Alto (reduce duplicación, mejora mantenibilidad)  
**Riesgo:** Bajo (cambio localizado, tests existentes siguen funcionando)

---

### Mejora #2: Unit of Work Pattern para Transacciones Atómicas

**Problema identificado:**
- No hay manera de hacer transacciones multi-repository atómicas
- Cada operación de repository es un commit independiente
- Dificulta workflows complejos (ej: crear fermentation + samples)

**Contexto:**
```python
# Escenario problemático actual:
await fermentation_repo.create(fermentation)  # COMMIT 1
await sample_repo.create(sample1)             # COMMIT 2 - ¿Qué pasa si falla?
await sample_repo.create(sample2)             # COMMIT 3 - Estado inconsistente
```

**Solución propuesta:**

**Archivo nuevo:** `src/shared/infra/repository/unit_of_work.py`
```python
"""
Unit of Work Pattern implementation.

Provides atomic transactions across multiple repositories.
Following Martin Fowler's patterns: https://martinfowler.com/eaaCatalog/unitOfWork.html
"""

from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infra.interfaces.session_manager import ISessionManager
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository


class UnitOfWork:
    """
    Unit of Work for managing database transactions.
    
    Provides:
    - Atomic transactions across multiple repositories
    - Automatic commit on success
    - Automatic rollback on error
    - Lazy repository initialization
    
    Usage:
        async with UnitOfWork(session_manager) as uow:
            fermentation = await uow.fermentation_repo.create(...)
            sample = await uow.sample_repo.create(...)
            # Auto-commit if no exceptions
    """
    
    def __init__(self, session_manager: ISessionManager):
        self.session_manager = session_manager
        self._session: Optional[AsyncSession] = None
        self._fermentation_repo: Optional[FermentationRepository] = None
        self._sample_repo: Optional[SampleRepository] = None
    
    @property
    def fermentation_repo(self) -> FermentationRepository:
        """Lazy-load fermentation repository."""
        if self._fermentation_repo is None:
            if self._session is None:
                raise RuntimeError("UnitOfWork not initialized. Use 'async with' statement.")
            self._fermentation_repo = FermentationRepository(self.session_manager)
        return self._fermentation_repo
    
    @property
    def sample_repo(self) -> SampleRepository:
        """Lazy-load sample repository."""
        if self._sample_repo is None:
            if self._session is None:
                raise RuntimeError("UnitOfWork not initialized. Use 'async with' statement.")
            self._sample_repo = SampleRepository(self.session_manager)
        return self._sample_repo
    
    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for atomic transactions.
        
        Usage:
            async with uow.transaction():
                await uow.fermentation_repo.create(...)
                await uow.sample_repo.create(...)
                # Auto-commit on success, auto-rollback on exception
        """
        session_cm = await self.session_manager.get_session()
        async with session_cm as session:
            self._session = session
            try:
                yield self
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                self._session = None


# Alternative: Simpler function-based UoW
@asynccontextmanager
async def unit_of_work(session_manager: ISessionManager):
    """
    Simplified Unit of Work as context manager.
    
    Usage:
        async with unit_of_work(session_manager) as uow:
            await uow.fermentation_repo.create(...)
    """
    uow = UnitOfWork(session_manager)
    async with uow.transaction():
        yield uow
```

**Uso en Service Layer:**

**Actualizar:** `fermentation_service.py` (nuevo método)
```python
class FermentationService(IFermentationService):
    
    async def create_fermentation_with_initial_sample(
        self,
        winery_id: int,
        user_id: int,
        fermentation_data: FermentationCreate,
        initial_sample_data: SampleCreate
    ) -> Fermentation:
        """
        Create fermentation and initial sample in atomic transaction.
        
        Args:
            winery_id: Multi-tenancy scope
            user_id: Audit trail
            fermentation_data: Fermentation creation data
            initial_sample_data: Initial sample (sugar, density, etc.)
        
        Returns:
            Created fermentation entity
        
        Raises:
            ValueError: Validation failed
            RepositoryError: Database transaction failed
        """
        from src.shared.infra.repository.unit_of_work import unit_of_work
        
        # Validate fermentation
        validation_result = self._validator.validate_creation_data(fermentation_data)
        if not validation_result.is_valid:
            raise ValueError(f"Validation failed: {validation_result.errors}")
        
        # Atomic transaction
        async with unit_of_work(self._fermentation_repo.session_manager) as uow:
            # Create fermentation
            fermentation = await uow.fermentation_repo.create(
                winery_id=winery_id,
                data=fermentation_data
            )
            
            # Create initial sample
            initial_sample_data.fermentation_id = fermentation.id
            await uow.sample_repo.create(
                winery_id=winery_id,
                data=initial_sample_data
            )
            
            # Auto-commit if no exceptions
            return fermentation
```

**Tests:** `tests/unit/test_unit_of_work.py`
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.shared.infra.repository.unit_of_work import UnitOfWork, unit_of_work


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_session_manager(mock_session):
    manager = MagicMock()
    
    @asynccontextmanager
    async def get_session():
        yield mock_session
    
    manager.get_session = get_session
    return manager


@pytest.mark.asyncio
async def test_unit_of_work_commits_on_success(mock_session_manager, mock_session):
    """Test that UoW commits when no exceptions occur."""
    async with unit_of_work(mock_session_manager) as uow:
        # Simulate repository operations
        pass
    
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_unit_of_work_rolls_back_on_exception(mock_session_manager, mock_session):
    """Test that UoW rolls back when exception occurs."""
    with pytest.raises(ValueError):
        async with unit_of_work(mock_session_manager) as uow:
            raise ValueError("Simulated error")
    
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_unit_of_work_lazy_loads_repositories(mock_session_manager):
    """Test that repositories are initialized only when accessed."""
    async with unit_of_work(mock_session_manager) as uow:
        # Repositories not initialized yet
        assert uow._fermentation_repo is None
        
        # Access triggers lazy load
        repo = uow.fermentation_repo
        assert repo is not None
```

**Beneficios:**
- ✅ Transacciones atómicas multi-repository
- ✅ Rollback automático en errores
- ✅ Evita estados inconsistentes en BD
- ✅ Código más limpio (context manager)
- ✅ Sigue patrón Enterprise (Martin Fowler)

**Estimación:** 4-5 horas  
**Impacto:** Alto (habilita workflows complejos)  
**Riesgo:** Medio (cambio en arquitectura de transacciones, requiere testing exhaustivo)

---

### Mejora #3: Environment Configuration (.env)

**Problema identificado:**
- Configuración hardcoded en varios archivos
- No hay `.env.example` para onboarding
- Dificulta deployment en diferentes ambientes

**Archivos afectados:**
```python
# src/shared/infra/database/config.py (hardcoded)
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/wine_fermentation"

# src/shared/auth/infra/services/jwt_service.py (hardcoded)
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
```

**Solución propuesta:**

**Archivo nuevo:** `.env.example`
```bash
# Wine Fermentation System - Environment Configuration
# Copy this file to .env and update with your values

# ============================================================
# DATABASE CONFIGURATION
# ============================================================
# Production: PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/wine_fermentation

# Development: SQLite (optional)
# DATABASE_URL=sqlite+aiosqlite:///./dev.db

# ============================================================
# JWT AUTHENTICATION
# ============================================================
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=CHANGE_THIS_TO_A_SECURE_RANDOM_STRING
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# ============================================================
# APPLICATION
# ============================================================
APP_NAME=Wine Fermentation System
APP_VERSION=0.1.0
DEBUG=false
LOG_LEVEL=INFO

# ============================================================
# CORS (Cross-Origin Resource Sharing)
# ============================================================
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
CORS_CREDENTIALS=true

# ============================================================
# DATABASE POOL (PostgreSQL only)
# ============================================================
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_PRE_PING=true

# ============================================================
# TESTING
# ============================================================
TEST_DATABASE_URL=sqlite+aiosqlite:///:memory:?cache=shared
```

**Archivo nuevo:** `src/shared/infra/config/settings.py`
```python
"""
Application settings using pydantic-settings.

Loads configuration from environment variables with validation.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Usage:
        from config.settings import get_settings
        
        settings = get_settings()
        print(settings.database_url)
    """
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30
    
    # Application
    app_name: str = "Wine Fermentation System"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_credentials: bool = True
    
    # Testing
    test_database_url: str = "sqlite+aiosqlite:///:memory:?cache=shared"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Singleton pattern
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience
settings = get_settings()
```

**Actualizar:** `src/shared/infra/database/config.py`
```python
# ANTES:
class DatabaseConfig:
    def __init__(self):
        self.url = "postgresql+asyncpg://..."  # Hardcoded

# DESPUÉS:
from src.shared.infra.config.settings import get_settings

class DatabaseConfig:
    def __init__(self, url: Optional[str] = None):
        settings = get_settings()
        self.url = url or settings.database_url
        self.pool_size = settings.db_pool_size
        self.max_overflow = settings.db_max_overflow
        self.pool_pre_ping = settings.db_pool_pre_ping
```

**Actualizar:** `pyproject.toml` (agregar dependencia)
```toml
[tool.poetry.dependencies]
pydantic-settings = "^2.0.0"
python-dotenv = "^1.0.0"
```

**Actualizar:** `.gitignore`
```bash
# Environment files
.env
.env.local
.env.*.local
```

**Tests:** `tests/unit/test_settings.py`
```python
import os
import pytest
from src.shared.infra.config.settings import Settings


def test_settings_loads_from_env(monkeypatch):
    """Test that settings load from environment variables."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    
    settings = Settings()
    assert settings.database_url == "postgresql://test"
    assert settings.jwt_secret_key == "test-secret"


def test_settings_has_defaults():
    """Test that settings have sensible defaults."""
    os.environ["JWT_SECRET_KEY"] = "required-key"
    settings = Settings()
    
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_access_token_expire_minutes == 15
    assert settings.debug is False
```

**Beneficios:**
- ✅ Configuración centralizada
- ✅ Validación automática (Pydantic)
- ✅ Fácil deployment (solo cambiar .env)
- ✅ Secrets no en código fuente
- ✅ Type-safe configuration

**Estimación:** 3-4 horas  
**Impacto:** Alto (mejor seguridad, facilita deployment)  
**Riesgo:** Medio (requiere actualizar múltiples archivos)

---

## 🟡 PRIORIDAD MEDIA (3-4 semanas)

### Mejora #4: Interface Segregation en IFermentationService

**Problema identificado:**
- `IFermentationService` tiene 7 métodos (viola ISP)
- Clients que solo necesitan lectura dependen de métodos de escritura
- Dificulta testing y mocking

**Código actual:**
```python
class IFermentationService(ABC):
    async def create_fermentation(...)      # WRITE
    async def get_fermentation(...)         # READ
    async def get_fermentations_by_winery(...)  # READ
    async def update_status(...)            # WRITE
    async def complete_fermentation(...)    # WRITE
    async def soft_delete(...)              # WRITE
    def validate_creation_data(...)         # VALIDATE
```

**Solución propuesta:**

**Archivo nuevo:** `src/modules/fermentation/src/service_component/interfaces/fermentation_reader_interface.py`
```python
"""Interface for read-only fermentation operations."""

from abc import ABC, abstractmethod
from typing import Optional, List

from src.modules.fermentation.src.domain.entities.fermentation import Fermentation


class IFermentationReader(ABC):
    """
    Read-only interface for fermentation queries.
    
    Follows Interface Segregation Principle - clients that only
    need to read data don't depend on write methods.
    """
    
    @abstractmethod
    async def get_fermentation(
        self,
        fermentation_id: int,
        winery_id: int
    ) -> Optional[Fermentation]:
        """Get single fermentation by ID."""
        pass
    
    @abstractmethod
    async def get_fermentations_by_winery(
        self,
        winery_id: int,
        status: Optional[str] = None,
        include_completed: bool = False
    ) -> List[Fermentation]:
        """Get all fermentations for a winery."""
        pass
```

**Archivo nuevo:** `src/modules/fermentation/src/service_component/interfaces/fermentation_writer_interface.py`
```python
"""Interface for write fermentation operations."""

from abc import ABC, abstractmethod

from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.dtos import FermentationCreate


class IFermentationWriter(ABC):
    """
    Write interface for fermentation operations.
    
    Follows Interface Segregation Principle.
    """
    
    @abstractmethod
    async def create_fermentation(
        self,
        winery_id: int,
        user_id: int,
        data: FermentationCreate
    ) -> Fermentation:
        """Create new fermentation."""
        pass
    
    @abstractmethod
    async def update_status(
        self,
        fermentation_id: int,
        winery_id: int,
        new_status: str,
        user_id: int
    ) -> bool:
        """Update fermentation status."""
        pass
    
    @abstractmethod
    async def complete_fermentation(
        self,
        fermentation_id: int,
        winery_id: int,
        user_id: int,
        completion_date: datetime
    ) -> Fermentation:
        """Complete fermentation."""
        pass
    
    @abstractmethod
    async def soft_delete(
        self,
        fermentation_id: int,
        winery_id: int,
        user_id: int
    ) -> bool:
        """Soft delete fermentation."""
        pass
```

**Actualizar:** `fermentation_service.py`
```python
# FermentationService implements ALL interfaces
class FermentationService(IFermentationReader, IFermentationWriter, IFermentationService):
    """
    Full fermentation service implementation.
    
    Implements multiple interfaces following ISP.
    """
    # ... existing implementation
```

**Uso en API Layer:**
```python
# Read-only endpoint solo necesita IFermentationReader
async def get_fermentation(
    fermentation_id: int,
    service: Annotated[IFermentationReader, Depends(get_fermentation_reader)]
):
    # Solo puede llamar métodos de lectura
    return await service.get_fermentation(fermentation_id, winery_id)

# Write endpoint necesita IFermentationWriter
async def create_fermentation(
    request: FermentationCreateRequest,
    service: Annotated[IFermentationWriter, Depends(get_fermentation_writer)]
):
    # Solo puede llamar métodos de escritura
    return await service.create_fermentation(...)
```

**Beneficios:**
- ✅ Menor acoplamiento (clients usan solo lo que necesitan)
- ✅ Mejor testability (mock interfaces más pequeñas)
- ✅ Cumple ISP (Interface Segregation Principle)
- ✅ Más fácil agregar nuevas implementaciones

**Estimación:** 5-6 horas  
**Impacto:** Medio (mejora diseño, no cambia funcionalidad)  
**Riesgo:** Bajo (backward compatible, puede coexistir con IFermentationService)

---

### Mejora #5: Conventional Commits + Changelog Automático

**Problema identificado:**
- No hay estándar para mensajes de commit
- No hay changelog generado automáticamente
- Dificulta release notes y trazabilidad

**Solución propuesta:**

**Archivo nuevo:** `.commitlintrc.json`
```json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [
      2,
      "always",
      [
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "perf",
        "test",
        "build",
        "ci",
        "chore",
        "revert"
      ]
    ],
    "scope-enum": [
      2,
      "always",
      [
        "api",
        "auth",
        "fermentation",
        "samples",
        "database",
        "tests",
        "docs"
      ]
    ]
  }
}
```

**Archivo nuevo:** `.github/workflows/release.yml`
```yaml
name: Release

on:
  push:
    branches:
      - main

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install standard-version
        run: npm install -g standard-version
      
      - name: Generate changelog and bump version
        run: standard-version
      
      - name: Push changes
        run: |
          git push --follow-tags origin main
```

**Archivo nuevo:** `COMMIT_CONVENTIONS.md`
```markdown
# Commit Message Conventions

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types

- **feat**: Nueva funcionalidad
- **fix**: Bug fix
- **docs**: Cambios en documentación
- **style**: Formateo, no cambia lógica
- **refactor**: Refactoring sin cambiar funcionalidad
- **perf**: Mejora de performance
- **test**: Agregar/modificar tests
- **build**: Cambios en build system
- **ci**: Cambios en CI/CD
- **chore**: Tareas de mantenimiento

## Scopes

- **api**: API layer
- **auth**: Authentication/Authorization
- **fermentation**: Fermentation module
- **samples**: Samples module
- **database**: Database infrastructure
- **tests**: Test infrastructure
- **docs**: Documentation

## Examples

```bash
# Nueva feature
feat(api): add pagination to GET /fermentations

Implements pagination with page and size query parameters.
Includes validation and tests.

Closes #123

# Bug fix
fix(auth): resolve JWT token expiry issue

Token was expiring immediately due to timezone mismatch.
Now using UTC for all timestamps.

# Breaking change
feat(api)!: change fermentation status enum values

BREAKING CHANGE: Status values changed from UPPERCASE to lowercase.
Migration required for existing databases.
```

## Benefits

- ✅ Changelog generado automáticamente
- ✅ Versionado semántico automático (SemVer)
- ✅ Commits consistentes y legibles
- ✅ Fácil hacer release notes
```

**Configurar Git Hooks:** `.husky/commit-msg`
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npx --no-install commitlint --edit "$1"
```

**Beneficios:**
- ✅ Commits estandarizados
- ✅ Changelog automático (CHANGELOG.md)
- ✅ Versionado automático (SemVer)
- ✅ Mejor trazabilidad de cambios

**Estimación:** 2-3 horas  
**Impacto:** Medio (mejora proceso de desarrollo)  
**Riesgo:** Bajo (solo afecta workflow de commits)

---

### Mejora #6: Logging y Monitoring

**Problema identificado:**
- No hay logging estructurado
- Errores 500 no se registran en sistema de monitoring
- Dificulta debugging en producción

**Solución propuesta:**

**Archivo nuevo:** `src/shared/infra/logging/logger.py`
```python
"""
Structured logging configuration.

Uses structlog for structured, JSON-formatted logs compatible
with monitoring systems (Datadog, ELK, etc.).
"""

import logging
import structlog
from typing import Any, Dict

from src.shared.infra.config.settings import get_settings


def configure_logging():
    """
    Configure structured logging with structlog.
    
    Features:
    - JSON output in production
    - Colored console in development
    - Automatic context injection (request_id, user_id, etc.)
    - Exception stack traces
    """
    settings = get_settings()
    
    # Determine output format based on environment
    if settings.debug:
        # Development: colorful console output
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ]
    else:
        # Production: JSON for log aggregation
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True
    )


def get_logger(name: str = __name__) -> Any:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


# Middleware for request logging
from fastapi import Request
import time

async def logging_middleware(request: Request, call_next):
    """
    Log all HTTP requests with timing.
    
    Adds request_id to log context for request tracing.
    """
    logger = get_logger("api")
    
    # Generate request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # Bind context for this request
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Log successful request
        duration = time.time() - start_time
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2)
        )
        
        return response
    
    except Exception as e:
        # Log failed request
        duration = time.time() - start_time
        logger.error(
            "request_failed",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=round(duration * 1000, 2),
            exc_info=True
        )
        raise
```

**Actualizar:** `exception_handlers.py`
```python
from src.shared.infra.logging.logger import get_logger

logger = get_logger("api.exceptions")

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with logging."""
    
    # Log to monitoring system
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        exc_info=True  # Include stack trace
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request.headers.get("X-Request-ID")}
    )
```

**Integración con Sentry (opcional):**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

def configure_sentry():
    """Configure Sentry for error tracking."""
    settings = get_settings()
    
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1
        )
```

**Actualizar:** `pyproject.toml`
```toml
[tool.poetry.dependencies]
structlog = "^23.1.0"
python-json-logger = "^2.0.7"
sentry-sdk = {extras = ["fastapi"], version = "^1.32.0", optional = true}
```

**Beneficios:**
- ✅ Logs estructurados (JSON)
- ✅ Request tracing (request_id)
- ✅ Performance monitoring (duration)
- ✅ Error tracking (Sentry)
- ✅ Compatible con Datadog, ELK, Splunk

**Estimación:** 4-5 horas  
**Impacto:** Alto (crucial para producción)  
**Riesgo:** Bajo (adición, no modifica lógica existente)

---

## 🟢 PRIORIDAD BAJA (1-2 meses)

### Mejora #7: End-to-End Tests

**Objetivo:** Tests de workflows completos

**Ejemplo:**
```python
@pytest.mark.e2e
async def test_complete_fermentation_lifecycle():
    """Test full fermentation workflow: CREATE → GET → UPDATE → COMPLETE."""
    
    # 1. Create fermentation
    response = client.post("/api/v1/fermentations", json={...})
    assert response.status_code == 201
    fermentation_id = response.json()["id"]
    
    # 2. Get fermentation
    response = client.get(f"/api/v1/fermentations/{fermentation_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "ACTIVE"
    
    # 3. Add samples
    response = client.post(f"/api/v1/fermentations/{fermentation_id}/samples", json={...})
    assert response.status_code == 201
    
    # 4. Complete fermentation
    response = client.patch(f"/api/v1/fermentations/{fermentation_id}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
```

**Estimación:** 6-8 horas  
**Impacto:** Medio (aumenta confianza en releases)

---

### Mejora #8: API Versioning Dinámico

**Objetivo:** Soportar múltiples versiones de API simultáneamente

**Ejemplo:**
```python
# v1: Actual
@router_v1.get("/fermentations")
async def list_fermentations_v1(...):
    # Current implementation

# v2: Nueva versión con breaking changes
@router_v2.get("/fermentations")
async def list_fermentations_v2(...):
    # New implementation with different response format
```

**Estimación:** 8-10 horas  
**Impacto:** Bajo (solo necesario cuando haya breaking changes)

---

### Mejora #9: Performance Optimization

**Objetivo:** Optimizar queries y agregar caching

**Áreas:**
1. **Database Query Optimization:**
   - Agregar índices en columnas frecuentes (winery_id, status)
   - Eager loading de relaciones (joinedload)
   - Query batching

2. **Caching:**
   - Redis para datos frecuentemente accedidos
   - Cache de resultados de validación

**Ejemplo:**
```python
# Agregar cache con Redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@cache(expire=300)  # 5 minutos
async def get_fermentation(fermentation_id: int, winery_id: int):
    # Cached result
    return await repo.get_by_id(fermentation_id, winery_id)
```

**Estimación:** 10-12 horas  
**Impacto:** Alto (solo cuando haya problemas de performance)

---

## 📋 Plan de Implementación Sugerido

### Semana 1-2 (Prioridad Alta)
- [ ] Mejora #1: Exception Handlers (2-3 horas)
- [ ] Mejora #3: Environment Config (3-4 horas)
- [ ] Mejora #2: Unit of Work (4-5 horas)
- [ ] **Total:** ~10-12 horas

### Semana 3-4 (Prioridad Media)
- [ ] Mejora #6: Logging & Monitoring (4-5 horas)
- [ ] Mejora #4: Interface Segregation (5-6 horas)
- [ ] Mejora #5: Conventional Commits (2-3 horas)
- [ ] **Total:** ~11-14 horas

### Mes 2-3 (Prioridad Baja)
- [ ] Mejora #7: E2E Tests (6-8 horas)
- [ ] Mejora #8: API Versioning (8-10 horas)
- [ ] Mejora #9: Performance (10-12 horas)
- [ ] **Total:** ~24-30 horas

---

## ✅ Criterios de Aceptación

Para cada mejora:

1. **Tests pasan:** 100% de tests existentes + nuevos tests
2. **Documentación:** Actualizar component-context.md correspondiente
3. **Code review:** Aprobación antes de merge
4. **No regresiones:** Funcionalidad existente intacta
5. **Performance:** No degradación > 5%

---

## 📊 Métricas de Éxito

**Objetivo post-mejoras:**

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Duplicación de código | ~3% | < 1% |
| Cobertura de tests | ~90% | > 95% |
| Tiempo de onboarding | ~4 horas | < 2 horas |
| Tiempo de deployment | Manual | < 5 min |
| MTTR (Mean Time To Repair) | N/A | < 1 hora |

---

## 🔄 Proceso de Implementación

Para cada mejora:

```bash
# 1. Crear branch
git checkout -b improvement/exception-handlers

# 2. Implementar cambios (TDD)
# - RED: Write failing tests
# - GREEN: Implement minimum code
# - REFACTOR: Clean up

# 3. Verificar
poetry run pytest
poetry run mypy src/

# 4. Commit (conventional)
git commit -m "feat(api): add global exception handlers

Centralizes error mapping in FastAPI application.
Eliminates 50+ lines of duplicated try/except blocks.

Closes #XXX"

# 5. Push & PR
git push origin improvement/exception-handlers

# 6. Code review + merge
# 7. Deploy
```

---

## 📝 Notas Finales

- **No bloquean desarrollo actual:** Todas son mejoras incrementales
- **Backward compatible:** No rompen funcionalidad existente
- **Documentadas:** Cada mejora incluye tests y documentación
- **Priorizadas:** Implementar en orden sugerido para máximo impacto

**¿Listo para empezar?** Sugiero comenzar con **Mejora #1** (Exception Handlers) por:
- ✅ Alto impacto (elimina 50+ líneas duplicadas)
- ✅ Bajo riesgo (cambio localizado)
- ✅ Rápido (2-3 horas)
- ✅ Prepara terreno para Mejora #6 (Logging)

---

**Última actualización:** 2025-11-14  
**Próxima revisión:** Después de implementar mejoras de Prioridad Alta
