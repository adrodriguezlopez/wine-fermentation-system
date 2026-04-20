---
name: nextjs-app-router
description: Use when building Next.js 14+ features with App Router — route groups, client/server components, layouts, API routes, dev proxy rewrites, or configuring next.config.ts
---

# Next.js App Router

## Overview

Next.js 14 App Router uses React Server Components by default. All components are server components unless you add `"use client"` at the top. This project uses **all client components** (no SSR needed — data comes from a separate backend API).

## Key Rules

- `app/` directory = App Router (not `pages/`)
- Default: Server Component. Add `"use client"` for interactivity, state, hooks, browser APIs
- Layouts persist across navigation — don't put per-page state in layouts
- `loading.tsx` = automatic Suspense boundary for a route segment
- `error.tsx` = error boundary (must be `"use client"`)
- Route groups `(name)/` organize routes without affecting URL paths

## Route Structure (This Project)

```
app/
  (auth)/                  # No layout shell — login pages
    login/page.tsx
    register/page.tsx
  (dashboard)/             # With sidebar layout
    layout.tsx             # Sidebar + nav wrapper
    fermentations/
      page.tsx             # List
      [id]/page.tsx        # Detail
    alerts/page.tsx
    settings/page.tsx
  layout.tsx               # Root layout: fonts, providers
  page.tsx                 # Redirect → /fermentations
```

## Component Pattern

Since ALL components are client components here, put `"use client"` at the top of every component file:

```tsx
"use client";

import { useState } from "react";

export function MyComponent() {
  const [value, setValue] = useState("");
  return <input value={value} onChange={e => setValue(e.target.value)} />;
}
```

## Dev Proxy (next.config.ts)

Backend runs on separate ports. Rewrite API calls in development:

```ts
// next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/auth/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
      {
        source: "/api/fermentation/:path*",
        destination: "http://localhost:8001/api/:path*",
      },
      {
        source: "/api/analysis/:path*",
        destination: "http://localhost:8002/api/:path*",
      },
      {
        source: "/api/alerts/:path*",
        destination: "http://localhost:8003/api/:path*",
      },
    ];
  },
};

export default nextConfig;
```

## Providers Setup (Root Layout)

```tsx
// app/layout.tsx
import { QueryProvider } from "@/providers/query-provider";
import { AuthProvider } from "@/providers/auth-provider";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
```

QueryProvider must be a `"use client"` component wrapping `QueryClientProvider`.

## Navigation

```tsx
import { useRouter } from "next/navigation";  // App Router (NOT next/router)
import Link from "next/link";

// Programmatic:
const router = useRouter();
router.push("/fermentations");

// Declarative:
<Link href="/fermentations/123">View</Link>
```

## Dynamic Routes

```
app/fermentations/[id]/page.tsx
```

```tsx
"use client";
export default function Page({ params }: { params: { id: string } }) {
  const { id } = params;
  // use id to fetch data
}
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `useRouter` from `next/router` | Use `next/navigation` in App Router |
| Putting `QueryClientProvider` in Server Component | Wrap in `"use client"` component |
| Accessing `params` without destructuring | `params.id` not `params['id']` in page props |
| Using `pages/` patterns (getServerSideProps) | App Router uses React hooks + TanStack Query |
