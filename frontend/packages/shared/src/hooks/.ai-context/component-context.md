# Component Context: Hooks (`packages/shared/src/hooks/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions

## Component responsibility

**React hooks** for authentication state, current user identity, role checks, data polling, and stale data detection. These hooks wrap TanStack Query and Zustand, providing a clean API surface to both `apps/web` and `apps/mobile`.

**Position**: Called by page and screen components. They depend on `src/api/` functions and `src/storage/` for token management.

## Architecture pattern

Custom hooks wrapping TanStack Query (`useQuery`, `useMutation`) and Zustand store. Hooks are framework-agnostic React — they work in Next.js and Expo Router equally.

## Files

### `useAuth.ts`
Auth session management hook.
```typescript
const { login, logout, isAuthenticated, isLoading } = useAuth()
// login(credentials) → calls POST /auth/login → stores tokens → sets Zustand auth state
// logout() → clears TokenStorage + Zustand state → navigates to /login
```

### `useCurrentUser.ts`
Returns the decoded JWT payload as `UserContext`.
```typescript
const { user, isLoading } = useCurrentUser()
// Calls GET /auth/me; result cached in TanStack Query
// user: { user_id, email, role, winery_id }
```

### `useRole.ts`
Role-based access helpers.
```typescript
const { role, isAdmin, isWinemaker, hasRole } = useRole()
// Reads from useCurrentUser(); used by RoleGuard component
```

### `usePolling.ts`
Polling hook factory — wraps TanStack Query `refetchInterval`.
```typescript
const { data, isLoading } = usePolling(
  ['fermentation', id, 'latest-sample'],
  () => sampleApi.getLatestSample(id),
  { intervalMs: 30_000, enabled: status !== 'COMPLETED' }
)
// Automatically stops polling when enabled becomes false
```

### `useStaleDataWarning.ts`
Detects when cached data is older than 4 hours — used to show the offline stale banner on mobile.
```typescript
const { isStale, staleSinceMinutes } = useStaleDataWarning(queryKey)
// Reads TanStack Query cache metadata
// isStale = true when staleSinceMinutes > 240
```

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 2 / packages/shared
