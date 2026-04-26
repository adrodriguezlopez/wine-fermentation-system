# ADR-048: Frontend MSW Testing Strategy for `apps/web`

**Status:** Accepted  
**Date:** 2026-04-26  
**Authors:** Development Team  
**Related ADRs:** ADR-045 (Frontend Architecture), ADR-047 (Frontend Polling Strategy)

> **📋 Context:** [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)

---

## Context

`apps/web` components fetch data through TanStack Query, which makes real HTTP requests to the backend services. In the test environment (Vitest + jsdom) there is no backend running. MSW (Mock Service Worker) is already installed and the server is initialized in `src/test/setup.ts` — but no handlers exist yet because Iteration 3 only built the layout shell (no data-fetching screens). As screen implementation begins in Iteration 4+, a consistent handler organization strategy must be established before the first data-fetching test is written, or the test suite will become inconsistent and hard to maintain.

---

## Decision

1. **Handlers are organized by backend domain**, mirroring the four backend microservices and the `packages/shared/src/api/` structure:

   ```
   src/test/handlers/
   ├── fermentation.ts   ← /api/fermentation/*
   ├── winery.ts         ← /api/winery/*
   ├── fruit-origin.ts   ← /api/fruit-origin/*
   ├── analysis.ts       ← /api/analysis/*
   └── index.ts          ← re-exports all handlers for the global server
   ```

2. **Happy-path handlers are registered globally in `src/test/setup.ts`.** The MSW server starts with all domain handlers active. Every test runs against a fully simulated API by default — no boilerplate needed per test file.

3. **Error and edge-case handlers use `server.use(...)` per test.** When a test needs to simulate a 404, 500, validation error, or loading state, it calls `server.use(http.get(...))` inside the test. `afterEach(() => server.resetHandlers())` (already in `setup.ts`) restores the global happy-path handlers after each test.

4. **Handler response shapes match the actual backend DTOs.** Handlers return the exact same JSON structure as the real API — typed against the DTO interfaces in `packages/shared/src/types/`. No approximate mocks. If a DTO changes, the handler must change too.

5. **Handler data is minimal but valid.** Happy-path fixtures use the smallest valid dataset (e.g. a list with 1–2 items, a detail with the minimum required fields). Tests that need specific data states (e.g. a fermentation with `status: 'COMPLETED'`, or an alert with `severity: 'CRITICAL'`) override with `server.use(...)`.

6. **Polling is disabled in tests.** All queries under test are called with `refetchInterval: false` in the test environment, or the `QueryClient` in test utils is configured with `defaultOptions: { queries: { refetchInterval: false, retry: false } }`. This prevents tests from hanging on poll timers.

7. **A `renderWithProviders` test utility is created at `src/test/utils.tsx`.** It wraps the component under test with `QueryClientProvider` (using the test `QueryClient` from decision 6) and any other required providers. Tests never set up providers manually.

---

## Architectural Notes

- MSW intercepts at the network layer (via `msw/node` in Vitest). This means TanStack Query, Axios interceptors (including the 401 refresh logic in `ApiClient`), and all intermediate code run exactly as in production. Only the HTTP response is simulated.
- This is strictly preferable to mocking `packages/shared` modules directly — module mocks bypass all the integration logic and create false confidence.
- The `server` instance (from `setupServer(...)`) is exported from `src/test/setup.ts` so individual test files can call `server.use(...)` without re-creating it.

---

## Consequences

- ✅ Test files are clean — no per-file handler boilerplate for the common case
- ✅ Handler organization mirrors the existing domain structure of the whole project
- ✅ Tests exercise the real TanStack Query + Axios + ApiClient stack, not mocks
- ✅ `resetHandlers()` after each test guarantees isolation between tests
- ✅ `renderWithProviders` eliminates repeated provider setup across test files
- ⚠️ Adding a new API endpoint requires adding a handler to the appropriate domain file — easy but must not be forgotten
- ⚠️ If a DTO shape changes in `packages/shared`, all related handlers must be updated — caught at TypeScript compile time if handlers are typed correctly
- ❌ MSW does not test the actual backend — integration against real services requires a separate E2E layer (out of scope for MVP)

---

## Related ADRs

- **[ADR-045](./ADR-045-frontend-architecture.md)**: Establishes Vitest + RTL + MSW as the testing stack; this ADR specifies how MSW is used within that stack
- **[ADR-047](./ADR-047-frontend-polling-strategy.md)**: Polling must be disabled in the test `QueryClient` (decision 6 above) to avoid timer-related test hangs

---

## Status
Accepted
