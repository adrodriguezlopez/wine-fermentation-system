# Component Context: Infrastructure Component (Authentication & Authorization Module)

> **Parent Context**: See `../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
**Data persistence and retrieval operations** for user entities within the Authentication & Authorization Module.

**Position in module**: Foundation layer providing data access abstraction to Service Component (future), enforcing user uniqueness and soft delete patterns at persistence level.

**Architectural Decision:** Following ADR-007, this component implements the repository pattern with PostgreSQL-specific optimizations for user queries and authentication lookups.

## Architecture pattern
**Repository Pattern** with async SQLAlchemy and dependency injection.

**Design approach**: Abstract data access through IUserRepository interface with PostgreSQL-specific implementations optimized for authentication query patterns.

- **Repository Interface**: IUserRepository defined in domain component (8 async methods)
- **Concrete Repository**: UserRepository (SQLAlchemy implementation in this component)
- **Entity Model**: User entity from domain with SQLAlchemy mappings
- **Data flow**: Service → IUserRepository → UserRepository → SQLAlchemy AsyncSession → PostgreSQL
- **Extension points**: Caching layer, read replicas, audit logging
- **Integration strategy**: Dependency injection provides implementations to Service Component

## Component interfaces

### **Receives from (Service Component - future)**
- User creation requests: Validated UserCreate data ready for persistence
- Query requests: Lookup by ID, email, username
- Update requests: User modifications with validation
- Soft delete requests: Account deactivation

### **Provides to (Service Component - future)**
- User instances: Complete user objects with all fields
- Existence checks: Email/username uniqueness validation
- Query results: Single user or None for lookups
- Operation confirmations: Success (User/bool) or exceptions

### **Uses (Database Layer)**
- SQLAlchemy AsyncSession: Async ORM operations
- PostgreSQL connection: ACID transactions and concurrent access
- Connection pooling: Performance optimization for concurrent operations

## Key patterns implemented
- **Repository Pattern**: Abstract persistence concerns from business logic
- **Async/Await**: Non-blocking database operations with AsyncSession
- **Query Optimization**: Use of `scalar_one_or_none()` for single results, `func.count()` for existence checks
- **Soft Deletes**: Filter `deleted_at IS NULL` in all queries
- **Timestamp Management**: Automatic `created_at`, `updated_at`, `deleted_at` handling

## Business rules enforced
- **Email uniqueness**: Check `exists_by_email()` before creation
- **Username uniqueness**: Check `exists_by_username()` before creation
- **Soft delete filtering**: All queries exclude records where `deleted_at IS NOT NULL`
- **Timestamp integrity**: Set `created_at`/`updated_at` on create, update `updated_at` on modify
- **Referential integrity**: User-Fermentation-Sample relationships (via lazy="raise")

## Connection with other components
**Service Component (future)**: Receives IUserRepository implementation via dependency injection
**Domain Component**: Implements IUserRepository interface, uses User entity
**Database Layer**: Direct SQLAlchemy AsyncSession integration with PostgreSQL

## Implementation status

**Status:** ✅ **Repository Layer Complete (21 tests passing)**  
**Last Updated:** 2025-10-28  
**Reference:** ADR-007 Phase 2

**Note:** This component is production-ready for service layer usage. Service layer integration is next phase.

### Implemented Components

**UserRepository** ✅ COMPLETE
- **Location**: `infra/repositories/user_repository.py`
- **Methods**: 8 async methods (100% interface coverage)
  - ✅ `create(user: User) -> User` - Create with duplicate checking, timestamp setting
  - ✅ `get_by_id(user_id: UUID) -> Optional[User]` - Retrieve by ID, exclude soft-deleted
  - ✅ `get_by_email(email: str) -> Optional[User]` - Retrieve by email, exclude soft-deleted
  - ✅ `get_by_username(username: str) -> Optional[User]` - Retrieve by username, exclude soft-deleted
  - ✅ `update(user: User) -> User` - Update with validation and timestamp
  - ✅ `delete(user_id: UUID) -> bool` - Soft delete (sets deleted_at), returns False if not found
  - ✅ `exists_by_email(email: str) -> bool` - Efficient count-based existence check
  - ✅ `exists_by_username(username: str) -> bool` - Efficient count-based existence check
- **Tests**: 21 passing (100% coverage of implementation)
- **Status**: Fully implemented with AsyncSession integration
- **Compliance**: Implements IUserRepository Protocol exactly

### Test Coverage Breakdown

**TestUserRepositoryCreate (4 tests)**
- ✅ test_create_user_success - Happy path with timestamp verification
- ✅ test_create_user_duplicate_email - Raises UserAlreadyExistsError("email", value)
- ✅ test_create_user_duplicate_username - Raises UserAlreadyExistsError("username", value)
- ✅ test_create_sets_timestamps - Verifies created_at, updated_at, ID assignment

**TestUserRepositoryGetById (3 tests)**
- ✅ test_get_by_id_found - Returns user when exists
- ✅ test_get_by_id_not_found - Returns None when not exists
- ✅ test_get_by_id_excludes_soft_deleted - Filters deleted_at IS NOT NULL

**TestUserRepositoryGetByEmail (2 tests)**
- ✅ test_get_by_email_found - Returns user when exists
- ✅ test_get_by_email_not_found - Returns None when not exists

**TestUserRepositoryGetByUsername (2 tests)**
- ✅ test_get_by_username_found - Returns user when exists
- ✅ test_get_by_username_not_found - Returns None when not exists

**TestUserRepositoryUpdate (2 tests)**
- ✅ test_update_user_success - Updates and commits successfully
- ✅ test_update_sets_updated_at - Modifies updated_at timestamp

**TestUserRepositoryDelete (3 tests)**
- ✅ test_delete_user_success - Soft deletes and returns True
- ✅ test_delete_user_not_found - Returns False when user doesn't exist
- ✅ test_delete_sets_deleted_at - Sets deleted_at timestamp on user object

**TestUserRepositoryExists (4 tests)**
- ✅ test_exists_by_email_true - Returns True when email exists
- ✅ test_exists_by_email_false - Returns False when email doesn't exist
- ✅ test_exists_by_username_true - Returns True when username exists
- ✅ test_exists_by_username_false - Returns False when username doesn't exist

**TestUserRepositoryIntegration (1 test)**
- ✅ test_repository_implements_interface - Validates Protocol compliance

**Total: 21 tests passing (0.28s execution time)**

## Implementation details

### create() method
```python
async def create(self, user: User) -> User:
    # 1. Check email uniqueness (calls exists_by_email)
    # 2. Check username uniqueness (calls exists_by_username)
    # 3. Set timestamps (created_at, updated_at = now)
    # 4. Add to session, commit, refresh
    # 5. Return persisted user with ID
    # Raises: UserAlreadyExistsError("email"|"username", value)
