# Component Context: Mobile Profile (`apps/mobile/components/profile/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Screen**: `app/(tabs)/profile/index.tsx`

## Component responsibility

**User profile and session management** for the mobile app. Shows current user info, winery context, and the logout button which clears SecureStore tokens and redirects to login.

## Components

### `UserInfoCard.tsx`
Card displaying:
- User full name (large, bold)
- User email (muted)
- Role badge (`<StatusBadge>` with WINEMAKER label)
- Winery name (subheading)
- Winery code in DM Mono

Data from `useCurrentUser()` hook.

### `LogoutButton.tsx`
Full-width destructive button at bottom of profile screen. Label: "Sign Out".  
On press: calls `authApi.logout` (if online), clears `SecureStore` tokens via `SecureStoreTokenStorage.clear()`, clears TanStack Query cache, navigates to `/(auth)/login`.  
Works offline: tokens are always cleared locally even if the API call fails.

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 4
