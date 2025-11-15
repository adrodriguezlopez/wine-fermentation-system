# Architectural Guidelines

**Wine Fermentation System**  
**Última actualización:** 2025-10-05  
**Propósito:** Principios arquitectónicos estándar para todo el sistema

---

## 🏗️ Principios Arquitectónicos Fundamentales

### SOLID Principles (Obligatorios)

**Single Responsibility Principle (SRP)**
- Cada clase tiene una sola razón para cambiar
- Ejemplos: `DatabaseConfig` (solo configuración), `DatabaseSession` (solo session management)

**Open/Closed Principle (OCP)**  
- Extensible via interfaces sin modificar implementaciones existentes
- Ejemplo: Nuevos repositorios implementan `IBaseRepository` sin cambiar código existente

**Liskov Substitution Principle (LSP)**
- Todas las implementaciones son sustituibles por sus interfaces
- Ejemplo: `DatabaseSession` sustituible por cualquier `ISessionManager`

**Interface Segregation Principle (ISP)**
- Interfaces específicas, no genéricas
- Ejemplo: `IFermentationRepository` ≠ `ISampleRepository` ≠ `ISessionManager`

**Dependency Inversion Principle (DIP)**
- Dependencias hacia abstracciones, nunca hacia concreciones
- Ejemplo: `DatabaseSession(config: IDatabaseConfig)` no `DatabaseSession(config: DatabaseConfig)`

---

## 🎯 Clean Architecture Layers

```
┌─────────────────────────────────────────┐
│           Domain Layer                  │
│  ┌─────────────────────────────────┐    │
│  │   Repository Interfaces         │    │  
│  │   (IFermentationRepository)     │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
                    ▲
                    │ (dependency direction)
┌─────────────────────────────────────────┐
│        Infrastructure Layer             │
│  ┌─────────────────────────────────┐    │
│  │   Repository Implementations   │    │
│  │   Database, ORM, External APIs │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
                    ▲
                    │ 
┌─────────────────────────────────────────┐
│       Shared Infrastructure             │
│  ┌─────────────────────────────────┐    │
│  │   Session, Config, Errors      │    │
│  │   (IDatabaseConfig, ISessionMgr)│    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Rules:**
- Infrastructure can depend on Domain (via interfaces)
- Domain NEVER depends on Infrastructure
- Shared Infrastructure provides technical primitives

---

## 🔄 Design Patterns (Estándar)

### Repository Pattern
```python
# Domain defines interface
class IFermentationRepository(Protocol):
    async def get_by_id(self, id: int, winery_id: int) -> Fermentation: ...

# Infrastructure implements
class FermentationRepository(BaseRepository):
    async def get_by_id(self, id: int, winery_id: int) -> Fermentation: ...
```

### Unit of Work Pattern  
```python
# For transactions across multiple repositories
async with unit_of_work() as uow:
    fermentation = await uow.fermentation_repo.get_by_id(123, winery_id=1)
    await uow.sample_repo.add_sample(sample)
    await uow.commit()  # atomic
```

### Error Mapping Pattern
```python
# Database exceptions → Domain exceptions
try:
    await session.execute(query)
except IntegrityError as e:
    raise DuplicateEntityError(f"Entity already exists: {e}")
```

### Interface/Protocol Pattern
```python
# Use protocols for dependency inversion
class IDatabaseConfig(Protocol):
    @property
    def async_engine(self) -> AsyncEngine: ...

# Implementations follow contract  
class DatabaseConfig:
    @property
    def async_engine(self) -> AsyncEngine: ...
```

---

## 🧪 Development Methodology

### Test-Driven Development (TDD) - Religioso
1. **🔴 RED**: Write failing test first
2. **🟢 GREEN**: Minimum implementation to pass
3. **🔵 REFACTOR**: Clean code while keeping tests green
4. **Repeat**: For every feature/method

### Testing Strategy
```
Unit Tests: 
├── Domain logic (pure functions, no dependencies)
├── Repository implementations (mocked dependencies)  
├── Interface compliance (protocol adherence)
└── Error handling (exception mapping)

Integration Tests:
├── Database operations (real DB)
├── End-to-end workflows  
└── Performance validation
```

### File Organization
```
src/
├── shared/infra/          # Technical infrastructure
│   ├── interfaces/        # Protocols (IDatabaseConfig, ISessionManager)
│   ├── database/         # Implementations (DatabaseConfig, DatabaseSession)
│   └── test/             # Infrastructure tests
│
└── modules/{module}/
    ├── domain/           # Business logic + Repository interfaces
    ├── infrastructure/   # Repository implementations  
    ├── repository_component/  # Technical helpers (BaseRepository, errors)
    └── tests/           # Module-specific tests
