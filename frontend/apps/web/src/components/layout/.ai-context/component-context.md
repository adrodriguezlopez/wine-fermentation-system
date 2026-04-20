# Component Context: Layout (`apps/web/src/components/layout/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions

## Component responsibility

**Shell components** that wrap all dashboard pages: sidebar navigation, top bar, and access control wrappers. These components are rendered once and persist across route changes.

## Files

### `AdminLayout.tsx`
Top-level shell: `AdminSidebar` on the left, `TopBar` across the top, `<main>` content area to the right. Handles responsive collapse of sidebar. Framer Motion page transition wrapper for content area.

### `AdminSidebar.tsx`
Left navigation bar. Nav items with icons (lucide-react):
- Dashboard
- Fermentations
- Protocols
- Fruit Origin
- Admin > Wineries *(only rendered for ADMIN role — reads `useRole()`)*

Active item highlighted with `#8B1A2E` accent. Winery name displayed at top (from `useCurrentUser().wineryId` → winery name lookup).

### `TopBar.tsx`
Horizontal top bar: page title (from route), spacer, current user name + role badge, logout button. Logout calls `useAuth().logout()`.

### `ProtectedRoute.tsx`
Wrapper component. Checks `useAuth().isAuthenticated`. If false, redirects to `/login`. Renders `null` during auth check to avoid flash of unauthenticated content.

### `RoleGuard.tsx`
```typescript
<RoleGuard requiredRole="ADMIN">
  <AdminOnlyContent />
</RoleGuard>
```
Reads `useRole()`. If current user's role does not satisfy `requiredRole`, either redirects to `/403` (for page-level guards) or renders `null` (for inline section guards). `redirectTo` prop controls behavior.

### `PageHeader.tsx`
Reusable page-level header: title (Cormorant Garamond), optional breadcrumb, optional action slot (right-aligned). Used at the top of every page.

## Design notes

- Sidebar background: `#1A1A2E` (dark navy) with `#FAFAF8` text and `#8B1A2E` active accent
- TopBar background: `#FFFFFF` with bottom border `#E5E7EB`
- Sidebar nav item transitions: 150ms ease on background color
- Page content Framer Motion: `initial={{ opacity: 0, y: 8 }}` → `animate={{ opacity: 1, y: 0 }}` on route change

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 3 / apps/web
