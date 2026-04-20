# Component Context: Protocol Components (`apps/web/src/components/protocols/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **API Reference**: Protocol endpoints in `.github/skills/wine-frontend-context/SKILL.md`

## Component responsibility

**Protocol template management UI** — creating, editing, cloning, and managing step definitions for fermentation protocols. Protocols are the winery's master recipes; winemakers execute them against active fermentations.

## Components

### `ProtocolTable.tsx`
Table of all protocols. Columns: varietal name, varietal code, version, status (active/draft), step count, "Clone" button per row. Clone calls `protocolApi.cloneProtocol` with a new version string prompt. "New Protocol" button links to `/protocols/new`.

### `ProtocolForm.tsx`
React Hook Form + `ProtocolSchema`.  
Fields: varietal code, varietal name, version (semver), expected duration days, description (textarea).  
Works in both create mode (`POST /protocols`) and edit mode (`PATCH /protocols/{id}`).  
Activate button (ADMIN only) → `POST /protocols/{id}/activate`.

### `StepsList.tsx`
Ordered list of protocol steps with drag-to-reorder. Each step shows: sequence number, step type label, duration, threshold values summary. Add step button at bottom. Edit and delete per row.  
Uses `@dnd-kit/core` for drag ordering — reorder triggers `PATCH /protocols/{id}/steps/{sid}` for each affected step.

### `ProtocolStepForm.tsx`
Modal form for adding/editing a protocol step.  
React Hook Form + `ProtocolStepSchema`.  
Fields: step type (select from `StepType` enum), sequence (auto-incremented but editable), duration hours, threshold values (key-value pairs for temperature min/max, density target, etc.).

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 3 / apps/web
