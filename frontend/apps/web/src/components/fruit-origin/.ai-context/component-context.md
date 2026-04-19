# Component Context: Fruit Origin Components (`apps/web/src/components/fruit-origin/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **API Reference**: Fruit origin endpoints in `.github/skills/wine-frontend-context/SKILL.md`

## Component responsibility

**Vineyard and harvest lot management UI**. Vineyards are the physical growing locations; harvest lots are individual fruit batches harvested from a vineyard block. Harvest lots are linked to fermentations (and blends) to track fruit provenance.

## Components

### `VineyardTable.tsx`
Table of all vineyards for the current winery. Columns: code, name, harvest lot count, notes excerpt, edit/delete actions. Row click navigates to vineyard detail. "New Vineyard" button.

### `VineyardForm.tsx`
React Hook Form. Fields: code (auto-uppercased), name, notes.  
Create: `POST /vineyards/`, Edit: `PATCH /vineyards/{id}`.

### `HarvestLotTable.tsx`
Table nested under vineyard detail page. Columns: code, harvest date, grape variety, weight kg, brix at harvest. "New Harvest Lot" button links to lot creation form.

### `HarvestLotForm.tsx`
React Hook Form. Fields: block ID, code, harvest date, weight kg, brix at harvest, brix method, grape variety, clone, rootstock, pick method (machine/hand), field temperature °C, notes.  
Create: `POST /harvest-lots/`.  
All numeric fields (weight, brix, temp) rendered with DM Mono input styling.

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 3 / apps/web
