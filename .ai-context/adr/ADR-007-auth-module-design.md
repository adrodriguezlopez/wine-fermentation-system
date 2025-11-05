# ADR-007: Authentication Module Design (Shared Infrastructure)

**Status:** ✅ **IMPLEMENTED** (Nov 4, 2025)  
**Date Created:** 2025-10-26  
**Date Implemented:** 2025-11-04  
**Deciders:** Development Team  
**Related ADRs:** ADR-006 (API Layer - depends on this)

> **📋 Context Files:**
> - [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md) - Principios de diseño
> - [Project Context](../project-context.md) - Módulos del sistema

---

## Context

El sistema requiere **autenticación y autorización** para todos los módulos (fermentation, winery, fruit_origin, future modules). Actualmente:

1. **User entity existe en lugar INCORRECTO** - Está en `modules/fermentation/src/domain/entities/user.py` pero debería ser shared infrastructure
2. **NO existe módulo de autenticación completo** - Solo User entity, falta repository, services, JWT
3. **API Layer bloqueada** - ADR-006 no puede implementarse sin auth completo
4. **Multi-tenancy sin enforcement** - `winery_id` en services pero sin validación HTTP vía JWT
5. **No hay JWT infrastructure** - Token generation/validation faltante
6. **Arquitectura inconsistente** - Otros módulos (winery, fruit_origin) no pueden importar User sin depender de fermentation

**Requirements identificados:**
- Autenticación JWT stateless (microservices-ready)
- Multi-tenancy enforcement (winery_id en token)
- Role-based authorization (Admin, Winemaker, Operator, Viewer)
- User management (CRUD usuarios por winery)
- Password hashing seguro (bcrypt/argon2)
- Token refresh mechanism
- FastAPI dependencies reusables (`get_current_user`, `require_role`)

**Decisión**: 
1. **Migrar** User entity desde `modules/fermentation/` a `shared/auth/` (corrección arquitectural)
2. **Implementar** Auth Module completo como **shared infrastructure** antes de API layers

---

## Decision

### 1. Module Location & Structure

