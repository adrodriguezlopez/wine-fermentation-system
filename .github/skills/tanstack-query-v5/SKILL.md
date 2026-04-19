---
name: tanstack-query-v5
description: Use when writing data fetching with TanStack Query v5 (React Query) — useQuery, useMutation, QueryClient setup, polling, cache invalidation, or migrating v4 patterns to v5
---

# TanStack Query v5

## Overview

TanStack Query v5 has **breaking changes from v4**. The API is more consistent but different. Key change: everything goes through `queryOptions()` and the generic types moved.

## Setup

```tsx
// providers/query-provider.tsx
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,   // 30s — matches backend polling interval
        retry: 1,
      },
    },
  }));
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
```

## useQuery (v5 pattern)

```tsx
import { useQuery } from "@tanstack/react-query";
import { getFermentations } from "@/lib/api";

// v5: no separate TData/TError generics on the hook — use queryOptions() instead
const { data, isLoading, isError, error } = useQuery({
  queryKey: ["fermentations", wineryId],
  queryFn: () => getFermentations(wineryId),
  refetchInterval: 30_000,  // polling
});
```

## queryOptions() Helper (v5 — preferred)

Define query once, use everywhere (component + prefetch + invalidate):

```tsx
// lib/queries/fermentation-queries.ts
import { queryOptions } from "@tanstack/react-query";
import { getFermentation } from "@/lib/api";

export const fermentationQuery = (id: string) => queryOptions({
  queryKey: ["fermentation", id],
  queryFn: () => getFermentation(id),
  staleTime: 30_000,
});

// In component:
const { data } = useQuery(fermentationQuery(id));

// Prefetch:
await queryClient.prefetchQuery(fermentationQuery(id));
```

## useMutation (v5 pattern)

```tsx
import { useMutation, useQueryClient } from "@tanstack/react-query";

// v5: mutationFn is required, no separate generic for variables
const mutation = useMutation({
  mutationFn: (data: CreateFermentationDto) => createFermentation(data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["fermentations"] });
  },
  onError: (error) => {
    console.error("Failed:", error);
  },
});

// Call it:
mutation.mutate({ name: "Batch 2024" });
// Or async:
await mutation.mutateAsync({ name: "Batch 2024" });
```

## v4 → v5 Migration Cheatsheet

| v4 | v5 |
|----|-----|
| `useQuery(key, fn, options)` | `useQuery({ queryKey, queryFn, ...options })` |
| `useMutation(fn, options)` | `useMutation({ mutationFn: fn, ...options })` |
| `useQuery<Data, Error>(...)` | Use `queryOptions<Data, Error>(...)` |
| `onSuccess` in `useQuery` | Removed — use `useEffect` or server callbacks |
| `keepPreviousData: true` | `placeholderData: keepPreviousData` |
| `isLoading` (no data + fetching) | `isPending` (no data) vs `isFetching` (any fetch) |
| `status === 'loading'` | `status === 'pending'` |
| `getQueryData(key)` | Same, unchanged |
| `setQueryData(key, data)` | Same, unchanged |
| `invalidateQueries(key)` | `invalidateQueries({ queryKey: key })` |

## Polling Pattern (30s — This Project)

```tsx
const { data: alerts } = useQuery({
  queryKey: ["alerts", wineryId],
  queryFn: () => getActiveAlerts(wineryId),
  refetchInterval: 30_000,
  refetchIntervalInBackground: false,  // pause when tab is hidden
});
```

## Infinite Scroll / Pagination

```tsx
import { useInfiniteQuery } from "@tanstack/react-query";

const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ["fermentations"],
  queryFn: ({ pageParam }) => getFermentations({ cursor: pageParam }),
  initialPageParam: undefined,              // v5: required
  getNextPageParam: (lastPage) => lastPage.next_cursor,
});
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `useQuery(key, fn)` positional args | v5 requires object: `useQuery({ queryKey, queryFn })` |
| `status === 'loading'` | Use `status === 'pending'` in v5 |
| Expecting `onSuccess` in `useQuery` | Removed in v5; use `useEffect` watching `data` |
| `isLoading` for "any fetch" | Use `isFetching`; `isLoading` = `isPending && isFetching` |
| Missing `initialPageParam` in `useInfiniteQuery` | Required in v5 |
