# Module Context: Mobile App (`frontend/apps/mobile/`)

> **Workspace Context**: See `../../.ai-context/project-context.md` for the full frontend project
> **Sister App**: See `../web/.ai-context/module-context.md` for the admin web app

## Module responsibility

**Winemaker mobile app** — deployed as a PWA. The mobile app is the primary tool for winemakers on the winery floor. They monitor active fermentations, record readings (samples), follow protocol step checklists, view analysis results, and manage corrective actions. Wineries are mobile-first; tablets and phones in a winery cellar are the primary device.

## Tech stack

| Concern | Choice |
|---|---|
| Framework | Expo SDK 52 |
| Navigation | Expo Router v3 (file-based routing) |
| Styling | NativeWind (Tailwind React Native) |
| State | TanStack Query v5 + Zustand |
| HTTP | `packages/shared` ApiClient (Axios) |
| Animation | Expo Reanimated |
| Auth storage | Expo SecureStore via `SecureStoreTokenStorage` |
| Offline | SyncQueue + TanStack Query persistence via AsyncStorage |
| Deployment | PWA (no app store) |
| Testing | Jest + RNTL + MSW |

## Route tree (Expo Router v3)

```
app/
├── _layout.tsx              Root layout (font loading, query client)
├── index.tsx                Redirect → (auth)/login or (tabs)/fermentation
├── (auth)/
│   ├── _layout.tsx          Auth layout (no navbar)
│   └── login.tsx            Login screen
├── (tabs)/
│   ├── _layout.tsx          Bottom tab bar layout
│   ├── fermentation/
│   │   ├── index.tsx        Fermentation list screen
│   │   └── [id]/
│   │       ├── index.tsx    Fermentation detail (readings + samples)
│   │       ├── protocol.tsx Protocol checklist screen
│   │       └── analysis.tsx Analysis summary screen
│   ├── actions/
│   │   └── index.tsx        My actions screen
│   └── profile/
│       └── index.tsx        Profile + logout
└── 403.tsx                  Forbidden screen (precaution if admin hits mobile)
```

## Module interfaces

| Interface | Source | Purpose |
|---|---|---|
| `packages/shared/src/api` | ApiClient + per-service files | All HTTP calls |
| `packages/shared/src/hooks` | `useAuth`, `useRole`, `usePolling`, `useStaleDataWarning` | Auth + polling |
| `packages/shared/src/storage` | `SecureStoreTokenStorage` | JWT persistence |
| `packages/shared/src/sync` | `SyncQueue` | Queue writes when offline |
| `packages/ui/src/formatters` | Format functions | Format numeric readings |
| `packages/ui/src/constants` | Label/color maps | Enum display values |

## Key architecture decisions

### Bottom tab navigation
5 tabs: Fermentation List, Fermentation Detail (active fermentation context), Actions, Profile. Detail tab is navigated to by tapping a fermentation card, not a tab item directly.

### Offline behavior
- TanStack Query persistence via AsyncStorage — cached data survives app restart
- `SyncQueue` flushes on foreground — `AppState` listener calls `syncQueue.flush()` on `active`
- `<StaleBanner>` appears when data is older than 4 hours
- `<OfflineIndicator>` in root layout when `useNetInfo().isConnected === false`
- Online-only operations: login, alert acknowledge/dismiss, start execution

### Auth flow
JWT stored in Expo SecureStore. 401 auto-refresh in ApiClient interceptor (same logic as web but uses `SecureStoreTokenStorage`). Login screen is outside tab layout.

### Polling
Protocol execution steps poll every 30s via `usePolling` hook. Stops automatically when `status === 'COMPLETED'`.

## Component contexts

| Component group | Context file |
|---|---|
| UI primitives | `components/ui/.ai-context/component-context.md` |
| Fermentation list | `components/fermentation/.ai-context/component-context.md` |
| Fermentation detail | `components/fermentation-detail/.ai-context/component-context.md` |
| Protocol checklist | `components/protocol/.ai-context/component-context.md` |
| Analysis summary | `components/analysis/.ai-context/component-context.md` |
| Alerts | `components/alerts/.ai-context/component-context.md` |
| Actions | `components/actions/.ai-context/component-context.md` |
| Profile | `components/profile/.ai-context/component-context.md` |

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 4
