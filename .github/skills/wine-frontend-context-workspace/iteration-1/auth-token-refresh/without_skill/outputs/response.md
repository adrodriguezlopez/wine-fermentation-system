# Implementing Login and Token Refresh in a React Frontend

## 1. Overview of the Auth Flow

1. User submits credentials → server returns `access_token` (short-lived, ~15 min) + `refresh_token` (long-lived, ~7 days)
2. Frontend stores tokens securely
3. Every API request includes the `access_token` in the `Authorization` header
4. When the `access_token` expires (HTTP 401), the frontend uses the `refresh_token` to get a new one
5. If `refresh_token` is expired too, log the user out

## 2. Token Storage

Store `access_token` in memory/React state and `refresh_token` in an `HttpOnly` cookie (set by the server) for best security. For simpler internal tools, `localStorage` works.

## 3. Auth Context

```jsx
import { createContext, useContext, useState, useCallback } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(
    () => localStorage.getItem('access_token') || null
  );

  const login = useCallback(async (username, password) => {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new Error('Login failed');
    const data = await res.json();
    setAccessToken(data.access_token);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
  }, []);

  const logout = useCallback(() => {
    setAccessToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }, []);

  return (
    <AuthContext.Provider value={{ accessToken, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

## 4. Axios Interceptor for Auto Token Refresh

```js
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const orig = error.config;
    if (error.response?.status === 401 && !orig._retry) {
      orig._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const { data } = await axios.post('/auth/refresh', { refresh_token: refreshToken });
        localStorage.setItem('access_token', data.access_token);
        orig.headers.Authorization = `Bearer ${data.access_token}`;
        return api(orig);
      } catch (err) {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(err);
      }
    }
    return Promise.reject(error);
  }
);
```

## 5. Security Notes

- Prefer `HttpOnly` cookies for refresh tokens to prevent XSS theft
- Use HTTPS in production
- Keep access tokens short-lived (5–15 min)
