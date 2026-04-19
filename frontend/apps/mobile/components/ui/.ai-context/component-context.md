# Component Context: Mobile UI Primitives (`apps/mobile/components/ui/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Styling**: NativeWind (Tailwind React Native) — utility classes instead of `StyleSheet`

## Component responsibility

**Shared primitive components** used across all mobile screens. React Native equivalents of the web `components/ui/` group — adapted for touch targets, NativeWind, and mobile interaction patterns.

## Components

### `Screen.tsx`
Base wrapper component for every screen. Applies `SafeAreaView` + `ScrollView` with consistent padding. Renders `<OfflineIndicator>` at top if offline. Props: `children`, `title?: string`, `refreshing?: boolean`, `onRefresh?: () => void`.

### `StatusBadge.tsx`
Displays a fermentation status string with the correct background colour from `FERMENTATION_STATUS_COLOR`. React Native `<View>` + `<Text>`. Touch size ≥ 44pt.

### `ConfidencePill.tsx`
Displays a confidence level (HIGH/MEDIUM/LOW) using `CONFIDENCE_COLOR` and `CONFIDENCE_LABEL`. Pill shape with coloured background.

### `EmptyState.tsx`
Centered illustration placeholder + message text + optional action button. Used on empty lists.

### `LoadingSpinner.tsx`
React Native `<ActivityIndicator>` centred in a full-height container. Colour: `#8B1A2E` (wine red accent).

### `ErrorMessage.tsx`
Card-style error display with error text and optional "Retry" callback button.

### `StaleBanner.tsx`
Yellow warning banner rendered at top of a screen when `useStaleDataWarning()` returns `true` (data older than 4h). Message: "Data last updated over 4 hours ago".

### `OfflineIndicator.tsx`
Thin banner at very top of `<Screen>` component when `useNetInfo().isConnected === false`. Message: "You are offline. Changes will sync when reconnected."

### `BottomSheet.tsx`
Wraps Expo `@gorhom/bottom-sheet`. Renders children inside a dismissible bottom sheet panel. Used by `SampleBottomSheet` and `MarkCompleteSheet`.

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 4
