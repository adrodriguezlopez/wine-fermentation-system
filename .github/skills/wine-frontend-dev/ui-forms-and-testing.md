# UI, Forms, And Testing

## UI Composition Reality

The current reusable UI footprint is small.

Real reusable components today are concentrated in layout pieces, especially:

- `src/components/layout/sidebar.tsx`
- `src/components/layout/topbar.tsx`
- `src/components/layout/admin-layout.tsx`

Most domain component folders are placeholders.

Build from that reality:

- prefer small, local UI first
- extract only after a second real use case appears
- keep naming domain-specific when the component is tied to fermentation/protocol behavior

## Server vs Client Component Rule

Default to server components.

Add `"use client"` only when the component needs:

- React state or effects
- browser-only APIs
- event handlers
- client-side stores
- TanStack Query hooks

Do not add `"use client"` at layout/page level out of habit.

## Forms

The web app already depends on:

- `react-hook-form`
- `zod`
- `@hookform/resolvers`

Preferred form approach:

1. define or reuse a typed domain shape
2. create a Zod schema near the form unless it is shared across multiple surfaces
3. use React Hook Form for control and validation wiring
4. keep submission logic close to the action, not buried in generic abstractions too early

Move form schemas into shared code only when multiple apps or screens genuinely reuse them.

## Responsive Behavior

Use mobile-first Tailwind styling.

Because the current UI surface is still small, favor practical responsiveness over premature design-system expansion:

- make layout shells robust first
- make tables/cards degrade cleanly on narrow screens
- avoid adding a complex charting stack until a real screen needs it

## Testing Reality

Current web testing uses:

- `vitest`
- `@testing-library/react`
- `@testing-library/jest-dom`
- `jsdom`

Existing examples include:

- `src/app/(auth)/login/login-page.test.tsx`
- `src/components/layout/admin-layout.test.tsx`

Match existing patterns before inventing a new frontend test style.

## Validation Expectations

After UI or form changes, prefer this order:

1. targeted test if one exists
2. `pnpm --filter @wine/web type-check`
3. `pnpm --filter @wine/web test`
4. `pnpm --filter @wine/web lint`

If the task changes a route layout or auth-aware shell behavior, combine code validation with a direct read of the affected route files to confirm composition still makes sense.