# ADR-002 Repository Architecture - Implementation Plan

## Overview

This document provides a detailed implementation plan for ADR-002 Repository Architecture based on comprehensive analysis of the current codebase state.

## Current State Analysis

### ✅ Completed Components

**Domain Interfaces (100% Complete)**
- `IFermentationRepository` - Fully defined with async CRUD operations
- `ISampleRepository` - Complete interface with error handling patterns
- Location: `src/domain/fermentation/interfaces/`
- Status: Ready for implementation

**Entity Layer (100% Complete)**
- `Fermentation` entity with complete ORM mappings
- `BaseSample` entity with inheritance patterns
- `FermentationLotSource` association entity
- `User` entity with relationships
- All database constraints implemented (UNIQUE, CHECK, FK)
- Location: `src/domain/fermentation/entities/`
- Status: 63 unit tests passing, production ready

### 🔧 Infrastructure Gap (0% Complete)

**Missing Repository Components**
- `repository_component/` directory exists but only contains `__init__.py`
- No concrete repository implementations
- No BaseRepository foundation
- No Unit of Work implementation
- No error mapping infrastructure

## Critical Issues to Resolve

### 1. Missing Infrastructure Dependencies

**Database Configuration**
- No SQLAlchemy session management
- No connection configuration  
- No database URL handling

**Error Infrastructure**
- Missing `RepositoryError` hierarchy
- No error code mapping
- No PostgreSQL SQLSTATE handling

**Optimistic Locking**
- Missing `version` field in Fermentation entity
- No concurrency control implementation

## 5-Phase Implementation Plan

### Phase 1: Foundation Setup (1-2 days)

**Step 1.1: Database Configuration**
```python
# File: src/infrastructure/database/config.py
class DatabaseConfig:
    def __init__(self):
        self.url = os.getenv('DATABASE_URL')
        self.echo = os.getenv('DB_ECHO', 'false').lower() == 'true'
    
    def create_engine(self):
        return create_async_engine(self.url, echo=self.echo)
```

**Step 1.2: Session Management**
```python
# File: src/infrastructure/database/session.py
class DatabaseSession:
    def __init__(self, engine):
        self.session_factory = async_sessionmaker(engine)
    
    async def get_session(self):
        async with self.session_factory() as session:
            yield session
```

**Step 1.3: Error Infrastructure**
```python
# File: src/infrastructure/repository_component/errors.py
class RepositoryError(Exception):
    """Base repository error"""
    
class EntityNotFoundError(RepositoryError):
    """Entity not found in repository"""
    
class OptimisticLockError(RepositoryError):
    """Optimistic locking conflict"""
    
class DatabaseConnectionError(RepositoryError):
    """Database connection issues"""
```

### Phase 2: BaseRepository Implementation (2-3 days)

**Step 2.1: Generic BaseRepository**
```python
# File: src/infrastructure/repository_component/base_repository.py
from typing import TypeVar, Generic, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, entity_class: type[T]):
        self.session = session
        self.entity_class = entity_class
    
    async def get_by_id(self, id: int) -> Optional[T]:
        result = await self.session.get(self.entity_class, id)
        return result
    
    async def create(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity
    
    async def update(self, entity: T) -> T:
        await self.session.merge(entity)
        return entity
    
    async def delete(self, id: int) -> bool:
        entity = await self.get_by_id(id)
        if entity:
            await self.session.delete(entity)
            return True
        return False
```

**Step 2.2: Multi-tenant Scoping**
```python
# Add to BaseRepository
def _apply_tenant_filter(self, query, user_id: int):
    if hasattr(self.entity_class, 'user_id'):
        return query.where(self.entity_class.user_id == user_id)
    return query
```

**Step 2.3: Error Mapping**
```python
# Add to BaseRepository
def _map_database_error(self, error: Exception) -> RepositoryError:
    if isinstance(error, IntegrityError):
        if '23505' in str(error):  # unique_violation
            return UniqueConstraintError(str(error))
        elif '23503' in str(error):  # foreign_key_violation
            return ForeignKeyError(str(error))
    return DatabaseError(str(error))
```

### Phase 3: Concrete Repository Implementations (2-3 days)

**Step 3.1: FermentationRepository**
```python
# File: src/infrastructure/repository_component/fermentation_repository.py
class FermentationRepository(BaseRepository[Fermentation], IFermentationRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Fermentation)
    
    async def get_by_batch_number(self, batch_number: str, user_id: int) -> Optional[Fermentation]:
        query = select(Fermentation).where(
            Fermentation.batch_number == batch_number,
            Fermentation.user_id == user_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_fermentations(self, user_id: int) -> List[Fermentation]:
        query = select(Fermentation).where(
            Fermentation.user_id == user_id,
            Fermentation.end_date.is_(None)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
```

**Step 3.2: SampleRepository**
```python
# File: src/infrastructure/repository_component/sample_repository.py
class SampleRepository(BaseRepository[BaseSample], ISampleRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, BaseSample)
    
    async def get_by_fermentation(self, fermentation_id: int, user_id: int) -> List[BaseSample]:
        query = select(BaseSample).where(
            BaseSample.fermentation_id == fermentation_id,
            BaseSample.user_id == user_id
        ).order_by(BaseSample.sampling_date.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
```

