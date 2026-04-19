# Frontend Foundation — Iteration 3: apps/web

> **Source plan:** `docs/superpowers/plans/2026-04-18-frontend-foundation.md` (Tasks 10–15)  
> **Governing ADR:** [ADR-045](../../.ai-context/adr/ADR-045-frontend-architecture.md)  
> **Skills to load before starting:**  
> - `wine-frontend-context` → `.github/skills/wine-frontend-context/SKILL.md`  
> - `nextjs-app-router` → `.github/skills/nextjs-app-router/SKILL.md`  
> - `shadcn-ui` → `.github/skills/shadcn-ui/SKILL.md`

**Goal:** Deliver a working `apps/web` Next.js 14 application — scaffold, providers, login page, dashboard layout with role guard. All tests green. Dev server starts and proxies to backend.

**Deliverable:** `apps/web` with login route, dashboard route group protected by role guard, Shadcn/ui wine theme. `turbo build` and `turbo test` both succeed. `pnpm dev` starts the dev server at `localhost:3000`.

**Prerequisite:** Iteration 2 complete — `@wine/shared` resolves as a workspace dependency.

**Branch:** `feat/frontend-foundation-iteration-3` (branch from main after Iteration 2 is merged)

---

## Pre-flight

- [ ] Read `.github/skills/wine-frontend-context/SKILL.md`
- [ ] Read `.github/skills/nextjs-app-router/SKILL.md`
- [ ] Read `.github/skills/shadcn-ui/SKILL.md`
- [ ] Confirm Iteration 2 is merged: `git log --oneline -3`
- [ ] Create branch: `git checkout -b feat/frontend-foundation-iteration-3`
- [ ] Confirm `@wine/shared` resolves: `cd frontend && pnpm install`

---

## Task 10: apps/web — Next.js 14 scaffold

**Objective:** Initialize `apps/web` with Next.js 14 App Router, Tailwind CSS, and Shadcn/ui wine theme. Wire `next.config.ts` dev proxies.

### Steps

**10.1** Create `frontend/apps/web/package.json`:
```json
{
  "name": "@wine/web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "vitest run",
    "test:watch": "vitest",
    "type-check": "tsc --noEmit",
    "lint": "eslint src"
  },
  "dependencies": {
    "@wine/shared": "workspace:*",
    "@wine/ui": "workspace:*",
    "next": "14.2.3",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.5.0",
    "react-hook-form": "^7.51.0",
    "@hookform/resolvers": "^3.3.4",
    "axios": "^1.6.0",
    "js-cookie": "^3.0.5"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "@types/js-cookie": "^3.0.6",
    "@vitejs/plugin-react": "^4.2.0",
    "@testing-library/react": "^14.3.0",
    "@testing-library/user-event": "^14.5.0",
    "@testing-library/jest-dom": "^6.4.0",
    "msw": "^2.3.0",
    "typescript": "^5",
    "vitest": "^1.6.0",
    "jsdom": "^24.0.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "eslint": "^8",
    "eslint-config-next": "14.2.3"
  }
}
```

**10.2** Create `frontend/apps/web/tsconfig.json`:
```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

**10.3** Create `frontend/apps/web/next.config.ts` with dev proxy rewrites:
```typescript
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/fermentation/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/api/winery/:path*',
        destination: 'http://localhost:8001/api/:path*',
      },
      {
        source: '/api/fruit-origin/:path*',
        destination: 'http://localhost:8002/api/:path*',
      },
      {
        source: '/api/analysis/:path*',
        destination: 'http://localhost:8003/api/:path*',
      },
    ]
  },
}