```

---

## ⚡ Performance Guidelines

### Database Queries
- Always scope by `winery_id` (multi-tenant)
- Use soft-delete filters automatically
- Batch operations when possible
- Implement optimistic locking for concurrency

### Async Operations
- Use `async`/`await` consistently
- Context managers for resource cleanup
- Background tasks for non-critical operations

---

## 🔒 Security & Multi-tenancy

### Data Isolation
- Every query MUST include `winery_id`
- Repository methods enforce tenant scoping
- No cross-tenant data leakage

### Error Handling
- Never expose internal database errors to clients
- Map all exceptions through error catalog
- Log security-relevant events

---

## 🚫 Anti-Patterns (Evitar)

### ❌ Generic Repository
```python
# NO HACER
class GenericRepository[T]:
    async def get_all(self) -> List[T]: ...
```

### ❌ Anemic Domain Model
```python
# NO HACER - solo propiedades sin comportamiento
class Fermentation:
    id: int
    status: str  # sin métodos de negocio
```

### ❌ God Objects
```python
# NO HACER - responsabilidades mezcladas
class FermentationService:
    async def create_fermentation(self): ...
    async def send_email(self): ...
    async def calculate_taxes(self): ...
```

### ❌ Dependency on Concretions
```python
# NO HACER
class SampleRepository:
    def __init__(self, config: DatabaseConfig):  # concrete
        ...

# HACER
class SampleRepository:  
    def __init__(self, session_manager: ISessionManager):  # abstract
        ...
```

---

## �️ SQLAlchemy Import Best Practices

**Context:** Lecciones aprendidas de ADR-004 (Harvest Module Consolidation & SQLAlchemy Registry Fix)

### Problema: "Multiple classes found for path X"

SQLAlchemy mantiene un registro global de modelos. El error aparece cuando:
1. Usa paths cortos en `relationship()` → `"BaseSample"` es ambiguo
2. Single-table inheritance + bidirectional relationships → Conflicto en registro
3. Imports inconsistentes → Modelo registrado múltiples veces

### ✅ Solución 1: Fully-Qualified Paths en Relationships

**Regla:** Siempre usar la ruta completa del módulo en `relationship()`

```python
# ❌ ANTI-PATTERN: Path corto (ambiguo)
samples: Mapped[List["BaseSample"]] = relationship(
    "BaseSample",  # ← SQLAlchemy no sabe de dónde viene
    back_populates="fermentation"
)

# ✅ BEST PRACTICE: Fully-qualified path (explícito)
samples: Mapped[List["BaseSample"]] = relationship(
    "src.modules.fermentation.src.domain.entities.samples.base_sample.BaseSample",
    back_populates="fermentation"
)
```

**Beneficios:**
- No hay ambigüedad en el registry
- Fácil identificar origen del modelo
- Funciona con módulos múltiples

**Tradeoff:**
- Paths largos → más verboso
- Mitigación: Claridad > brevedad

---

### ✅ Solución 2: Unidirectional Relationships para Herencia Polimórfica

**Regla:** Con single-table inheritance, hacer relationship unidireccional usando `viewonly=True`

```python
# En BaseSample (clase base con herencia polimórfica)
class BaseSample(BaseEntity):
    __tablename__ = "samples"
    
    # Columna discriminadora
    sample_type: Mapped[str] = mapped_column(String(50))
    
    # ✅ Relationship unidireccional (viewonly=True)
    fermentation: Mapped["Fermentation"] = relationship(
        "src.modules.fermentation.src.domain.entities.fermentation.Fermentation",
        viewonly=True  # ← No intenta configurar back_populates
    )
    
    __mapper_args__ = {
        "polymorphic_identity": "sample",
        "polymorphic_on": sample_type,
    }

# En Fermentation (clase relacionada)
class Fermentation(BaseEntity):
    # ✅ Relationship sin back_populates
    samples: Mapped[List["BaseSample"]] = relationship(
        "src.modules.fermentation.src.domain.entities.samples.base_sample.BaseSample",
        cascade="all, delete-orphan"
        # NO back_populates para evitar conflicto con herencia
    )
```

**Por qué funciona:**
- `viewonly=True` → SQLAlchemy no intenta sincronizar bidireccional
- Evita conflictos con subclases (`WineSample`, `JuiceSample`)
- Permite navegación desde Fermentation → Samples (dirección más común)

**Tradeoff:**
- No se puede navegar `sample.fermentation` automáticamente
- Mitigación: Usar query explícita si se necesita navegación inversa

---

### ✅ Solución 3: Imports Consistentes en Entities

**Regla:** Importar `BaseEntity` siempre con ruta completa desde `src.`

```python
# ❌ ANTI-PATTERN: Import relativo inconsistente
from shared.infra.orm.base_entity import BaseEntity