### Phase 4: Unit of Work Implementation (1-2 days)

**Step 4.1: UnitOfWork Pattern**
```python
# File: src/infrastructure/repository_component/unit_of_work.py
class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._session = None
        self._fermentation_repository = None
        self._sample_repository = None
    
    async def __aenter__(self):
        self._session = self.session_factory()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self._session.rollback()
        await self._session.close()
    
    @property
    def fermentation_repository(self) -> IFermentationRepository:
        if not self._fermentation_repository:
            self._fermentation_repository = FermentationRepository(self._session)
        return self._fermentation_repository
    
    @property
    def sample_repository(self) -> ISampleRepository:
        if not self._sample_repository:
            self._sample_repository = SampleRepository(self._session)
        return self._sample_repository
    
    async def commit(self):
        await self._session.commit()
    
    async def rollback(self):
        await self._session.rollback()
```

### Phase 5: Read Models & Optimization (1-2 days)

**Step 5.1: Read-Only Repository**
```python
# File: src/infrastructure/repository_component/read_models.py
class FermentationReadModel:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_fermentation_summary(self, user_id: int) -> List[Dict[str, Any]]:
        query = text("""
            SELECT f.id, f.batch_number, f.start_date, f.end_date,
                   COUNT(s.id) as sample_count,
                   MAX(s.sampling_date) as last_sample_date
            FROM fermentations f
            LEFT JOIN samples s ON f.id = s.fermentation_id
            WHERE f.user_id = :user_id
            GROUP BY f.id, f.batch_number, f.start_date, f.end_date
            ORDER BY f.start_date DESC
        """)
        result = await self.session.execute(query, {"user_id": user_id})
        return [dict(row) for row in result]
```

## Implementation Priorities

### Critical Path Items
1. **Add optimistic locking field** to Fermentation entity
2. **Database configuration setup** (Docker PostgreSQL integration)
3. **Error infrastructure implementation**

### High Priority
1. BaseRepository implementation
2. Concrete repository implementations
3. Unit of Work pattern

### Medium Priority
1. Unit of Work pattern
2. Performance optimizations
3. Read model implementations

## Testing Strategy

### Unit Tests Structure
```
tests/
├── infrastructure/
│   ├── repository_component/
│   │   ├── test_base_repository.py
│   │   ├── test_fermentation_repository.py
│   │   ├── test_sample_repository.py
│   │   └── test_unit_of_work.py
│   └── database/
│       ├── test_config.py
│       └── test_session.py
```

### Integration Tests
- Database connectivity
- Repository CRUD operations
- Transaction management
- Error handling scenarios

## Database Migration Requirements

### 1. Add Optimistic Locking
```sql
-- Migration: Add version field for optimistic locking
ALTER TABLE fermentations ADD COLUMN version INTEGER DEFAULT 0 NOT NULL;
```

### 2. Performance Indexes
```sql
-- Optimize common queries
CREATE INDEX idx_fermentations_user_batch ON fermentations(user_id, batch_number);
CREATE INDEX idx_fermentations_user_active ON fermentations(user_id, end_date) WHERE end_date IS NULL;
CREATE INDEX idx_samples_fermentation_date ON samples(fermentation_id, sampling_date DESC);
```

## Configuration Management

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/wine_fermentation
DB_ECHO=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Application Configuration
TENANT_ISOLATION=true
OPTIMISTIC_LOCKING=true
```

### Settings Class
```python
# File: src/infrastructure/config/settings.py
class RepositorySettings:
    database_url: str
    echo_sql: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    tenant_isolation: bool = True
    optimistic_locking: bool = True
```

## Risk Mitigation

### Technical Risks
1. **Return Type Inconsistency**: Must be resolved before implementation
2. **Database Migration**: Require downtime for optimistic locking field
3. **Performance Impact**: Lazy loading vs eager loading strategy needed

### Implementation Risks
1. **Complex Transactions**: Unit of Work pattern adds complexity
2. **Error Handling**: PostgreSQL error code mapping requires testing
3. **Multi-tenancy**: Security implications of user scoping

## Success Criteria

### Functional Requirements
- [ ] All repository interfaces implemented
- [ ] Unit of Work pattern functional
- [ ] Error handling comprehensive
- [ ] Multi-tenant data isolation

### Non-Functional Requirements
- [ ] All existing tests pass (currently 63)
- [ ] New repository tests achieve >90% coverage
- [ ] Performance baseline maintained
- [ ] Zero data corruption during migration

## Timeline Estimate

**Total Duration**: 8-12 days

- Phase 1 (Foundation): 1-2 days
- Phase 2 (BaseRepository): 2-3 days  
- Phase 3 (Implementations): 2-3 days
- Phase 4 (Unit of Work): 1-2 days
- Phase 5 (Read Models): 1-2 days

**Critical Dependencies**: Return type resolution must happen before Phase 2 begins.

## Next Steps

1. **Database Setup**: Configure connection to Docker PostgreSQL instance
2. **Entity Update**: Add optimistic locking field to Fermentation
3. **Begin Phase 1**: Foundation infrastructure implementation
4. **Docker Integration**: Ensure PostgreSQL container is properly configured

---

*This implementation plan is based on analysis of the current codebase state. All 63 existing tests are passing, and return type consistency has been resolved.*