```

### Query methods (get_by_*)
```python
async def get_by_id/email/username(...) -> Optional[User]:
    # 1. Build SELECT with WHERE clause
    # 2. Filter: deleted_at IS NULL (soft delete filtering)
    # 3. Execute query with scalar_one_or_none()
    # 4. Return user or None
```

### update() method
```python
async def update(self, user: User) -> User:
    # 1. Verify user exists (calls get_by_id)
    # 2. Raise UserNotFoundError if not found
    # 3. Update user.updated_at = now
    # 4. Merge changes, commit, refresh
    # 5. Return updated user
```

### delete() method
```python
async def delete(self, user_id: UUID) -> bool:
    # 1. Verify user exists (calls get_by_id)
    # 2. Return False if not found (no exception)
    # 3. Set user.deleted_at = now (on object and in UPDATE)
    # 4. Execute UPDATE, commit
    # 5. Return True
```

### exists_by_*() methods
```python
async def exists_by_email/username(...) -> bool:
    # 1. SELECT COUNT(id) WHERE field = value AND deleted_at IS NULL
    # 2. Execute and get scalar result
    # 3. Return count > 0
    # Performance: Uses COUNT instead of fetching full entity
```

## Key implementation considerations

### SQLAlchemy AsyncSession Integration
- All methods are async for non-blocking I/O
- Use `await session.execute()` for all queries
- Proper use of `commit()`, `refresh()`, `merge()` for state management
- `scalar_one_or_none()` for single result queries
- `scalar()` for aggregate queries (COUNT)

### Soft Delete Pattern
- All queries include `WHERE deleted_at IS NULL` filter
- `delete()` sets timestamp instead of removing record
- Returns bool instead of raising exception on not found
- Preserves referential integrity and audit trail

### Error Handling
- Raises `UserAlreadyExistsError(field, value)` on duplicates
- Raises `UserNotFoundError(identifier)` on update of non-existent user
- Returns `False` from delete() instead of exception
- Proper error context for debugging

### Performance Optimizations
- Use `func.count()` for existence checks (faster than fetching entities)
- Use `scalar_one_or_none()` instead of `scalars().first()` (clearer intent)
- Index on email and username columns (defined in User entity)
- Avoid N+1 queries with lazy="raise" on relationships

### Testing Strategy
- **Unit tests**: Mock AsyncSession with AsyncMock and Mock
- **Mock patterns**: 
  - `scalar_one_or_none.return_value` for entity queries
  - `scalar.return_value` for count queries
  - `side_effect` for simulating database ID assignment
- **Test isolation**: Each test mocks only what it needs
- **Integration tests**: Deferred to Phase 5 with real database

## Design decisions

### Why scalar_one_or_none() instead of scalars().first()?
- More explicit about expecting single result
- Raises exception if multiple results (catches bugs)
- Clearer semantic intent
- Standard SQLAlchemy 2.0 pattern

### Why return False from delete() instead of raising?
- Interface contract specifies bool return
- Allows service layer to decide error handling
- Simpler for "delete if exists" use cases
- Consistent with REST DELETE idempotency

### Why check existence before create?
- Provide better error messages (field-specific)
- Avoid database constraint violation errors
- Support early validation in service layer
- Enable atomic check-and-insert patterns

### Why soft deletes?
- Preserve audit trail for compliance
- Maintain referential integrity with fermentations
- Allow account recovery if needed
- Support user reactivation workflows

## Next steps

**Phase 3: Service Layer**
1. Implement PasswordService (bcrypt hashing)
2. Implement JwtService (token encoding/decoding)
3. Implement AuthService (orchestrates repository + services)
4. Write service tests FIRST (TDD)
5. Wire dependencies with dependency injection

**Integration Points:**
- AuthService will receive UserRepository via constructor injection
- Services will coordinate repository calls with business logic
- Error mapping from repository to service layer
- Transaction coordination for multi-step operations
