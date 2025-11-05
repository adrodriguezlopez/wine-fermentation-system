# Component Context: Domain Component (Authentication & Authorization Module)

> **Parent Context**: See `../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
Defines the core business model, domain entities, enums, DTOs, and repository interfaces for the Authentication & Authorization Module. Centralizes security contracts, user management rules, and authorization invariants that must be respected by all other components.

**Position in module**: Acts as the foundation for the entire module. All other components (Repository, Service, API) depend on the abstractions and rules defined here, but the domain does not depend on any other component.

## Architecture pattern
- **Domain-Driven Design (DDD)**: Entities, DTOs, enums, errors, and repository interfaces live here.
- **Dependency Inversion Principle**: All dependencies point inward to the domain.
- **Protocol-based Interfaces**: Using Python typing.Protocol for repository contracts.

## Arquitectura específica del componente
- **Entities**: User (en `entities/`)
  - User: Core authentication entity with winery isolation
- **Enums**: UserRole (en `enums/`)
  - UserRole: ADMIN, WINEMAKER, OPERATOR, VIEWER with permission methods
- **DTOs**: 9 data transfer objects (en `dtos.py`)
  - UserContext, LoginRequest, LoginResponse, RefreshTokenRequest
  - UserCreate, UserUpdate, UserResponse
  - PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm
- **Interfaces**: 4 Protocol contracts (en `interfaces/`)
  - IUserRepository: User persistence contract (8 methods)
  - IPasswordService: Password hashing and validation (3 methods)
  - IJwtService: Token encoding/decoding (4 methods)
  - IAuthService: Authentication workflows (10 methods)
- **Errors**: 9 custom exception classes (en `errors.py`)
  - AuthenticationError hierarchy (InvalidCredentials, TokenExpired, InvalidToken)
  - AuthorizationError for permission denials
  - User-specific errors (NotFound, AlreadyExists, Inactive, NotVerified)
- **No lógica de infraestructura**: Solo contratos, reglas y modelos puros.

## Component interfaces

### IUserRepository (Protocol)
**Contract for user persistence operations:**
- `create(user: User) -> User`: Create new user with duplicate checking
- `get_by_id(user_id: int) -> Optional[User]`: Retrieve by ID (excludes deleted)
- `get_by_email(email: str) -> Optional[User]`: Retrieve by email (excludes deleted)
- `get_by_username(username: str) -> Optional[User]`: Retrieve by username (excludes deleted)
- `update(user: User) -> User`: Update existing user with timestamp
- `delete(user_id: int) -> bool`: Soft delete user (sets deleted_at)
- `exists_by_email(email: str) -> bool`: Check email uniqueness
- `exists_by_username(username: str) -> bool`: Check username uniqueness

### IPasswordService (Protocol)
**Contract for password security operations:**
- `hash_password(password: str) -> str`: Hash password with bcrypt
- `verify_password(plain: str, hashed: str) -> bool`: Verify password match
- `validate_password_strength(password: str) -> bool`: Check minimum requirements

### IJwtService (Protocol)
**Contract for JWT token operations:**
- `encode_access_token(user_context: UserContext) -> str`: Create access token
- `encode_refresh_token(user_id: int) -> str`: Create refresh token
- `decode_token(token: str) -> dict`: Decode and validate token
- `extract_user_context(token: str) -> UserContext`: Extract user from token

### IAuthService (Protocol)
**Contract for authentication workflows:**
- `login(request: LoginRequest) -> LoginResponse`: Authenticate user
- `refresh_access_token(request: RefreshTokenRequest) -> LoginResponse`: Refresh tokens
- `register_user(data: UserCreate) -> UserResponse`: Create new user account
- `verify_token(token: str) -> UserContext`: Validate and extract context
- `get_user(user_id: int) -> UserResponse`: Get user by ID
- `update_user(user_id: int, data: UserUpdate) -> UserResponse`: Update user
- `change_password(user_id: int, request: PasswordChangeRequest) -> bool`: Change password
- `request_password_reset(request: PasswordResetRequest) -> bool`: Request reset email
- `confirm_password_reset(request: PasswordResetConfirm) -> bool`: Complete reset
- `deactivate_user(user_id: int) -> bool`: Deactivate account

## Business rules enforced

### User Entity Rules
- **Email uniqueness**: No two active users can share the same email
- **Username uniqueness**: No two active users can share the same username
- **Soft deletes**: Deleted users have `deleted_at` set, not physically removed
- **Timestamps**: `created_at` and `updated_at` managed automatically
- **Role defaults**: New users default to VIEWER role
- **Winery isolation**: All users belong to exactly one winery

### Role Permissions
- **ADMIN**: Can manage users, write/modify all data
- **WINEMAKER**: Can write fermentations and samples
- **OPERATOR**: Can write samples only
- **VIEWER**: Read-only access

### Authentication Rules
- **Password hashing**: All passwords stored as bcrypt hashes (12 rounds)
- **Token expiration**: Access tokens expire in 15 minutes
- **Refresh tokens**: Valid for 7 days
- **Account verification**: Users must verify email before full access
- **Active accounts**: Only active users can authenticate

### Authorization Rules
- **is_authenticated**: User must be active AND verified
- **Role checks**: Hierarchical permission model
- **Winery scope**: Users only access data from their winery

## Connection with other components
- **Repository Component (infra)**: Implements IUserRepository for data persistence
- **Service Component (future)**: Implements IPasswordService, IJwtService, IAuthService for business logic
- **API Component (future)**: Uses DTOs for request/response validation

## Implementation status

**Status:** ✅ **Domain Layer Complete (81 tests passing)**
**Last Updated:** 2025-10-28
**Reference:** ADR-007 Phase 1

### Completed Components

**✅ User Entity**
- Fields: id, username, email, password_hash, full_name, winery_id, role, is_active, is_verified, last_login_at, deleted_at
- Relationships: fermentations, samples (lazy="raise" to prevent N+1 queries)
- Properties: is_authenticated (checks is_active AND is_verified)
- Inheritance: BaseEntity (created_at, updated_at)

**✅ UserRole Enum (11 tests passing)**
- 4 roles: ADMIN, WINEMAKER, OPERATOR, VIEWER
- Permission methods: can_manage_users(), can_write_fermentations(), can_write_samples(), can_modify_samples()
- String inheritance for JSON serialization

**✅ DTOs (17 tests passing, 1 skipped)**
- UserContext: Immutable frozen dataclass for request context
- LoginRequest/Response: Authentication flow
- RefreshTokenRequest: Token refresh
- UserCreate/Update/Response: User management
- PasswordChangeRequest/ResetRequest/ResetConfirm: Password workflows
- Test coverage: Creation, validation, immutability, role checking

**✅ Interfaces (30 tests passing)**
- IUserRepository: 8 methods, Protocol type validation
- IPasswordService: 3 methods, Protocol type validation
- IJwtService: 4 methods, Protocol type validation
- IAuthService: 10 methods, Protocol type validation
- Test coverage: Protocol detection, method signatures, return types

**✅ Errors (22 tests passing)**
- 9 custom exception classes with proper hierarchy
- Test coverage: Messages, inheritance, field access, exception chaining
- Hierarchy: AuthenticationError → InvalidCredentials, TokenExpired, InvalidToken
- Separate: AuthorizationError, UserNotFoundError, UserAlreadyExistsError, UserInactiveError, UserNotVerifiedError

### Test Summary
- **Total**: 81 tests (80 passed, 1 skipped)
- **Execution time**: 0.19s
- **Skipped**: test_from_entity (deferred to integration tests - requires fermentation module)

## Key implementation considerations
- El dominio nunca debe depender de infraestructura ni frameworks externos.
- Todas las reglas críticas deben estar aquí para garantizar la integridad del sistema.
- Passwords nunca se exponen en DTOs, solo password_hash en UserResponse.
- Soft deletes preservan audit trail y permiten recuperación.
- Lazy loading con "raise" previene N+1 queries accidentales.
- Protocol interfaces permiten duck typing y testing flexible.

## Design decisions

### Why Protocol instead of ABC?
- More Pythonic for structural subtyping
- Allows duck typing without explicit inheritance
- Better for testing with mocks
- Follows modern Python typing patterns

### Why soft deletes?
- Preserve audit trail for compliance
- Allow data recovery if needed
- Maintain referential integrity
- Support undo operations

### Why lazy="raise" for relationships?
- Prevents accidental N+1 query problems
- Forces explicit relationship loading
- Better performance visibility
- Encourages proper query design

### Why immutable UserContext?
- Thread-safe for async operations
- Prevents accidental mutations
- Clear data flow in request handling
- Easier to reason about state
