# Component Context: Repository Component (Fermentation Management Module)

> **Parent Context**: See `../module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
**Data persistence and retrieval operations** for fermentation and sample entities within the Fermentation Management Module.

**Position in module**: Foundation layer providing data access abstraction to Service Component, enforcing user isolation and referential integrity at persistence level.

## Architecture pattern
**Repository Pattern** with dependency injection and transaction coordination.

**Design approach**: Abstract data access through interfaces with PostgreSQL-specific implementations optimized for time-series fermentation data patterns.

- **Repository Interfaces**: Not defined here. IFermentationRepository, ISampleRepository, and any other repository contracts are defined in the domain component and shared across Service and Repository components.
- **Concrete Repositories**: FermentationRepository, SampleRepository (SQLAlchemy implementations, implement domain interfaces only in this component)
- **Entity Models**: Fermentation, BaseSample with polymorphic inheritance for sample types
- **Data flow**: Service → Repository Interface → Concrete Repository → SQLAlchemy → PostgreSQL
- **Extension points**: Additional repository interfaces, query optimization, caching integration
- **Integration strategy**: Dependency injection provides implementations to Service Component

## Component interfaces

### **Receives from (Service Component)**
- Entity creation/update requests: Validated data ready for persistence
- Query requests: Filtering, pagination, and sorting parameters
- Transaction coordination: Multi-repository operations requiring consistency

### **Provides to (Service Component)**
- Entity instances: Fermentation and sample objects with relationships loaded
- Query results: Paginated collections with metadata
- Operation confirmations: Success/failure status with conflict information

### **Uses (Database Layer)**
- SQLAlchemy ORM: Entity mapping and relationship management
- PostgreSQL connection: ACID transactions and concurrent access
- Connection pooling: Performance optimization for concurrent operations

## Key patterns implemented
- **Repository Pattern**: Abstract persistence concerns from business logic
- **Unit of Work**: Transaction coordination across multiple entities
- **Query Object**: Complex filtering and sorting operations
- **Specification Pattern**: Reusable query conditions for common operations

## Business rules enforced
- **User data isolation**: All queries automatically filter by user context
- **Referential integrity**: Fermentation-sample relationships and constraint enforcement
- **Duplicate detection**: Conflict resolution for sample timestamps and batch operations
- **Soft deletes**: Maintain audit trail while allowing logical deletion

## Connection with other components
**Service Component**: Receives repository interfaces via dependency injection
**Database Layer**: Direct SQLAlchemy ORM integration with PostgreSQL

## Implementation status
- **NOT YET IMPLEMENTED**: Interface contracts defined, ready for implementation
- **Next steps**: ISampleRepository implementation first, then IFermentationRepository
- **Pattern**: Core CRUD operations, then complex queries and optimizations

## Key implementation considerations
- **Async operations**: All methods async for FastAPI compatibility and performance
- **Query optimization**: Time-series queries require indexing strategy for chronological access
- **Transaction management**: Coordinate sample additions with potential analysis triggers
- **Error handling**: Distinguish between constraint violations and system errors