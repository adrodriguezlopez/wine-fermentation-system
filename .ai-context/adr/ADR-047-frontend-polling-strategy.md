# ADR-047: Frontend Polling Strategy

**Status:** Accepted  
**Date:** 2026-04-26  
**Authors:** Development Team  
**Related ADRs:** ADR-045 (Frontend Architecture), ADR-040 (Notifications & Alerts Strategy)

> **📋 Context:** [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)

---

## Context

The backend exposes no WebSocket or SSE endpoints — all real-time data must be obtained via polling. The frontend (`apps/web`) needs a consistent, explicitly specified polling contract: which queries poll, at what interval, when they stop, what happens on window focus, and how stale data is communicated to the user. Without a written contract, each screen would make independent decisions and the result would be inconsistent UX and unpredictable backend load. ADR-040 establishes the alert polling requirement (<15s to log); ADR-045 establishes TanStack Query v5 as the server-state layer.

---

## Decision

1. **Standard polling interval: 30 seconds.** All actively polled queries use `refetchInterval: 30_000`. No query polls faster than 30s in `apps/web`.

2. **Queries that poll:**
   - Dashboard summary (active fermentation count, recent alert count)
   - Fermentation list (`GET /fermentations`)
   - Fermentation detail — latest sample and alert count for the open fermentation
   - Active alerts for any open fermentation

3. **Queries that do NOT poll:**
   - Protocols list and detail (reference data, changes are user-initiated)
   - Fruit origin — vineyards and harvest lots (reference data)
   - Admin / winery management (low-change operational data)
   - Any query whose subject fermentation has `status === 'COMPLETED'`

4. **Stop polling when fermentation is COMPLETED.** All queries scoped to a specific fermentation pass `refetchInterval: fermentation?.status === 'COMPLETED' ? false : 30_000`. This is checked after the fermentation detail query resolves.

5. **Window focus behavior: Option C — continue polling + immediate refetch on focus.** TanStack Query's default `refetchOnWindowFocus: true` is kept enabled globally. When the user returns to the tab, all active queries refetch immediately regardless of where they are in the 30s cycle. This ensures the user always sees fresh data the moment they look at the screen.

6. **Stale data threshold is configurable per query criticality:**
   - **Critical queries** (fermentation detail, active alerts): `staleThreshold: 2 * 60 * 1000` (2 minutes)
   - **Summary queries** (dashboard, fermentation list): `staleThreshold: 5 * 60 * 1000` (5 minutes)
   - **Reference queries** (protocols, fruit origin, admin): no stale warning — these are not real-time

7. **Stale data UX: banner, not error state.** When a polled query has not succeeded within its threshold, a non-blocking banner is shown (`useStaleDataWarning` from `packages/shared`): *"Last updated X minutes ago — checking connection..."*. The last known data remains visible. The component never replaces content with an error state due to a poll failure alone.

8. **`useStaleDataWarning` threshold parameter.** The hook in `packages/shared` accepts a `threshold` option (milliseconds). Call sites pass `STALE_THRESHOLD_CRITICAL` (2 min) or `STALE_THRESHOLD_SUMMARY` (5 min) — constants exported from `packages/shared/src/constants/polling.ts`.

---

## Architectural Notes

- The 4-hour `staleThreshold` in `useStaleDataWarning` was designed for `apps/mobile` offline mode. Web uses different values — this is intentional and expected.
- TanStack Query's default `retry: 3` with exponential backoff applies before a query reaches `isError`. The stale banner activates independently of `isError` — it fires when the last *successful* fetch is older than the threshold, regardless of retry state.
- `refetchOnWindowFocus` is a global QueryClient option set in `QueryProvider`. Individual queries can override it by passing `refetchOnWindowFocus: false` — allowed only for reference data queries.

---

## Consequences

- ✅ Consistent user experience — all screens follow the same polling rules
- ✅ Users always see fresh data immediately when they return to the tab
- ✅ Fermentation COMPLETED correctly stops unnecessary polling
- ✅ Critical alerts surface within 30s on any active fermentation screen
- ✅ Stale data is surfaced without hiding last known values from the user
- ⚠️ Dashboard home page polls even on summary data — modest backend load, acceptable for internal winery tool
- ⚠️ `refetchOnWindowFocus` means every tab switch triggers a refetch — on slow connections this may cause a brief loading flash; mitigated by TanStack Query's stale-while-revalidate (shows cached data while refetching)
- ❌ No push notifications — if a user has the browser closed, they will not receive alerts

---

## Related ADRs

- **[ADR-045](./ADR-045-frontend-architecture.md)**: Establishes TanStack Query v5 as the server-state layer that this ADR configures
- **[ADR-040](./ADR-040-notifications-alerts.md)**: Defines the alert acknowledge/dismiss distinction and the "<15 seconds to log" mobile constraint that informed the 30s interval choice

---

## Status
Accepted
