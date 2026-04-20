# Component Context: API Client (`packages/shared/src/api/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **API Reference**: See `.github/skills/wine-frontend-context/SKILL.md` for full endpoint reference

## Component responsibility

**Typed HTTP API functions** — one file per backend domain module, plus the `ApiClient` class that all of them use. Each function is a thin, typed wrapper around an axios call. No business logic here — just HTTP.

**Position**: The lowest-level data-fetching layer. TanStack Query hooks (in `src/hooks/`) call these functions and handle caching, loading states, and error handling.

## Architecture pattern

`ApiClient` class (constructed with `baseURLs` + `TokenStorage`) + per-module function files that accept an `ApiClient` instance.

### `ApiClient` (client.ts)

Responsibilities:
- Create an axios instance per service base URL
- Inject `Authorization: Bearer <access_token>` header on every request via request interceptor
- Catch 401 responses, call `POST /auth/refresh`, store the new access token, and **retry the original request** — transparently to the caller
- On refresh failure: call `tokenStorage.clear()`, throw `AuthExpiredError` (callers redirect to login)
- Normalize all backend error responses (`{ detail: string }`) into `ApiError` instances

```typescript
// Construction — base URLs injected, never read from process.env
const client = new ApiClient({
  baseURLs: { fermentation: '...', winery: '...', fruitOrigin: '...', analysis: '...' },
  tokenStorage: new CookieTokenStorage(), // or SecureStoreTokenStorage
})
```

## Files

| File | Axios instance | Endpoints covered |
|------|---------------|------------------|
| `client.ts` | `ApiClient` class | Auth: login, refresh, me |
| `fermentation.ts` | `client.fermentation` | createFermentation, createBlendFermentation, getFermentation, listFermentations, updateFermentation, deleteFermentation, getFermentationTimeline, getFermentationStatistics |
| `sample.ts` | `client.fermentation` | createSample, listSamples, getLatestSample, getSample |
| `protocol.ts` | `client.fermentation` | createProtocol, listProtocols, getProtocol, updateProtocol, cloneProtocol, activateProtocol |
| `protocol-steps.ts` | `client.fermentation` | addStep, listSteps, updateStep, deleteStep |
| `execution.ts` | `client.fermentation` | startExecution, getExecution, updateExecution, listExecutions |
| `step-completion.ts` | `client.fermentation` | completeStep, listStepCompletions, getCompletion |
| `alert.ts` | `client.fermentation` | listAlerts, checkAlerts, acknowledgeAlert, dismissAlert |
| `action.ts` | `client.fermentation` | createAction, listFermentationActions, listExecutionActions, getAction, updateActionOutcome, deleteAction |
| `analysis.ts` | `client.analysis` | triggerAnalysis, getAnalysis, listAnalyses |
| `recommendation.ts` | `client.analysis` | getRecommendation, applyRecommendation |
| `advisory.ts` | `client.analysis` | listAdvisories, acknowledgeAdvisory |
| `winery.ts` | `client.winery` | createWinery, listWineries, getWinery, getWineryByCode, updateWinery, deleteWinery |
| `vineyard.ts` | `client.fruitOrigin` | createVineyard, listVineyards, getVineyard, updateVineyard, deleteVineyard |
| `harvest-lot.ts` | `client.fruitOrigin` | createHarvestLot, listHarvestLots, getHarvestLot, updateHarvestLot, deleteHarvestLot |
| `index.ts` | — | Re-exports all functions |

## Key constraint: 401 auto-refresh flow

```
Request → 401 received
        → POST /auth/refresh with refresh token
        → success: store new access_token, retry original request (caller never sees the 401)
        → failure: clear all tokens, throw AuthExpiredError
                 → caller (useAuth hook) catches AuthExpiredError → redirects to /login
```

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 2 / packages/shared
