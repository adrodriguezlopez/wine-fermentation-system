---
name: turborepo-monorepo
description: Use when working in a Turborepo monorepo — running tasks, adding packages, configuring turbo.json, path aliases, pnpm workspaces, or sharing code between apps
---

# Turborepo Monorepo

## Overview

Turborepo orchestrates tasks across a monorepo with caching and parallelism. This project uses **pnpm workspaces** with Turborepo.

## Workspace Structure (This Project)

```
frontend/
  apps/
    web/          → Next.js 14 web app
    mobile/       → Expo SDK 52 mobile app
  packages/
    shared/       → API client, hooks, TanStack Query keys
    ui/           → Zod schemas, formatters, constants
  turbo.json
  pnpm-workspace.yaml
  package.json
```

## Running Tasks

```bash
# From frontend/ root — runs across all apps/packages:
pnpm turbo dev          # Start all dev servers
pnpm turbo build        # Build all apps
pnpm turbo test         # Run all tests
pnpm turbo lint         # Lint all packages

# Single app only:
pnpm --filter web dev
pnpm --filter mobile start
pnpm --filter shared build

# With turbo directly:
turbo run dev --filter=web
```

## turbo.json

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "test": {
      "dependsOn": ["^build"]
    },
    "lint": {}
  }
}
```

`"^build"` means "build dependencies first before building this package."

## pnpm-workspace.yaml

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

## Adding a Shared Package Dependency

From an app that needs to use `packages/shared`:

```bash
# Add shared package as dependency of web app:
pnpm --filter web add @wine/shared
```

In `apps/web/package.json`:
```json
{
  "dependencies": {
    "@wine/shared": "workspace:*"
  }
}
```

## Path Aliases

Each package exports via its `package.json` `exports` field and TypeScript paths.

`packages/shared/package.json`:
```json
{
  "name": "@wine/shared",
  "exports": {
    ".": "./src/index.ts"
  }
}
```

`apps/web/tsconfig.json`:
```json
{
  "compilerOptions": {
    "paths": {
      "@wine/shared": ["../../packages/shared/src/index.ts"],
      "@wine/ui": ["../../packages/ui/src/index.ts"],
      "@/*": ["./src/*"]
    }
  }
}
```

## Package Exports Pattern

Each package has a barrel `src/index.ts` that re-exports everything:

```ts
// packages/shared/src/index.ts
export * from "./api/client";
export * from "./queries/fermentation-queries";
export * from "./hooks/use-auth";
export type * from "./types";
```

## Adding a New Package

```bash
mkdir packages/my-package
cd packages/my-package
pnpm init
```

Then add it to `turbo.json` if it has build tasks.

## Common Commands Reference

| Task | Command |
|------|---------|
| Install all deps | `pnpm install` (from `frontend/`) |
| Add dep to one app | `pnpm --filter web add axios` |
| Add dev dep to root | `pnpm add -D -w typescript` |
| Run single task | `turbo run build --filter=web` |
| Clear turbo cache | `turbo run build --force` |
| List packages | `pnpm ls -r --depth 0` |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Running `npm install` in an app | Always use `pnpm install` from `frontend/` root |
| Importing across packages without exports field | Add `exports` to `package.json` and rebuild |
| Circular dependency between packages | `ui` should not import from `shared`; only apps import from both |
| Forgetting `workspace:*` version | Workspace packages use `"workspace:*"` not a version number |
| Cache stale after changing package | Run `turbo run build --force` to bypass cache |
