# Data Fetching And API Integration

## Current Integration Layers

The API wiring is already split across web-specific and shared code.

Use these layers intentionally:

- `apps/web/src/lib/api-client.ts` — web app wiring for base URLs and token storage
- `packages/shared/src/api/client.ts` — shared `ApiClient` implementation with refresh behavior
- `packages/shared/src/api/*.ts` — domain-specific API modules
- `packages/shared/src/types/*.ts` — shared response/request types
- `packages/shared/src/hooks/*.ts` — shared React hooks such as `useCurrentUser`

## HTTP Routing Model

The Next.js app uses rewrite-based internal proxies in `apps/web/next.config.mjs`:

- `/api/fermentation/*`
- `/api/winery/*`
- `/api/fruit-origin/*`
- `/api/analysis/*`

Do not hardcode direct backend hosts in page or component code.

## Query Behavior Today

`QueryProvider` sets these defaults:

- `staleTime: 60_000`
- `retry: 1`

The current-user hook narrows behavior further with:

- `staleTime: 5 * 60 * 1000`
- `enabled` only when session cookies exist

When adding new queries, choose defaults deliberately. Do not copy polling or stale-time values without a behavioral reason.

## Preferred Change Path For New Backend Data

When integrating a new endpoint:

1. add or update shared types in `packages/shared/src/types/`
2. add or update the shared API module in `packages/shared/src/api/`
3. expose web-specific wiring only if needed in `apps/web`
4. create the page/component hook-up in the route or component layer

Avoid putting transport logic directly inside pages unless it is truly one-off and will not be reused.

## Polling Guidance

This codebase expects polling for some real-time-ish UX, but it does not mean every query should poll.

Use polling only when:

- the screen is expected to reflect live fermentation changes
- the backend does not push updates
- the user benefits from passive refresh

Before adding polling, answer:

- what data becomes stale quickly?
- when should polling stop?
- what query key owns the cache?

## Error Handling Guidance

The shared API client already handles auth expiry and token refresh behavior.

Do not duplicate refresh logic inside components.

Component responsibilities should usually be limited to:

- loading state
- empty state
- success rendering
- non-auth API error presentation

## Validation Loop

After API/query changes:

```bash
pnpm --filter @wine/web type-check
pnpm --filter @wine/web test
pnpm --filter @wine/web lint
```

If you changed shared types or API modules, verify the consuming web files still match the updated shapes.