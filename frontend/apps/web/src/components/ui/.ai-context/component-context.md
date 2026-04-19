# Component Context: UI Primitives (`apps/web/src/components/ui/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions

## Component responsibility

**Design-system primitives** — thin wrappers over Shadcn/ui components with the project's design tokens pre-applied. These are the atomic building blocks used across every feature component. They ensure consistent visual language without repeating Tailwind class strings everywhere.

Shadcn/ui components are installed into this folder (as is standard). Custom primitives extending them live here too.

## Files

### `DataTable.tsx`
Paginated, sortable table built on Shadcn `Table`. Features:
- Loading state: skeleton rows (3 per page by default)
- Empty state: renders `<EmptyState>` slot
- Pagination controls at bottom
- Column definitions typed with TanStack Table

### `Drawer.tsx`
Slide-in side panel (Shadcn `Sheet`). Used for "Add Sample" and "Record Action" forms. Props: `title`, `description`, `trigger`, `children`. Closes on overlay click and Escape key.

### `StatusBadge.tsx`
Renders `FermentationStatus` as a colored pill. Reads `FERMENTATION_STATUS_LABEL` and `FERMENTATION_STATUS_COLOR` from `@ui/constants`. Variants: `default` (pill) and `dot` (small dot + text).

### `ConfidenceBadge.tsx`
Renders `ConfidenceLevel` (HIGH/MEDIUM/LOW) as a colored badge. Reads from `@ui/constants/confidence-levels`.

### `PageHeader.tsx`
See layout context — re-exported from `layout/` for convenience.

### `EmptyState.tsx`
Centered icon + heading + optional description + optional CTA button. Used in empty tables and lists.
```typescript
<EmptyState icon={Flask} title="No fermentations yet" description="Create your first fermentation to get started." action={<Button>New Fermentation</Button>} />
```

### `LoadingSkeleton.tsx`
Two variants:
- `<LoadingSkeleton.Card />` — rounded rect skeleton for metric cards
- `<LoadingSkeleton.Row />` — table row skeleton (5 cells)

### `ErrorMessage.tsx`
Displays an `ApiError.detail` string with a retry button. Used in error boundaries and query error states.

### `ConfirmDialog.tsx`
Shadcn `AlertDialog` wrapper for destructive actions. Props: `title`, `description`, `confirmLabel`, `onConfirm`. Used before delete operations.

## Design notes

All primitives use the shared design tokens:
- Accent `#8B1A2E` for primary buttons and active states
- `DM Sans` for all text in these components (set at Tailwind base layer)
- Border radius: `rounded-md` (8px) throughout

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 3 / apps/web
