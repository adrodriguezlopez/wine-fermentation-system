# Component Context: Mobile Fermentation List (`apps/mobile/components/fermentation/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Screen**: `app/(tabs)/fermentation/index.tsx`

## Component responsibility

**Fermentation list screen components**. The main landing screen after login. Winemakers see all active fermentations assigned to the current winery. Each card shows current status and the most recent density reading.

## Components

### `FermentationList.tsx`
`FlatList` of `<FermentationCard>` items. Pull-to-refresh via TanStack Query `refetch`. `<EmptyState>` when no fermentations. `<StaleBanner>` when data is stale. Uses `useQuery(['fermentations'])` from `fermentationApi`.

### `FermentationCard.tsx`
Card representing a single fermentation. Content:
- Vessel code (bold, large)
- Vintage year
- `<StatusBadge>` with current status
- Latest density reading in DM Mono (if available)
- Days fermenting count
- Chevron right icon

Tap navigates to `fermentation/[id]`. Card touch area full-width with feedback.

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 4
