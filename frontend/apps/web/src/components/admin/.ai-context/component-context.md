# Component Context: Admin Components (`apps/web/src/components/admin/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Access**: ADMIN role only — `<RoleGuard requiredRole="ADMIN">` wraps all these pages

## Component responsibility

**Winery management UI** accessible only to ADMIN role. Admins can create new winery tenants, view all wineries, and update winery details. WINEMAKER role cannot see these routes — the layout guard redirects to `/403`.

## Components

### `WineryTable.tsx`
Table of all wineries in the system (no multi-tenant filter — ADMIN sees everything). Columns: name, code, location, owner email, fermentation count, created date, edit link, soft delete button (with `<ConfirmDialog>`). Paginated. "New Winery" button.

### `WineryForm.tsx`
React Hook Form + `WinerySchema`.  
Fields: name, code (uppercased, 2-10 chars), location, owner_id (user lookup or input).  
Create: `POST /admin/wineries`, Edit: `PATCH /admin/wineries/{id}`.  
Delete: `DELETE /admin/wineries/{id}` — triggers `<ConfirmDialog>` before proceeding.

## Security notes

- These components are only rendered inside `<RoleGuard requiredRole="ADMIN">`
- The layout-level guard (`(dashboard)/layout.tsx`) also redirects WINEMAKER users attempting to navigate to `/admin/*` routes to `/403`
- Double guard: layout-level redirect + component-level `RoleGuard` wrapper

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 3 / apps/web