**Location:** `src/shared/auth/` (NOT a domain module, it's infrastructure)

```
src/shared/auth/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   └── user.py                    # User entity (SQLAlchemy)
│   ├── dtos/
│   │   ├── __init__.py
│   │   ├── user_context.py            # UserContext (JWT claims)
│   │   ├── login_dto.py               # LoginRequest/Response
│   │   ├── token_dto.py               # TokenPair (access + refresh)
│   │   └── user_dto.py                # UserCreate, UserUpdate, UserResponse
│   ├── enums/
│   │   ├── __init__.py
│   │   └── user_role.py               # UserRole enum
│   └── interfaces/
│       ├── __init__.py
│       ├── user_repository_interface.py
│       └── auth_service_interface.py
├── repository/
│   ├── __init__.py
│   └── user_repository.py             # SQLAlchemy implementation
├── service/
│   ├── __init__.py
│   ├── auth_service.py                # Login, logout, register
│   ├── jwt_service.py                 # Token encode/decode/validate
│   └── password_service.py            # Hashing, verification
├── dependencies/
│   ├── __init__.py
│   └── auth_dependencies.py           # FastAPI dependencies
├── errors.py                          # Auth-specific exceptions
└── config.py                          # JWT config (secret, expiry)
```

### 2. User Entity Design (Migration from Existing)

**Current Location (INCORRECT):** `src/modules/fermentation/src/domain/entities/user.py`  
**New Location (CORRECT):** `src/shared/auth/domain/entities/user.py`

**Existing Entity (will be migrated):**
```python
class User(BaseEntity):
    """User entity for authentication and authorization"""
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}  # Keep for testing
    
    # Identity (EXISTING - keep as-is)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile (EXISTING - keep as-is)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    winery_id: Mapped[int] = mapped_column(ForeignKey("wineries.id"), nullable=False)
    
    # Authorization (EXISTING - keep as-is)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Audit (EXISTING - rename last_login → last_login_at for consistency)
    last_login: Mapped[Optional[datetime]] = mapped_column(nullable=True)  # Rename to last_login_at
    
    # NEW FIELDS TO ADD:
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="viewer")  # ADD: UserRole enum
    # NOTE: `created_at` / `updated_at` are provided by BaseEntity - do NOT duplicate here.
    
    # Relationships (EXISTING - update after migration)
    # Will need to update fully-qualified paths after migration
```

**Changes Required:**
- ✅ **Move file** to shared/auth/domain/entities/
- ✅ **Add `role` field** (String, default="viewer")
- ✅ **Rename `last_login`** → `last_login_at` (consistency)
- ✅ **Update relationship imports** (from fermentation module entities)
- ✅ **Update all imports** across fermentation module

**Key Decisions:**
- ✅ Email + Username already implemented correctly
- ✅ Password hash stored (NEVER plaintext) - already correct
- ✅ Multi-tenancy via `winery_id` FK - already correct
- ✅ Role-based authorization (enum) - **TO ADD**
- ✅ Soft delete support (inherited from BaseEntity) - already correct
- ✅ Last login tracking - already exists, just rename

### 3. UserRole Enum (NEW - To be created)

**Location:** `src/shared/auth/domain/enums/user_role.py`

```python
class UserRole(str, Enum):
    """User roles for authorization"""
    ADMIN = "admin"              # System admin, all permissions
    WINEMAKER = "winemaker"      # Manage fermentations, samples, reports
    OPERATOR = "operator"        # Read fermentations, add samples
    VIEWER = "viewer"            # Read-only access (DEFAULT for new users)
```

**Why Enum instead of separate table:**
- ✅ **MVP simplicity**: 4 static roles, no per-winery customization needed
- ✅ **Performance**: No JOIN on every auth check
- ✅ **Type safety**: Enum provides compile-time validation
- ✅ **Stored as string** in User.role column
- 🔄 **Future**: If role customization needed, migrate to Permission-based ACL table

**Permission Matrix:**
| Action | Admin | Winemaker | Operator | Viewer |
|--------|-------|-----------|----------|--------|
| Create Fermentation | ✅ | ✅ | ❌ | ❌ |
| Update Fermentation | ✅ | ✅ | ❌ | ❌ |
| Delete Fermentation | ✅ | ✅ | ❌ | ❌ |
| Read Fermentation | ✅ | ✅ | ✅ | ✅ |
| Add Sample | ✅ | ✅ | ✅ | ❌ |
| Manage Users | ✅ | ❌ | ❌ | ❌ |

### 4. JWT Token Design

**Token Structure:**
```json
{
  "user_id": 123,
  "winery_id": 1,
  "email": "winemaker@bodega.com",
  "role": "winemaker",
  "exp": 1730000000,
  "iat": 1729999000,
  "jti": "unique-token-id"
}
```

**Token Types:**
- **Access Token**: 15 minutos expiry, used for API requests
- **Refresh Token**: 7 días expiry, used to get new access token

**Security:**
- Algorithm: HS256 (HMAC SHA-256)
- Secret: Environment variable `JWT_SECRET` (min 32 chars)
- Token blacklist: Redis (future) for logout/revocation

### 5. DTOs Design

**UserContext (JWT Claims):**
```python
@dataclass
class UserContext:
    """User context extracted from JWT token"""
    user_id: int
    winery_id: int
    email: str
    role: UserRole
    permissions: List[str]  # Derived from role
```

**Login DTOs:**
```python
@dataclass
class LoginRequest:
    email: str
    password: str

@dataclass
class LoginResponse:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes
    user: UserResponse
```

**User DTOs:**
```python
@dataclass
class UserCreate:
    email: str
    username: str
    password: str
    full_name: str
    winery_id: int
    role: UserRole

@dataclass
class UserUpdate:
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

@dataclass
class UserResponse:
    id: int
    email: str
    username: str
    full_name: str
    winery_id: int
    role: UserRole
    is_active: bool
    last_login_at: Optional[datetime]
```

### 6. Service Interfaces

**IAuthService:**
```python
class IAuthService(ABC):
    """Authentication service interface"""
    
    @abstractmethod
    async def login(self, email: str, password: str) -> LoginResponse:
        """Authenticate user and return tokens"""
        
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """Generate new access token from refresh token"""
        
    @abstractmethod
    async def logout(self, user_id: int, token: str) -> bool:
        """Invalidate user tokens (future: blacklist)"""
        
    @abstractmethod
    async def verify_token(self, token: str) -> UserContext:
        """Validate token and extract user context"""
        
    @abstractmethod
    async def register_user(self, data: UserCreate, created_by: int) -> User:
        """Create new user (admin only)"""

    @abstractmethod
    async def update_user(self, user_id: int, data: UserUpdate, updated_by: int) -> User:
        """Update user profile or role (admin/manager)"""

    @abstractmethod
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change password when user provides old password"""

    @abstractmethod
    async def request_password_reset(self, email: str) -> bool:
        """Initiate password reset (send email with token)"""

    @abstractmethod
    async def confirm_password_reset(self, token: str, new_password: str) -> bool:
        """Complete password reset using token"""

    @abstractmethod
    async def deactivate_user(self, user_id: int, by_user_id: int) -> bool:
        """Deactivate (soft-delete) a user account"""
```

**IJwtService:**
```python
class IJwtService(ABC):
    """JWT token management interface"""
    
    @abstractmethod
    def encode_token(self, payload: Dict[str, Any], expires_delta: timedelta) -> str:
        """Generate JWT token"""
        
    @abstractmethod
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        
    @abstractmethod
    def create_access_token(self, user: User) -> str:
        """Create access token for user"""
        
    @abstractmethod
    def create_refresh_token(self, user: User) -> str:
        """Create refresh token for user"""
```

**IPasswordService:**
```python
class IPasswordService(ABC):
    """Password hashing and verification interface"""
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt/argon2"""
        
    @abstractmethod
    def verify_password(self, password: str, hash: str) -> bool:
        """Verify password against hash"""
```

### 7. FastAPI Dependencies

**Core Dependencies:**
```python
# dependencies/auth_dependencies.py

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: IAuthService = Depends(get_auth_service)
) -> UserContext:
    """Extract and validate user from JWT token"""
    try:
        user_context = await auth_service.verify_token(token)
        return user_context
    except JwtDecodeError:
        raise HTTPException(401, "Invalid token")
    except JwtExpiredError:
        raise HTTPException(401, "Token expired")

def require_role(*allowed_roles: UserRole):
    """Decorator to require specific roles"""
    async def role_checker(
        user: UserContext = Depends(get_current_user)
    ) -> UserContext:
        if user.role not in allowed_roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return role_checker

async def get_current_active_user(
    user: UserContext = Depends(get_current_user)
) -> UserContext:
    """Ensure user is active"""
    # Check is_active in DB if needed
    return user
```

**Usage Examples:**
```python
# Require authentication
@router.get("/profile")
async def get_profile(user: UserContext = Depends(get_current_user)):
    return user

# Require specific role
@router.post("/fermentations")
async def create_fermentation(
    user: UserContext = Depends(require_role(UserRole.ADMIN, UserRole.WINEMAKER))
):
    ...

# Admin only
@router.post("/users")
async def create_user(
    user: UserContext = Depends(require_role(UserRole.ADMIN))
):
    ...
```

### 8. Error Handling

**Custom Exceptions:**
```python
class AuthenticationError(Exception):
    """Base authentication error"""

class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password"""

class UserNotFoundError(AuthenticationError):
    """User does not exist"""

class UserInactiveError(AuthenticationError):
    """User account is deactivated"""

class JwtDecodeError(AuthenticationError):
    """JWT token decode failed"""

class JwtExpiredError(AuthenticationError):
    """JWT token expired"""

class InsufficientPermissionsError(AuthenticationError):
    """User lacks required permissions"""
```

**HTTP Mapping:**
```python
InvalidCredentialsError     → 401 Unauthorized
UserNotFoundError          → 404 Not Found
UserInactiveError          → 403 Forbidden
JwtDecodeError             → 401 Unauthorized
JwtExpiredError            → 401 Unauthorized
InsufficientPermissionsError → 403 Forbidden
```

### 9. Testing Strategy

**Unit Tests (~30 tests):**
```
tests/unit/shared/auth/
├── test_user_entity.py              # 3 tests
├── test_user_repository.py          # 8 tests
├── test_auth_service.py             # 10 tests
├── test_jwt_service.py              # 5 tests
├── test_password_service.py         # 4 tests
└── test_auth_dependencies.py        # (mocked in API tests)
```

**Integration Tests (~10 tests):**
```
tests/integration/shared/auth/
├── test_auth_flow_integration.py    # Login → API call → Refresh
└── test_user_repository_integration.py
```

**Test Categories:**
- **Password Hashing**: Verify bcrypt/argon2 correctness
- **JWT Encode/Decode**: Token generation and validation
- **Login Flow**: Email/password → tokens
- **Token Refresh**: Refresh token → new access token
- **Authorization**: Role-based access control
- **Multi-tenancy**: User can only access own winery data

---

## Architectural Notes

### Alignment with Guidelines

✅ **Follows [ARCHITECTURAL_GUIDELINES.md](../ARCHITECTURAL_GUIDELINES.md):**
- Shared infrastructure (not a domain module)
- Interface-based design (DIP)
- Separation of concerns (auth, jwt, password services)
- Type safety with dataclasses/DTOs
- Repository pattern for User entity
- Dependency injection for FastAPI

### Design Decisions

**Chosen:**
- **JWT** over sessions: Stateless, microservices-ready, no server-side storage
- **bcrypt/argon2** for passwords: Industry standard, secure, battle-tested
- **Role-based** over permission-based: Simpler for MVP, easier to understand
- **Refresh tokens**: Better UX, 15min access token limits attack window
- **Shared module** over per-module auth: Reusability, single source of truth

**Rejected:**
- **OAuth2 providers** (Google, etc.): Out of scope for MVP, can add later
- **Permission-based ACL**: Too complex for current needs (4 roles sufficient)
- **Session storage**: Requires Redis/DB, adds state, complicates scaling
- **Magic links**: Email infrastructure not ready, password-based simpler

### Security Considerations

**Implemented:**
- ✅ Password hashing (bcrypt rounds=12 or argon2id)
- ✅ JWT expiry (15min access, 7 days refresh)
- ✅ Token signature verification (HS256)
- ✅ Role-based authorization
- ✅ Multi-tenancy isolation

**Future Enhancements:**
- 🔄 Token blacklist (Redis) for logout
- 🔄 Rate limiting on login endpoint
- 🔄 Account lockout after failed attempts
- 🔄 Email verification flow
- 🔄 Password reset via email
- 🔄 2FA/MFA support

---

## Consequences

### ✅ Benefits

1. **Unblocks API development**: All modules can now implement HTTP endpoints
2. **Multi-tenancy enforced**: `winery_id` extracted from token automatically
3. **Reusable**: Single auth module serves all domain modules
4. **Secure**: Industry-standard JWT + password hashing
5. **Testable**: Dependencies mockeable, clear interfaces
6. **Type-safe**: DTOs provide compile-time safety
7. **Scalable**: Stateless JWT enables horizontal scaling

### ⚠️ Trade-offs

1. **Initial investment**: ~2-3 días de desarrollo antes de API layers
2. **JWT limitations**: Can't invalidate tokens without blacklist (future Redis)
3. **Refresh token storage**: Client must store securely (HttpOnly cookies recommended)
4. **Role granularity**: 4 roles may be insufficient long-term (future: permissions)

### ❌ Limitations

1. **No SSO/OAuth**: Solo email/password auth (external providers future)
2. **No MFA**: Single-factor authentication only (future enhancement)
3. **No audit log**: User actions not logged (future: audit module)
4. **No password policy**: Min length/complexity not enforced (future)

### 📊 Implementation Estimate

- **Phase 0 (Migration)**: ~100 líneas changed (imports, entity updates, SQL migration)
- **Domain Layer**: ~150 líneas (UserRole enum, DTOs, interfaces) - User already exists
- **Repository Layer**: ~100 líneas (UserRepository)
- **Service Layer**: ~300 líneas (AuthService, JwtService, PasswordService)
- **Dependencies**: ~100 líneas (FastAPI dependencies)
- **Tests**: ~600 líneas (30 unit + 10 integration tests)
- **Total NEW code**: ~1250 líneas, ~40 tests
- **Total MIGRATION**: ~100 líneas imports updated

**Effort**: 
- Day 1: 2h migration + 4h domain/repository = 6 hours
- Day 2: 6h services + dependencies = 6 hours  
- Day 3: 6h integration tests + docs = 6 hours
- **Total: 3 días (18 hours actual work)**

---

## Implementation Checklist

### ✅ Phase 0: User Entity Migration (COMPLETED - Oct 28, 2025)
**CRITICAL**: Must be done FIRST to avoid breaking existing fermentation module

- [x] **Create new location**: `src/shared/auth/domain/entities/user.py`
- [x] **Copy User entity** from `modules/fermentation/src/domain/entities/user.py`
- [x] **Add missing fields**:
  - [x] `role: Mapped[str]` with default="viewer"
  - [x] Timestamps inherited from BaseEntity
- [x] **Rename field**: `last_login` → `last_login_at`
- [x] **Update User relationships**:
  - [x] Keep fermentation relationship with fully-qualified import
  - [x] Keep samples relationship with fully-qualified import
- [x] **Update ALL imports in fermentation module** (~20 files):
  - [x] `src/modules/fermentation/src/domain/entities/fermentation.py`
  - [x] `src/modules/fermentation/src/domain/entities/samples/base_sample.py`
  - [x] All test files using User entity
- [x] **Run existing tests** to verify migration didn't break anything
- [x] **Delete old User entity** file after verification
- [x] **Commit migration**: `git commit -m "refactor: Move User entity to shared/auth infrastructure"`

**Result**: All 173 existing fermentation tests still passing ✅

### ✅ Phase 1: Domain Layer (COMPLETED - Oct 28, 2025)
- [x] Create `src/shared/auth/` structure
- [x] User entity (migrated in Phase 0)
- [x] UserRole enum with permission helpers (`src/shared/auth/domain/enums/user_role.py`)
- [x] DTOs (UserContext, LoginRequest/Response, UserCreate/Update/Response, PasswordChange, RefreshToken)
- [x] Interfaces (IAuthService, IJwtService, IPasswordService, IUserRepository)
- [x] Custom exceptions (errors.py) - 9 error classes
- [x] **Tests**: 81 unit tests passing

### ✅ Phase 2: Repository Layer (COMPLETED - Oct 28, 2025)
- [x] UserRepository implementation with SQLAlchemy AsyncSession
- [x] CRUD operations (create, get_by_email, get_by_id, get_by_username, update, soft delete)
- [x] Existence checks (exists_by_email, exists_by_username)
- [x] Soft delete support with deleted_at filtering
- [x] **Tests**: 21 unit tests passing

### ✅ Phase 3: Service Layer (COMPLETED - Oct 28, 2025)
- [x] PasswordService with bcrypt hashing
  - [x] hash_password() - bcrypt with 12 rounds
  - [x] verify_password() - constant-time comparison
  - [x] validate_password_strength() - 8+ chars, upper, lower, digit
  - [x] **Tests**: 12 unit tests
- [x] JwtService with PyJWT
  - [x] encode_access_token() - 15 min expiry
  - [x] encode_refresh_token() - 7 days expiry
  - [x] decode_token() - validation with error handling
  - [x] extract_user_context() - UserContext from token
  - [x] **Tests**: 13 unit tests
- [x] AuthService - orchestration layer
  - [x] login() - email/password authentication
  - [x] refresh_access_token() - token renewal
  - [x] register_user() - user creation with validation
  - [x] verify_token() - token validation
  - [x] get_user() - user retrieval
  - [x] update_user() - profile/role updates
  - [x] change_password() - password change with old password
  - [x] request_password_reset() - placeholder for Phase 6
  - [x] confirm_password_reset() - placeholder for Phase 6
  - [x] deactivate_user() - soft delete
  - [x] **Tests**: 25 unit tests
- [x] Config via environment variables (JWT_SECRET)
- [x] **Total Service Tests**: 50 unit tests

### ✅ Phase 4: FastAPI Dependencies (COMPLETED - Oct 28, 2025)
- [x] `get_current_user()` dependency - JWT extraction and validation
- [x] `get_current_active_user()` helper - active status check
- [x] `require_role()` factory - role-based access control
- [x] Convenience helpers (require_admin, require_winemaker, require_operator)
- [x] HTTPBearer scheme setup (bearer_scheme)
- [x] Integration with FastAPI exception handlers (401/403)
- [x] **Tests**: 11 unit tests

### ✅ Phase 5: Integration Tests (COMPLETED - Nov 4, 2025)
- [x] Test DB setup with User table (SQLite in-memory with AsyncEngine)
- [x] **AUTH_TEST_MODE environment variable** - avoids FK constraints in isolated tests
- [x] Login flow integration test (4 tests)
  - [x] Valid credentials returns tokens
  - [x] Invalid password fails
  - [x] Non-existent email fails
  - [x] Inactive user fails
- [x] Token refresh integration test (2 tests)
  - [x] Refresh token generates new access token
  - [x] Token contains valid user context
- [x] User registration flow (3 tests)
  - [x] New user creation persists to database
  - [x] Duplicate email fails
  - [x] Duplicate username fails
- [x] Password management (2 tests)
  - [x] Password change flow with verification
  - [x] Wrong old password fails
- [x] User deactivation (1 test)
  - [x] Deactivated user cannot login
- [x] Multi-tenancy isolation (5 tests)
  - [x] Users belong to correct winery
  - [x] Login includes winery context in token
  - [x] Multiple users per winery
  - [x] Email uniqueness across wineries
  - [x] Username uniqueness across wineries
- [x] Role-based authorization (7 tests)
  - [x] Admin role assignment and verification
  - [x] Winemaker role assignment
  - [x] Operator role assignment
  - [x] Viewer role default
  - [x] Role update functionality
  - [x] Token contains role information for all roles
- [x] Repository integration tests (real database operations)
- [x] **Total Integration Tests**: 24 tests passing

### ✅ Phase 6: Documentation & Cleanup (COMPLETED - Nov 4, 2025)
- [x] Create `shared/auth/README.md` with usage examples
- [x] Update `project-context.md` (Auth module fully implemented)
- [x] Update fermentation module docs (User now from shared/auth)
- [x] Document environment variables (JWT_SECRET)
- [x] **Verify fermentation module** still imports User correctly
- [x] Integration tests execution notes (separate runs due to SQLAlchemy mapper conflicts)
- [x] Update ADR-007 status to IMPLEMENTED

---

## ✅ Implementation Summary

**Total Test Coverage: 186 tests passing**
- **Unit Tests**: 163 tests (domain, repository, services, dependencies)
- **Integration Tests**: 24 tests (auth flows, multi-tenancy, RBAC)
- **Test Execution**: Tests must run separately due to SQLAlchemy mapper registry conflicts
  - Unit: `pytest src/shared/auth/tests/unit/`
  - Integration: `pytest src/shared/auth/tests/integration/`

**Code Metrics:**
- Domain Layer: DTOs, enums, interfaces, errors
- Repository Layer: UserRepository with 8 async methods
- Service Layer: 3 services (AuthService, JwtService, PasswordService)
- FastAPI Layer: 7 reusable dependencies
- Total Lines: ~2,100 lines of production code + tests

**Migration Success:**
- ✅ User entity successfully moved to shared/auth
- ✅ Fermentation module updated with correct imports
- ✅ All 173 fermentation tests still passing (182 with new integration tests)
- ✅ No breaking changes to existing functionality

---

## Migration Impact Analysis

### Files Requiring Import Updates (~20 files in fermentation module):

**Entities:**
- `src/modules/fermentation/src/domain/entities/fermentation.py`
- `src/modules/fermentation/src/domain/entities/samples/base_sample.py`

**Tests:**
- `tests/integration/conftest.py` (test_user fixture)
- `tests/integration/repository_component/test_fermentation_repository_integration.py`
- All files with `fermented_by_user_id` references

**Import Change:**
```python
# BEFORE (INCORRECT):
from src.modules.fermentation.src.domain.entities.user import User

# AFTER (CORRECT):
from src.shared.auth.domain.entities.user import User
```

### Database Migration (SQL):
```sql
-- Add new columns to existing users table
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'viewer' NOT NULL;
ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT NOW() NOT NULL;
ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT NOW() NOT NULL;

-- Rename existing column
ALTER TABLE users RENAME COLUMN last_login TO last_login_at;

-- Create index on role for authorization queries
CREATE INDEX idx_users_role ON users(role);

-- Update existing users to have winemaker role (if they exist)
UPDATE users SET role = 'winemaker' WHERE role IS NULL OR role = '';
```

### Risk Mitigation:
1. ✅ **Phase 0 first**: Migrate User entity before building new auth features
2. ✅ **Keep relationships**: User↔Fermentation, User↔Sample relationships preserved
3. ✅ **Run tests**: Verify 173 fermentation tests still pass after migration
4. ✅ **Incremental commits**: Separate commits for migration vs new features
5. ✅ **Backward compatible**: Existing test fixtures continue working

---

## Status

**✅ IMPLEMENTED** - Completed Nov 4, 2025

**Implementation Timeline:**
- Oct 26, 2025: ADR Accepted
- Oct 28, 2025: Phases 0-4 Completed (Domain, Repository, Services, Dependencies)
- Nov 4, 2025: Phase 5 Completed (Integration Tests)

**Test Results:**
- ✅ 186 total tests passing (163 unit + 24 integration)
- ✅ Auth module fully functional and tested
- ✅ Fermentation module integration verified (182 tests passing)
- ✅ Multi-tenancy and RBAC working correctly

**Priority:** **HIGH** - **COMPLETED** ✅ - Now unblocks ADR-006 (API Layer)

**Next Steps:**
1. ~~Create branch: `feature/shared-auth-module`~~ ✅ DONE
2. ~~Execute Phase 0 (User migration)~~ ✅ DONE
3. ~~Implement Phase 1-2 (Domain + Repository)~~ ✅ DONE
4. ~~Implement Phase 3-4 (Services + Dependencies)~~ ✅ DONE
5. ~~Implement Phase 5 (Integration tests)~~ ✅ DONE
6. ~~Document and commit~~ ✅ DONE
7. **READY**: Proceed with ADR-006 (API Layer) - Auth infrastructure complete
8. Begin fermentation API implementation using auth dependencies

**Migration Success:**
- ✅ User entity successfully moved to shared/auth
- ✅ All fermentation module tests still passing
- ✅ No breaking changes
- ✅ Auth dependencies ready for API layer use

---

## References

- **[ADR-006: API Layer Design](./ADR-006-api-layer-design.md)** - DEPENDS on this ADR
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [Passlib Documentation](https://passlib.readthedocs.io/) - bcrypt/argon2
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