export default nextConfig
```

**10.4** Create `frontend/apps/web/tailwind.config.ts` with wine theme:
```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        wine: {
          50: '#fdf2f4',
          100: '#fce7ea',
          200: '#f9d0d7',
          300: '#f4aab6',
          400: '#ec7a8e',
          500: '#e04d68',
          600: '#cc2d4d',
          700: '#ab2040',
          800: '#8B1A2E',
          900: '#7a1829',
          950: '#430a15',
        },
      },
      fontFamily: {
        display: ['Cormorant Garamond', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
```

**10.5** Create `frontend/apps/web/postcss.config.js`:
```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

**10.6** Initialize Shadcn/ui by creating `frontend/apps/web/components.json`:
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/app/globals.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

**10.7** Create `frontend/apps/web/src/app/globals.css` with CSS variables for wine theme:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap');

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 349 69% 32%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 349 69% 32%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 349 69% 50%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 349 69% 50%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

**10.8** Create `frontend/apps/web/src/lib/utils.ts` (Shadcn/ui utility):
```typescript
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

**10.9** Update `frontend/apps/web/package.json` to add `clsx` and `tailwind-merge` to dependencies:
- Add `"clsx": "^2.1.0"` and `"tailwind-merge": "^2.3.0"` to `dependencies`

**10.10** Create minimal `frontend/apps/web/src/app/layout.tsx`:
```tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Wine Fermentation System',
  description: 'Monitor and manage your wine fermentation processes',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
```

**10.11** Create `frontend/apps/web/vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    coverage: {
      reporter: ['text', 'json', 'html'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

**10.12** Create `frontend/apps/web/src/test/setup.ts`:
```typescript
import '@testing-library/jest-dom'
```

**Verification:**
```bash
cd frontend && pnpm install
pnpm --filter @wine/web type-check
```
Expected: zero TypeScript errors.

---

## Task 11: Providers + ApiClient singleton + Zustand auth store

**Objective:** Wire up the React context providers (`QueryProvider`, `AuthProvider`), the singleton `ApiClient` instance with `CookieTokenStorage`, and the Zustand auth store.

### Steps

**11.1** Create `frontend/apps/web/src/lib/api-client.ts`:
```typescript
import { ApiClient } from '@wine/shared'
import { CookieTokenStorage } from '@wine/shared'

export const apiClient = new ApiClient({
  storage: new CookieTokenStorage(),
  baseUrls: {
    fermentation: '/api/fermentation',
    winery: '/api/winery',
    fruitOrigin: '/api/fruit-origin',
    analysis: '/api/analysis',
  },
})
```

**11.2** Create `frontend/apps/web/src/stores/auth-store.ts`:
```typescript
import { create } from 'zustand'
import type { UserResponse } from '@wine/shared'

interface AuthState {
  user: UserResponse | null
  setUser: (user: UserResponse | null) => void
  clearUser: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  clearUser: () => set({ user: null }),
}))
```

**11.3** Create `frontend/apps/web/src/providers/query-provider.tsx`:
```tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}
```

**11.4** Create `frontend/apps/web/src/providers/auth-provider.tsx`:
```tsx
'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { makeUseCurrentUser } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth-store'

const useCurrentUser = makeUseCurrentUser(apiClient)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const setUser = useAuthStore((s) => s.setUser)
  const clearUser = useAuthStore((s) => s.clearUser)

  const { data: user, isError } = useCurrentUser()

  useEffect(() => {
    if (user) {
      setUser(user)
    }
  }, [user, setUser])

  useEffect(() => {
    if (isError) {
      clearUser()
      if (!pathname.startsWith('/login')) {
        router.replace('/login')
      }
    }
  }, [isError, clearUser, router, pathname])

  return <>{children}</>
}
```

**11.5** Update `frontend/apps/web/src/app/layout.tsx` to wrap with providers:
```tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { QueryProvider } from '@/providers/query-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Wine Fermentation System',
  description: 'Monitor and manage your wine fermentation processes',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
```

**11.6** Write failing tests for Zustand auth store — `frontend/apps/web/src/stores/auth-store.test.ts`:
```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from './auth-store'

describe('useAuthStore', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null })
  })

  it('initializes with null user', () => {
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('setUser stores the user', () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      role: 'WINEMAKER' as const,
      winery_id: 'w1',
      is_active: true,
    }
    useAuthStore.getState().setUser(mockUser)
    expect(useAuthStore.getState().user).toEqual(mockUser)
  })

  it('clearUser resets to null', () => {
    useAuthStore.setState({ user: { id: '1' } as any })
    useAuthStore.getState().clearUser()
    expect(useAuthStore.getState().user).toBeNull()
  })
})
```

**Verification:**
```bash
pnpm --filter @wine/web test
```
Expected: auth store tests pass (3 passing).

---

## Task 12: Login page

**Objective:** Implement the `(auth)/login` route — email/password form with react-hook-form + Zod validation, calls `makeUseAuth(apiClient).login()`, redirects on success.

### Steps

**12.1** Write failing tests first — `frontend/apps/web/src/app/(auth)/login/login-page.test.tsx`:
```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LoginPage from './page'

// Mock the api client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    auth: { login: vi.fn(), refresh: vi.fn(), me: vi.fn() },
  },
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('LoginPage', () => {
  it('renders email field, password field, and sign-in button', () => {
    render(<LoginPage />, { wrapper })
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows validation error on empty submit', async () => {
    const user = userEvent.setup()
    render(<LoginPage />, { wrapper })
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument()
  })

  it('shows password validation error on empty password', async () => {
    const user = userEvent.setup()
    render(<LoginPage />, { wrapper })
    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    expect(await screen.findByText(/password is required/i)).toBeInTheDocument()
  })
})
```

**12.2** Run tests — expect RED (LoginPage doesn't exist yet):
```bash
pnpm --filter @wine/web test -- --reporter=verbose 2>&1 | head -30
```

**12.3** Create the route directory structure:
```
frontend/apps/web/src/app/(auth)/login/
```

**12.4** Create `frontend/apps/web/src/app/(auth)/login/page.tsx`:
```tsx
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { makeUseAuth } from '@wine/shared'
import { apiClient } from '@/lib/api-client'

const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})

type LoginFormData = z.infer<typeof loginSchema>

const useAuth = makeUseAuth(apiClient)

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoggingIn } = useAuth()

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data)
      router.replace('/dashboard')
    } catch {
      setError('root', {
        message: 'Invalid email or password',
      })
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-wine-50 to-wine-100">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-8">
        <div className="mb-8 text-center">
          <h1 className="font-display text-3xl font-semibold text-wine-800">
            Wine Fermentation
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Sign in to your account
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-foreground mb-1.5"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              {...register('email')}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              placeholder="you@winery.com"
            />
            {errors.email && (
              <p className="mt-1.5 text-xs text-destructive">
                {errors.email.message}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-foreground mb-1.5"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register('password')}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
            {errors.password && (
              <p className="mt-1.5 text-xs text-destructive">
                {errors.password.message}
              </p>
            )}
          </div>

          {errors.root && (
            <p className="text-sm text-destructive text-center">
              {errors.root.message}
            </p>
          )}

          <button
            type="submit"
            disabled={isLoggingIn}
            className="w-full rounded-md bg-wine-800 px-4 py-2.5 text-sm font-semibold text-white hover:bg-wine-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wine-800 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoggingIn ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
```

**12.5** Create `frontend/apps/web/src/app/(auth)/layout.tsx` (unauthenticated layout — no AuthProvider):
```tsx
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
```

**12.6** Run tests — expect GREEN:
```bash
pnpm --filter @wine/web test -- --reporter=verbose 2>&1 | head -40
```
Expected: 3 login page tests pass.

---

## Task 13: Dashboard layout + role guard

**Objective:** Implement the `(dashboard)` route group with `AdminLayout` (role guard blocking WINEMAKER from `/admin/*`), `Sidebar`, `Topbar`, and a placeholder dashboard page.

### Steps

**13.1** Write failing tests first — `frontend/apps/web/src/components/layout/admin-layout.test.tsx`:
```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AdminLayout from './admin-layout'

const mockReplace = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: mockReplace }),
  usePathname: () => '/admin/users',
}))

vi.mock('@/stores/auth-store', () => ({
  useAuthStore: (selector: any) =>
    selector({
      user: {
        id: '1',
        email: 'winemaker@test.com',
        role: 'WINEMAKER',
        winery_id: 'w1',
        is_active: true,
      },
    }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('AdminLayout', () => {
  it('redirects WINEMAKER user away from /admin/* routes', () => {
    render(
      <AdminLayout>
        <div>admin content</div>
      </AdminLayout>,
      { wrapper }
    )
    expect(mockReplace).toHaveBeenCalledWith('/403')
  })
})
```

**13.2** Run tests — expect RED (AdminLayout doesn't exist yet):
```bash
pnpm --filter @wine/web test -- --reporter=verbose 2>&1 | head -20
```

**13.3** Create `frontend/apps/web/src/components/layout/admin-layout.tsx`:
```tsx
'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuthStore } from '@/stores/auth-store'

interface AdminLayoutProps {
  children: React.ReactNode
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const router = useRouter()
  const pathname = usePathname()
  const user = useAuthStore((s) => s.user)

  useEffect(() => {
    if (user && user.role === 'WINEMAKER' && pathname.startsWith('/admin')) {
      router.replace('/403')
    }
  }, [user, pathname, router])

  if (user?.role === 'WINEMAKER' && pathname.startsWith('/admin')) {
    return null
  }

  return <>{children}</>
}
```

**13.4** Create `frontend/apps/web/src/components/layout/sidebar.tsx`:
```tsx
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuthStore } from '@/stores/auth-store'
import { cn } from '@/lib/utils'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', adminOnly: false },
  { href: '/dashboard/fermentations', label: 'Fermentations', adminOnly: false },
  { href: '/dashboard/alerts', label: 'Alerts', adminOnly: false },
  { href: '/admin/wineries', label: 'Wineries', adminOnly: true },
  { href: '/admin/users', label: 'Users', adminOnly: true },
]

export function Sidebar() {
  const pathname = usePathname()
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'ADMIN'

  const visibleItems = navItems.filter(
    (item) => !item.adminOnly || isAdmin
  )

  return (
    <aside className="w-64 min-h-screen bg-wine-800 text-wine-50 flex flex-col">
      <div className="px-6 py-8">
        <h2 className="font-display text-xl font-semibold tracking-wide">
          Wine Fermentation
        </h2>
      </div>
      <nav className="flex-1 px-3 pb-4">
        <ul className="space-y-1">
          {visibleItems.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  'flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  pathname === item.href
                    ? 'bg-wine-700 text-white'
                    : 'text-wine-200 hover:bg-wine-700 hover:text-white'
                )}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      {user && (
        <div className="px-6 py-4 border-t border-wine-700">
          <p className="text-xs text-wine-300 truncate">{user.email}</p>
          <p className="text-xs text-wine-400">{user.role}</p>
        </div>
      )}
    </aside>
  )
}
```

**13.5** Create `frontend/apps/web/src/components/layout/topbar.tsx`:
```tsx
'use client'

import { useAuthStore } from '@/stores/auth-store'
import { makeUseAuth } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { useRouter } from 'next/navigation'

const useAuth = makeUseAuth(apiClient)

export function Topbar() {
  const user = useAuthStore((s) => s.user)
  const { logout } = useAuth()
  const router = useRouter()

  const handleLogout = async () => {
    await logout()
    router.replace('/login')
  }

  return (
    <header className="h-14 border-b border-border bg-background flex items-center justify-between px-6">
      <div />
      <div className="flex items-center gap-4">
        {user && (
          <span className="text-sm text-muted-foreground">{user.email}</span>
        )}
        <button
          onClick={handleLogout}
          className="text-sm font-medium text-wine-800 hover:text-wine-600 transition-colors"
        >
          Sign out
        </button>
      </div>
    </header>
  )
}
```

**13.6** Create `frontend/apps/web/src/app/(dashboard)/layout.tsx`:
```tsx
import { Sidebar } from '@/components/layout/sidebar'
import { Topbar } from '@/components/layout/topbar'
import { AuthProvider } from '@/providers/auth-provider'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AuthProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Topbar />
          <main className="flex-1 p-6">{children}</main>
        </div>
      </div>
    </AuthProvider>
  )
}
```

**13.7** Create placeholder dashboard page — `frontend/apps/web/src/app/(dashboard)/dashboard/page.tsx`:
```tsx
export default function DashboardPage() {
  return (
    <div>
      <h1 className="font-display text-2xl font-semibold text-wine-800 mb-4">
        Dashboard
      </h1>
      <p className="text-muted-foreground">
        Welcome to the Wine Fermentation System.
      </p>
    </div>
  )
}
```

**13.8** Create 403 page — `frontend/apps/web/src/app/403/page.tsx`:
```tsx
export default function ForbiddenPage() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="font-display text-4xl font-semibold text-wine-800 mb-4">
          403
        </h1>
        <p className="text-muted-foreground">
          You don&apos;t have permission to access this page.
        </p>
      </div>
    </div>
  )
}
```

**13.9** Create root redirect — `frontend/apps/web/src/app/page.tsx`:
```tsx
import { redirect } from 'next/navigation'

export default function HomePage() {
  redirect('/dashboard')
}
```

**13.10** Run tests — expect GREEN:
```bash
pnpm --filter @wine/web test -- --reporter=verbose
```
Expected: admin-layout test passes (WINEMAKER redirects to `/403`).

---

## Task 14: Environment config + .env.local

**Objective:** Create `.env.local` for the web app and add `NEXT_PUBLIC_*` constants for backend URLs (used in non-proxy scenarios like server-side rendering or Docker).

### Steps

**14.1** Create `frontend/apps/web/.env.local`:
```
NEXT_PUBLIC_FERMENTATION_API_URL=http://localhost:8000
NEXT_PUBLIC_WINERY_API_URL=http://localhost:8001
NEXT_PUBLIC_FRUIT_ORIGIN_API_URL=http://localhost:8002
NEXT_PUBLIC_ANALYSIS_API_URL=http://localhost:8003
```

**14.2** Create `frontend/apps/web/.env.example` (safe to commit):
```
NEXT_PUBLIC_FERMENTATION_API_URL=http://localhost:8000
NEXT_PUBLIC_WINERY_API_URL=http://localhost:8001
NEXT_PUBLIC_FRUIT_ORIGIN_API_URL=http://localhost:8002
NEXT_PUBLIC_ANALYSIS_API_URL=http://localhost:8003
```

**14.3** Ensure `.env.local` is gitignored. Check `frontend/.gitignore` — if it doesn't exist, create it:
```
# Dependencies
node_modules/
.pnp
.pnp.js

# Build outputs
.next/
out/
dist/
build/

# Environment files
.env.local
.env.*.local

# Turborepo
.turbo/

# Testing
coverage/

# Misc
.DS_Store
*.pem
```

**Verification:**
- `cat frontend/apps/web/.env.example` — readable, no secrets
- `cat frontend/.gitignore` — `.env.local` is listed

---

## Task 15: Final integration check

**Objective:** Verify the entire monorepo builds, all tests pass, TypeScript is clean, and the dev server starts correctly.

### Steps

**15.1** Install all dependencies from workspace root:
```bash
cd frontend && pnpm install
```

**15.2** Run full type-check across all packages:
```bash
pnpm type-check
```
Expected: zero TypeScript errors across `packages/ui`, `packages/shared`, `apps/web`.

**15.3** Run all tests:
```bash
pnpm test
```
Expected: all tests pass. Summary should show:
- `packages/ui`: schemas, formatters, constants tests ✓
- `packages/shared`: ApiClient, storage, hooks, sync tests ✓
- `apps/web`: auth store, login page, admin-layout tests ✓

**15.4** Run turbo build:
```bash
pnpm build
```
Expected: all three packages build successfully.

**15.5** Smoke-test the dev server (backend not required — just check it starts):
```bash
cd apps/web && pnpm dev &
sleep 5
curl -s http://localhost:3000 | head -5
kill %1
```
Expected: Next.js server responds (HTML or redirect).

**15.6** Verify no zero-React constraint violations in `packages/ui`:
```bash
grep -r "import React\|from 'react'\|from \"react\"" frontend/packages/ui/src/
```
Expected: no matches.

**15.7** Verify `winery_id` is never passed as a prop in `apps/web`:
```bash
grep -r "winery_id" frontend/apps/web/src/
```
Expected: no matches (or only in type definitions if any are needed there).

**15.8** Commit all work:
```bash
git add frontend/
git commit -m "feat(frontend): apps/web scaffold — Next.js 14, providers, login, dashboard layout

- Next.js 14 App Router with Tailwind CSS and Shadcn/ui wine theme
- QueryProvider + AuthProvider wired to @wine/shared ApiClient
- CookieTokenStorage singleton at src/lib/api-client.ts
- Zustand auth store for in-memory user state
- Login page with react-hook-form + Zod validation
- (dashboard) route group with Sidebar + Topbar + AuthProvider
- AdminLayout role guard: WINEMAKER redirected from /admin/* to /403
- Dev proxy rewrites: /api/fermentation|winery|fruit-origin|analysis/* → ports 8000-8003
- All tests passing, zero TypeScript errors

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>"
```

---

## Handoff

Iteration 3 completes the frontend foundation. The full monorepo (`packages/ui`, `packages/shared`, `apps/web`) is now implemented with:

- ✅ All Zod schemas, formatters, and constants in `@wine/ui` (zero React)
- ✅ ApiClient with 401 auto-refresh, all typed API factories, auth/polling hooks in `@wine/shared`
- ✅ Next.js 14 app with login route and protected dashboard route
- ✅ Role guard enforcing `ADMIN`-only access to `/admin/*`
- ✅ Dev proxy routing to all 4 backend microservices
- ✅ `winery_id` never passed as a component prop — enforced architecturally

**Next step after merging:** Connect real backend API calls — replace MSW mocks with live calls to the running FastAPI services on ports 8000–8003.
