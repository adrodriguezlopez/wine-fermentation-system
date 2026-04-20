# Component Context: Storage (`packages/shared/src/storage/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions

## Component responsibility

**Token storage abstraction** — defines a `TokenStorage` interface that decouples the `ApiClient` and auth hooks from the concrete storage mechanism. The web app uses cookies; the mobile app uses Expo SecureStore. Both implement the same interface, making `packages/shared` portable.

## Architecture pattern

Interface + two concrete implementations. `ApiClient` and `useAuth` depend on the `TokenStorage` interface. Apps inject the correct implementation at initialization time.

## Files

### `index.ts` — `TokenStorage` interface
```typescript
interface TokenStorage {
  getAccessToken(): Promise<string | null>
  setAccessToken(token: string): Promise<void>
  getRefreshToken(): Promise<string | null>
  setRefreshToken(token: string): Promise<void>
  clear(): Promise<void>
}
```

### `cookie.ts` — Web implementation
Uses `js-cookie`. Access token stored as a session cookie (expires when browser closes). Refresh token stored with 7-day expiry. Both set with `sameSite: 'strict'`.

```typescript
export class CookieTokenStorage implements TokenStorage { ... }
```

### `secure-store.ts` — Mobile implementation
Uses `expo-secure-store`. Both tokens stored as encrypted key-value pairs in the device keychain.

```typescript
export class SecureStoreTokenStorage implements TokenStorage { ... }
```

## Usage pattern

```typescript
// In apps/web — passed to ApiClient at app initialization
import { CookieTokenStorage } from '@shared/storage/cookie'
const tokenStorage = new CookieTokenStorage()

// In apps/mobile — passed to ApiClient at app initialization
import { SecureStoreTokenStorage } from '@shared/storage/secure-store'
const tokenStorage = new SecureStoreTokenStorage()
```

## Security notes

- Access tokens (15min expiry) stored in cookie/SecureStore — not in `localStorage` or `AsyncStorage`  
- Refresh tokens (7d expiry) stored in the same encrypted location  
- `clear()` is called on logout and on refresh failure — ensures no stale tokens remain  

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 2 / packages/shared
