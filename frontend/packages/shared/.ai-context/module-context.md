# Module Context: packages/shared

> **Parent Context**: See `frontend/.ai-context/project-context.md` for frontend-level decisions
> **System Context**: See `/.ai-context/project-context.md` for system-level decisions

## Module responsibility

**Shared logic layer** consumed by both `apps/web` and `apps/mobile`. Contains everything that is framework-agnostic: TypeScript type definitions matching backend DTOs, the HTTP API client, React hooks for data fetching/auth/polling, token storage abstractions, and the offline write queue.

**Critical rule**: This package NEVER imports from `apps/web` or `apps/mobile`. It NEVER reads `process.env` directly — base URLs are passed as constructor arguments so the package remains portable across both apps.

## Technology stack

- **Language**: TypeScript (strict mode)
- **HTTP client**: Axios with interceptors for token injection and 401 auto-refresh
- **Server state**: TanStack Query v5 hooks (framework-agnostic factory functions)
- **Web token storage**: js-cookie (httpOnly cookie pattern)
- **Mobile token storage**: expo-secure-store
- **Offline persistence**: @tanstack/query-async-storage-persister + @react-native-async-storage/async-storage
- **Build**: tsup for dual CJS/ESM output

## Module interfaces

**Consumed by**: `apps/web` and `apps/mobile` via `@shared` path alias
**Depends on**: `packages/ui` for shared Zod schemas (form validation in mutation hooks)
**Provides**: Types, API functions, React hooks, storage implementations, SyncQueue

## Component structure

| Component | Path | Responsibility |
|-----------|------|---------------|
| Types | `src/types/` | TypeScript interfaces matching all backend response shapes |
| API client | `src/api/` | Axios-based HTTP functions, one file per backend module |
| Hooks | `src/hooks/` | React hooks for auth, current user, role, polling, stale data |
| Storage | `src/storage/` | TokenStorage interface + web (cookie) and mobile (SecureStore) implementations |
| Sync | `src/sync/` | SyncQueue — offline write queue with AsyncStorage persistence |

## Key patterns

- **TokenStorage abstraction**: Web and mobile provide their own implementations. Hooks and ApiClient depend on the interface, never a concrete implementation directly.
- **ApiClient constructor injection**: `new ApiClient({ baseURLs, tokenStorage })` — no global singleton that reads env vars.
- **401 auto-refresh**: Axios response interceptor catches 401, calls `POST /auth/refresh`, stores new access token, retries original request. On refresh failure: clears tokens, throws `AuthExpiredError`.
- **TanStack Query hooks**: Each resource has a `useXxx` query hook and `useXxxMutation` mutation hook. Polling is configured per-hook via `refetchInterval` option.

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 1 of FRONTEND-PLAN.md

## Component contexts

| Component | Context file |
|-----------|-------------|
| `src/types/` | `src/types/.ai-context/component-context.md` |
| `src/api/` | `src/api/.ai-context/component-context.md` |
| `src/hooks/` | `src/hooks/.ai-context/component-context.md` |
| `src/storage/` | `src/storage/.ai-context/component-context.md` |
| `src/sync/` | `src/sync/.ai-context/component-context.md` |
