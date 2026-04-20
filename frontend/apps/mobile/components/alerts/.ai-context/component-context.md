# Component Context: Mobile Alerts (`apps/mobile/components/alerts/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Note**: Alerts appear in fermentation detail screens — no dedicated alerts tab on mobile

## Component responsibility

**Alert display and action components** for the mobile app. Alerts surface on the fermentation detail screen. The critical design constraint is that **both Acknowledge and Dismiss must always be visible** — they are semantically distinct actions and must never be collapsed.

## Components

### `AlertCard.tsx`
Card for a single fermentation alert.

Content:
- Alert type label (from `ALERT_TYPE_LABEL`)
- Description text
- `formatRelative(created_at)` timestamp
- Severity indicator (colour from `CONFIDENCE_COLOR`)

**Two action buttons always present** (side by side):
1. **Acknowledge** → `POST /alerts/{id}/acknowledge` — marks alert as seen but leaves it visible. Button text changes to "Acknowledged" + shows `formatDateTime(acknowledged_at)` after action. **Never removed from list**.
2. **Dismiss** → `POST /alerts/{id}/dismiss` — removes alert from the list. Confirm before dismiss (brief haptic feedback, no dialog needed on mobile).

**These buttons are never merged into one, never hidden, never replaced by a single action.** Both must render regardless of acknowledge state.

Online-only: if offline, both buttons show as disabled with brief tooltip "Requires connection".

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 4