# ✅ BEST PRACTICE: Import absoluto consistente
from src.shared.infra.orm.base_entity import BaseEntity
```

**Beneficios:**
- Mismo path de import en todos los módulos
- Evita doble registro del modelo base
- Compatible con tests y scripts

**Aplicar en:**
- Todos los entities (`fermentation.py`, `harvest_lot.py`, etc.)
- Tests que importan entities
- Scripts de debugging/recreación de DB

---

### ✅ Solución 4: `extend_existing=True` para Test Compatibility

**Regla:** Agregar `extend_existing=True` en `__table_args__` para entities usados en tests

```python
class HarvestLot(BaseEntity):
    __tablename__ = "harvest_lots"
    
    code: Mapped[str] = mapped_column(String(100))
    harvest_date: Mapped[datetime]
    
    __table_args__ = (
        UniqueConstraint('code', 'winery_id', name='uq_harvest_lot_code_winery'),
        {'extend_existing': True}  # ← Permite re-registro en tests
    )
```

**Por qué:**
- Tests pueden importar modelos múltiples veces (fixtures, conftest, test files)
- `extend_existing=True` → SQLAlchemy no falla si tabla ya está registrada
- Solo aplica en test environment, no afecta producción

---

### ✅ Solución 5: Transaction Management en Fixtures

**Regla:** En fixtures de tests, usar `flush()` en lugar de `commit()`

```python
# ❌ ANTI-PATTERN: commit() cierra transacción
@pytest_asyncio.fixture
async def test_winery(db_session):
    winery = Winery(code="TEST-WINERY", name="Test Winery")
    db_session.add(winery)
    await db_session.commit()  # ← Cierra transacción
    await db_session.refresh(winery)  # ← Abre nueva transacción
    return winery

# ✅ BEST PRACTICE: flush() mantiene transacción abierta
@pytest_asyncio.fixture
async def test_winery(db_session):
    winery = Winery(code="TEST-WINERY", name="Test Winery")
    db_session.add(winery)
    await db_session.flush()  # ← Asigna ID pero mantiene transacción
    return winery
    # Context manager hace rollback automático al final del test
```

**Beneficios:**
- Mantiene aislamiento entre tests
- No necesita cleanup manual
- `flush()` asigna IDs para relaciones FK

---

### 🎯 Checklist: SQLAlchemy Entity Development

Cuando creas o modificas un entity:

- [ ] ¿Import de `BaseEntity` es `from src.shared.infra.orm.base_entity`?
- [ ] ¿Relationships usan fully-qualified paths?
- [ ] ¿Single-table inheritance usa `viewonly=True` si es necesario?
- [ ] ¿`__table_args__` incluye `extend_existing=True` si se usa en tests?
- [ ] ¿Unique constraints incluyen `winery_id` para multi-tenancy?
- [ ] ¿Fixtures usan `flush()` en lugar de `commit()`?

---

### 📚 Referencias

- **ADR-004**: Harvest Module Consolidation & SQLAlchemy Registry Fix
- **SQLAlchemy Docs**: [Working with Polymorphic Inheritance](https://docs.sqlalchemy.org/en/20/orm/inheritance.html)
- **SQLAlchemy Docs**: [Relationship Configuration](https://docs.sqlalchemy.org/en/20/orm/relationship_api.html)

---

## �📋 Checklist para Code Reviews

### Architecture Compliance
- [ ] ¿Sigue principios SOLID?
- [ ] ¿Dependencies apuntan hacia abstracciones?
- [ ] ¿Clean Architecture layers respetadas?
- [ ] ¿Interfaces bien definidas y específicas?

### Implementation Quality
- [ ] ¿Tests escritos primero (TDD)?
- [ ] ¿Error handling implementado?
- [ ] ¿Multi-tenant scoping aplicado?
- [ ] ¿Resource cleanup (async context managers)?
- [ ] ¿SQLAlchemy imports usan fully-qualified paths?
- [ ] ¿Fixtures usan flush() en lugar de commit()?

### Performance & Security
- [ ] ¿Queries optimizadas?
- [ ] ¿Soft-delete aplicado?
- [ ] ¿No information leakage en errores?
- [ ] ¿Concurrent operations manejadas?

---

## 🔄 Evolución de Guidelines

Estas guidelines evolucionan con el proyecto. Cambios requieren:
1. Discusión en equipo
2. Actualización de este documento  
3. Migration plan para código existente
4. ADR documenting cambio (si es significativo)

---

*Última revisión: 2025-10-05 - Post harvest consolidation & SQLAlchemy registry fix*