# Implementing Login and Token Refresh in React — Wine Fermentation System

## Auth Endpoints (from skill)

**Login:**
```
POST /api/v1/auth/login
Content-Type: application/json

{ "email": "winemaker@bodega.com", "password": "..." }
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "email": "...", "role": "WINEMAKER", "winery_id": 1 }
}
```

**Refresh:**
```
POST /api/v1/auth/refresh
{ "refresh_token": "eyJ..." }
```

**Current user:**
```
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

---

## Token Storage Strategy

- `access_token` → **memory only** (Zustand store), NOT localStorage — prevents XSS theft
- `refresh_token` → `HttpOnly` cookie (set by server) OR localStorage if server doesn't support cookies

---

## Axios Interceptor: 401 → refresh → retry

```ts
// lib/api-client.ts
import axios from 'axios';
import { useAuthStore } from '@/stores/auth.store';

const api = axios.create({ baseURL: '/api/v1' });

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{ resolve: Function; reject: Function }> = [];

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) =>
          failedQueue.push({ resolve, reject })
        ).then((token) => {
          original.headers.Authorization = `Bearer ${token}`;
          return api(original);
        });
      }
      original._retry = true;
      isRefreshing = true;
      try {
        const refreshToken = useAuthStore.getState().refreshToken;
        const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken });
        useAuthStore.getState().setAccessToken(data.access_token);
        failedQueue.forEach(p => p.resolve(data.access_token));
        failedQueue = [];
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch (err) {
        failedQueue.forEach(p => p.reject(err));
        failedQueue = [];
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);
```

---

## Role-Based UI

The `user.role` field is either `WINEMAKER` or `ADMIN`. Use it to conditionally render admin sections:

```tsx
const { user } = useAuthStore();
{user?.role === 'ADMIN' && <AdminPanel />}
```

---

## Load User Context on App Start

```ts
// On app mount, if accessToken exists in memory:
const user = await api.get('/auth/me');
useAuthStore.getState().setUser(user.data);
```
