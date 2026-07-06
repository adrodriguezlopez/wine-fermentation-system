# Auth And Routing

## Current Auth Stack

Auth is not purely in-memory.

Current pieces:

- `apps/web/src/lib/api-client.ts` wires `ApiClient` with `CookieTokenStorage`
- `packages/shared/src/api/client.ts` owns request auth headers and refresh flow
- `apps/web/src/providers/auth-provider.tsx` syncs current user and redirects unauthenticated users
- `apps/web/src/stores/auth-store.ts` stores the resolved `UserDto`
- `packages/shared/src/hooks/useCurrentUser.ts` only runs when auth cookies are present

## Session Signals Used Today

The app checks these cookie names:

- `wine_access_token`
- `wine_refresh_token`

These cookies are used both for:

- server-side redirect decisions in `src/app/page.tsx`
- client-side auth gating in `AuthProvider`

## Routing Behavior

Current flow:

1. `src/app/page.tsx` reads cookies on the server.
2. If a session exists, it redirects to `/dashboard`.
3. Otherwise it redirects to `/login`.
4. Inside dashboard routes, `AuthProvider` keeps the client-side session state in sync.

This means you should not rebuild root routing around a fresh auth abstraction unless the task explicitly asks for that redesign.

## Protected UI Guidance

When adding protected pages under the dashboard route group:

- rely on the existing dashboard layout shell
- keep page components focused on page behavior
- avoid duplicating auth bootstrap logic in every page

If a page needs the current user:

- prefer the existing store/hook/provider flow
- only add a new auth helper if the current one cannot express the needed behavior

## Do Not Reintroduce These Patterns

- Access token stored only in a local variable
- New bespoke `AuthContext` replacing the existing store/provider flow without need
- LocalStorage as the primary token store
- Forcing every route component to be a client component just to read auth

## When Auth Changes Require Wider Updates

If you change:

- cookie names
- redirect destinations
- refresh behavior
- current user loading rules

then verify all of these together:

- `apps/web/src/app/page.tsx`
- `apps/web/src/providers/auth-provider.tsx`
- `apps/web/src/lib/api-client.ts`
- `packages/shared/src/api/client.ts`
- `packages/shared/src/hooks/useCurrentUser.ts`

## Validation Loop

After auth/routing changes:

```bash
pnpm --filter @wine/web type-check
pnpm --filter @wine/web test
```

If the behavior is route-level, also verify the redirect path and session assumptions in the touched page/layout files.