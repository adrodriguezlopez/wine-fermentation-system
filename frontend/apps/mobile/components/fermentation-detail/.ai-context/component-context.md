# Component Context: Mobile Fermentation Detail (`apps/mobile/components/fermentation-detail/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Screen**: `app/(tabs)/fermentation/[id]/index.tsx`

## Component responsibility

**Fermentation detail screen components** — the core monitoring view. Shows current readings, sample history, and navigation to protocol checklist and analysis screens.

## Components

### `ReadingsCard.tsx`
Displays the most recent sample values:
- Density value in DM Mono (large, prominent)
- Temperature °C in DM Mono
- Brix °Bx in DM Mono
- `formatRelative(recorded_at)` timestamp in small muted text

Polling via `usePolling(30_000)`. If no samples yet: "No readings recorded yet" message.

### `SampleFAB.tsx`
Floating Action Button (FAB) positioned bottom-right. Wine-red circle with "+" icon. Tapping opens `<SampleBottomSheet>`. Animated press feedback via Expo Reanimated.

### `SampleBottomSheet.tsx`
`<BottomSheet>` containing `<SampleForm>` (mobile version). Fields: sample type (segmented control), value (DM Mono numeric input), datetime (default: now), notes (optional).  
On submit: if online → `sampleApi.createSample` immediately; if offline → enqueued in `SyncQueue` as `POST /samples`.  
Invalidates or updates `['samples', id]` query on success.

### `NavigationLinks.tsx`
Two navigation row items:
1. "Protocol Checklist" → `fermentation/[id]/protocol`
2. "Analysis" → `fermentation/[id]/analysis`

Each row with an icon, label, and chevron right. Navigation uses `router.push`.

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 4
