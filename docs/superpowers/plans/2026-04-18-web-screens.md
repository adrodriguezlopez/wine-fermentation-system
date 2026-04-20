# Web Screens Implementation Plan (Phase 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all 19 admin web screens for `apps/web`.

**Prerequisite:** `2026-04-18-frontend-foundation.md` must be complete.

**Architecture:** All pages are `'use client'`. TanStack Query v5 handles data (use `{ queryKey, queryFn }` syntax). Components in `src/components/`. API via `apiClient` singleton.

**Tech Stack:** Next.js 14 App Router, TanStack Query v5, Shadcn/ui, Recharts, Framer Motion, React Hook Form + Zod, Lucide React, Vitest + RTL + MSW

**Skills:** `wine-frontend-context`, `nextjs-app-router`, `tanstack-query-v5`, `shadcn-ui`, `frontend-design`

---

## File Structure

```
apps/web/src/
├── app/(dashboard)/
│   ├── dashboard/page.tsx
│   ├── fermentations/page.tsx, new/page.tsx, [id]/page.tsx
│   │   └── [id]/analyses/page.tsx, [aid]/page.tsx, [aid]/recommendations/[rid]/page.tsx
│   ├── protocols/page.tsx, new/page.tsx, [id]/page.tsx
│   ├── fruit-origin/page.tsx, vineyards/new/page.tsx, vineyards/[id]/page.tsx
│   │   └── vineyards/[id]/lots/new/page.tsx
│   └── admin/wineries/page.tsx, new/page.tsx, [id]/page.tsx
├── components/
│   ├── charts/DensityLineChart.tsx, StatCard.tsx
│   ├── fermentation/FermentationTable.tsx, CreateFermentationForm.tsx,
│   │   FermentationDetailTabs.tsx, OverviewTab.tsx, ReadingsCard.tsx,
│   │   AddSampleDrawer.tsx, SampleForm.tsx, ProtocolTab.tsx,
│   │   AlertsTab.tsx, AlertRow.tsx, ActionsTab.tsx, HistoryTab.tsx
│   ├── analysis/AnalysisListTable.tsx, AnalysisReport.tsx, RecommendationDetail.tsx
│   ├── protocols/ProtocolTable.tsx, ProtocolForm.tsx
│   ├── fruit-origin/VineyardTable.tsx, VineyardForm.tsx, HarvestLotForm.tsx
│   └── admin/WineryForm.tsx
└── __tests__/msw/handlers.ts, msw/server.ts, alert-row.test.tsx, ...
```

---

## Task 1: MSW test infrastructure

**Files:**
- Create: `apps/web/__tests__/msw/handlers.ts`
- Create: `apps/web/__tests__/msw/server.ts`
- Modify: `apps/web/__tests__/setup.ts`

- [ ] **Step 1: Create MSW handlers**

```typescript
// apps/web/__tests__/msw/handlers.ts
import { http, HttpResponse } from 'msw'

const fermentation = {
  id: 'f-1', winery_id: 'w-1', vintage_year: 2024,
  yeast_strain: 'EC-1118', vessel_code: 'V-01',
  input_mass_kg: 5000, initial_sugar_brix: 22,
  initial_density: 1.090, start_date: '2024-04-01T00:00:00Z',
  status: 'ACTIVE', notes: null,
  created_at: '2024-04-01T00:00:00Z', updated_at: '2024-04-01T00:00:00Z',
}

export const handlers = [
  http.get('/api/fermentation/fermentations', () =>
    HttpResponse.json({ items: [fermentation], total: 1, page: 1, size: 20, pages: 1 })
  ),
  http.get('/api/fermentation/fermentations/f-1', () =>
    HttpResponse.json(fermentation)
  ),
  http.post('/api/fermentation/fermentations', () =>
    HttpResponse.json(fermentation, { status: 201 })
  ),
  http.get('/api/fermentation/fermentations/f-1/samples', () =>
    HttpResponse.json([])
  ),
  http.get('/api/fermentation/fermentations/f-1/samples/latest', () =>
    HttpResponse.json(null, { status: 404 })
  ),
  http.get('/api/analysis/analyses/fermentation/f-1', () =>
    HttpResponse.json([])
  ),
  http.get('/api/fermentation/protocols', () => HttpResponse.json([])),
  http.get('/api/fruit-origin/vineyards/', () => HttpResponse.json([])),
  http.get('/api/winery/admin/wineries', () => HttpResponse.json([])),
  http.post('/api/fermentation/alerts/:id/acknowledge', ({ params }) =>
    HttpResponse.json({ id: params.id, status: 'ACKNOWLEDGED' })
  ),
  http.post('/api/fermentation/alerts/:id/dismiss', ({ params }) =>
    HttpResponse.json({ id: params.id, status: 'DISMISSED' })
  ),
]
```

- [ ] **Step 2: Create MSW server**

```typescript
// apps/web/__tests__/msw/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'
export const server = setupServer(...handlers)
```

- [ ] **Step 3: Update setup.ts**

```typescript
// apps/web/__tests__/setup.ts
import '@testing-library/jest-dom'
import { beforeAll, afterEach, afterAll } from 'vitest'
import { server } from './msw/server'

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

- [ ] **Step 4: Install MSW**

```bash
cd frontend/apps/web && pnpm add -D msw
npx msw init public/ --save
```

- [ ] **Step 5: Run tests — expect existing tests still pass**

```bash
cd frontend/apps/web && pnpm test
```

- [ ] **Step 6: Commit**

```bash
git add frontend/apps/web/__tests__/ frontend/apps/web/public/mockServiceWorker.js
git commit -m "test: add MSW server for web app tests"
```

---

## Task 2: StatCard + DensityLineChart

**Files:**
- Create: `apps/web/src/components/charts/StatCard.tsx`
- Create: `apps/web/src/components/charts/DensityLineChart.tsx`
- Create: `apps/web/__tests__/stat-card.test.tsx`

- [ ] **Step 1: Write failing test**

```tsx
// apps/web/__tests__/stat-card.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatCard } from '../src/components/charts/StatCard'

describe('StatCard', () => {
  it('renders label and value', () => {
    render(<StatCard label="Density" value="1.0823" unit="g/cm³" />)
    expect(screen.getByText('Density')).toBeInTheDocument()
    expect(screen.getByText('1.0823')).toBeInTheDocument()
  })

  it('renders trend label when provided', () => {
    render(<StatCard label="Days" value="14" trend="up" trendLabel="vs avg" />)
    expect(screen.getByText('vs avg')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run to see FAIL**

```bash
cd frontend/apps/web && pnpm test stat-card
```

Expected: FAIL — `Cannot find module '../src/components/charts/StatCard'`

- [ ] **Step 3: Create StatCard.tsx**

```tsx
// apps/web/src/components/charts/StatCard.tsx
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatCardProps {
  label: string
  value: string | number
  unit?: string
  trend?: 'up' | 'down' | 'neutral'
  trendLabel?: string
}

export function StatCard({ label, value, unit, trend, trendLabel }: StatCardProps) {
  return (
    <div className="bg-surface border border-border rounded-md p-4">
      <p className="text-xs font-sans text-muted uppercase tracking-wide mb-1">{label}</p>
      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-mono text-text-primary">{value}</span>
        {unit && <span className="text-sm font-sans text-muted">{unit}</span>}
      </div>
      {trend && trendLabel && (
        <div className={cn(
          'flex items-center gap-1 mt-1 text-xs font-sans',
          trend === 'up' && 'text-success',
          trend === 'down' && 'text-danger',
          trend === 'neutral' && 'text-muted',
        )}>
          {trend === 'up' && <TrendingUp size={12} />}
          {trend === 'down' && <TrendingDown size={12} />}
          {trend === 'neutral' && <Minus size={12} />}
          {trendLabel}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Create DensityLineChart.tsx**

```tsx
// apps/web/src/components/charts/DensityLineChart.tsx
'use client'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, type TooltipProps,
} from 'recharts'
import { formatDensityShort, formatDensity, formatDateTime, formatDate } from '@wine/ui'
import type { SampleDto } from '@wine/shared'

function CustomTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  const s = payload[0].payload as SampleDto
  return (
    <div className="bg-surface border border-border rounded p-2 text-xs shadow-sm">
      <p className="font-mono font-medium">{formatDensity(s.value)}</p>
      <p className="text-muted">{formatDateTime(s.recorded_at)}</p>
    </div>
  )
}

export function DensityLineChart({ samples, isLoading }: { samples: SampleDto[]; isLoading?: boolean }) {
  if (isLoading) return <div className="h-[280px] bg-secondary animate-pulse rounded" />
  const densitySamples = samples.filter(s => s.sample_type === 'DENSITY')
  if (!densitySamples.length) {
    return (
      <div className="h-[280px] flex items-center justify-center text-muted text-sm">
        No density samples recorded yet
      </div>
    )
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={densitySamples} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} stroke="#E5E7EB" strokeDasharray="4 4" />
        <XAxis dataKey="recorded_at" tickFormatter={formatDate} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={formatDensityShort} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={50} />
        <Tooltip content={<CustomTooltip />} />
        <Line type="monotone" dataKey="value" stroke="#8B1A2E" strokeWidth={2}
          dot={{ r: 4, fill: '#8B1A2E', stroke: '#FFFFFF', strokeWidth: 2 }} activeDot={{ r: 6 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
```

- [ ] **Step 5: Run — expect PASS**

```bash
cd frontend/apps/web && pnpm test stat-card
```

- [ ] **Step 6: Commit**

```bash
git add frontend/apps/web/src/components/charts/
git commit -m "feat: StatCard and DensityLineChart components"
```

---

## Task 3: Dashboard page

**Files:**
- Modify: `apps/web/src/app/(dashboard)/dashboard/page.tsx`
- Create: `apps/web/__tests__/dashboard.test.tsx`

- [ ] **Step 1: Write failing test**

```tsx
// apps/web/__tests__/dashboard.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardPage from '../src/app/(dashboard)/dashboard/page'

vi.mock('../src/lib/api-client', () => ({ apiClient: {} }))
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }), usePathname: () => '/dashboard' }))
vi.mock('../src/stores/auth.store', () => ({
  useAuthStore: vi.fn((s: (state: { user: unknown }) => unknown) => s({ user: { id: 1, email: 'a@b.com', role: 'ADMIN', winery_id: 'w-1' } })),
}))

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{children}</QueryClientProvider>
)

describe('DashboardPage', () => {
  it('renders Dashboard heading', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
  })
  it('shows Recent Fermentations section', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByText(/recent fermentations/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run — expect FAIL** (heading exists but no Recent Fermentations section yet)

```bash
cd frontend/apps/web && pnpm test dashboard
```

- [ ] **Step 3: Implement dashboard page**

```tsx
// apps/web/src/app/(dashboard)/dashboard/page.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { createFermentationApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { FERMENTATION_STATUS_LABEL, FERMENTATION_STATUS_COLOR } from '@wine/ui'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { StatCard } from '@/components/charts/StatCard'
import { Plus } from 'lucide-react'
import type { FermentationDto } from '@wine/shared'

const fermentationApi = createFermentationApi(apiClient)

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['fermentations'],
    queryFn: () => fermentationApi.list({ size: 10 }),
    refetchInterval: 30_000,
  })
  const fermentations = data?.items ?? []
  const active = fermentations.filter(f => f.status === 'ACTIVE').length
  const slow = fermentations.filter(f => f.status === 'SLOW').length
  const stuck = fermentations.filter(f => f.status === 'STUCK').length

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-display font-semibold text-text-primary">Dashboard</h1>
        <Button asChild size="sm">
          <Link href="/fermentations/new"><Plus size={14} className="mr-1" />New Fermentation</Link>
        </Button>
      </div>
      <motion.div className="grid grid-cols-3 gap-4 mb-8"
        initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <StatCard label="Active" value={active} />
        <StatCard label="Slow" value={slow} trend={slow > 0 ? 'down' : 'neutral'} />
        <StatCard label="Stuck" value={stuck} trend={stuck > 0 ? 'down' : 'neutral'}
          trendLabel={stuck > 0 ? 'needs attention' : undefined} />
      </motion.div>
      <Card>
        <CardHeader><CardTitle className="text-base font-sans">Recent Fermentations</CardTitle></CardHeader>
        <CardContent>
          {isLoading && <p className="text-sm text-muted">Loading…</p>}
          {!isLoading && !fermentations.length && (
            <p className="text-sm text-muted">No fermentations yet. <Link href="/fermentations/new" className="text-accent underline">Create one</Link>.</p>
          )}
          {fermentations.map((f: FermentationDto) => (
            <Link key={f.id} href={`/fermentations/${f.id}`}
              className="flex items-center justify-between py-3 border-b border-border last:border-0 hover:bg-secondary px-2 -mx-2 rounded transition-colors">
              <span className="font-sans text-sm font-medium">{f.vessel_code}</span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-muted">{f.vintage_year}</span>
                <Badge variant="outline" style={{ color: FERMENTATION_STATUS_COLOR[f.status], borderColor: FERMENTATION_STATUS_COLOR[f.status] }}>
                  {FERMENTATION_STATUS_LABEL[f.status]}
                </Badge>
              </div>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
```

- [ ] **Step 4: Run — expect PASS**

```bash
cd frontend/apps/web && pnpm test dashboard
```

- [ ] **Step 5: Commit**

```bash
git add frontend/apps/web/src/app/(dashboard)/dashboard/
git commit -m "feat: dashboard with KPI cards and recent fermentations list"
```

---

## Task 4: Fermentation list + create pages

**Files:**
- Create: `apps/web/src/components/fermentation/FermentationTable.tsx`
- Create: `apps/web/src/components/fermentation/CreateFermentationForm.tsx`
- Create: `apps/web/src/app/(dashboard)/fermentations/page.tsx`
- Create: `apps/web/src/app/(dashboard)/fermentations/new/page.tsx`
- Create: `apps/web/__tests__/fermentation-list.test.tsx`

- [ ] **Step 1: Write failing test**

```tsx
// apps/web/__tests__/fermentation-list.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import FermentationsPage from '../src/app/(dashboard)/fermentations/page'

vi.mock('../src/lib/api-client', () => ({ apiClient: {} }))
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }), usePathname: () => '/fermentations' }))
vi.mock('../src/stores/auth.store', () => ({
  useAuthStore: vi.fn((s: (state: { user: unknown }) => unknown) => s({ user: { id: 1, email: 'a@b.com', role: 'ADMIN', winery_id: 'w-1' } })),
}))

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{children}</QueryClientProvider>
)

describe('FermentationsPage', () => {
  it('renders heading', () => {
    render(<FermentationsPage />, { wrapper })
    expect(screen.getByRole('heading', { name: /fermentations/i })).toBeInTheDocument()
  })
  it('renders New Fermentation link', () => {
    render(<FermentationsPage />, { wrapper })
    expect(screen.getByRole('link', { name: /new fermentation/i })).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd frontend/apps/web && pnpm test fermentation-list
```

- [ ] **Step 3: Create FermentationTable.tsx**

```tsx
// apps/web/src/components/fermentation/FermentationTable.tsx
'use client'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { FERMENTATION_STATUS_LABEL, FERMENTATION_STATUS_COLOR } from '@wine/ui'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { FermentationDto } from '@wine/shared'

export function FermentationTable({ fermentations, isLoading }: { fermentations: FermentationDto[]; isLoading: boolean }) {
  if (isLoading) return <div className="h-48 bg-secondary animate-pulse rounded" />
  if (!fermentations.length) return <p className="text-sm text-muted py-8 text-center">No fermentations found.</p>
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Vessel</TableHead>
          <TableHead>Vintage</TableHead>
          <TableHead>Yeast</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Started</TableHead>
          <TableHead />
        </TableRow>
      </TableHeader>
      <TableBody>
        {fermentations.map((f, i) => (
          <motion.tr key={f.id}
            initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            className="border-b border-border hover:bg-secondary/50 transition-colors">
            <TableCell className="font-medium">{f.vessel_code}</TableCell>
            <TableCell className="font-mono text-sm">{f.vintage_year}</TableCell>
            <TableCell className="text-sm text-muted">{f.yeast_strain}</TableCell>
            <TableCell>
              <Badge variant="outline" style={{ color: FERMENTATION_STATUS_COLOR[f.status], borderColor: FERMENTATION_STATUS_COLOR[f.status] }}>
                {FERMENTATION_STATUS_LABEL[f.status]}
              </Badge>
            </TableCell>
            <TableCell className="text-sm text-muted font-mono">{new Date(f.start_date).toLocaleDateString()}</TableCell>
            <TableCell><Button asChild variant="ghost" size="sm"><Link href={`/fermentations/${f.id}`}>View</Link></Button></TableCell>
          </motion.tr>
        ))}
      </TableBody>
    </Table>
  )
}
```

- [ ] **Step 4: Create fermentations/page.tsx**

```tsx
// apps/web/src/app/(dashboard)/fermentations/page.tsx
'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { createFermentationApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { FermentationTable } from '@/components/fermentation/FermentationTable'
import { Plus } from 'lucide-react'

const fermentationApi = createFermentationApi(apiClient)
const STATUSES = ['ALL', 'ACTIVE', 'SLOW', 'STUCK', 'COMPLETED'] as const

export default function FermentationsPage() {
  const [status, setStatus] = useState<string>('ALL')
  const [search, setSearch] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: ['fermentations', status],
    queryFn: () => fermentationApi.list({ status: status === 'ALL' ? undefined : status, size: 50 }),
    refetchInterval: 30_000,
  })
  const fermentations = (data?.items ?? []).filter(f =>
    !search || f.vessel_code.toLowerCase().includes(search.toLowerCase()) || String(f.vintage_year).includes(search)
  )
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-display font-semibold text-text-primary">Fermentations</h1>
        <Button asChild size="sm"><Link href="/fermentations/new"><Plus size={14} className="mr-1" />New Fermentation</Link></Button>
      </div>
      <div className="flex gap-2 mb-4 flex-wrap">
        {STATUSES.map(s => (
          <Badge key={s} variant={status === s ? 'default' : 'outline'} className="cursor-pointer" onClick={() => setStatus(s)}>
            {s === 'ALL' ? 'All' : s.charAt(0) + s.slice(1).toLowerCase()}
          </Badge>
        ))}
        <Input placeholder="Search…" value={search} onChange={e => setSearch(e.target.value)} className="ml-auto w-48 h-7 text-sm" />
      </div>
      <FermentationTable fermentations={fermentations} isLoading={isLoading} />
    </div>
  )
}
```

- [ ] **Step 5: Create CreateFermentationForm.tsx**

```tsx
// apps/web/src/components/fermentation/CreateFermentationForm.tsx
'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { CreateFermentationSchema, type CreateFermentationData } from '@wine/ui'
import { createFermentationApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const fermentationApi = createFermentationApi(apiClient)

export function CreateFermentationForm() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const form = useForm<CreateFermentationData>({
    resolver: zodResolver(CreateFermentationSchema),
    defaultValues: { start_date: new Date().toISOString() },
  })
  const mutation = useMutation({
    mutationFn: (data: CreateFermentationData) => fermentationApi.create(data),
    onSuccess: (f) => { queryClient.invalidateQueries({ queryKey: ['fermentations'] }); router.push(`/fermentations/${f.id}`) },
  })
  return (
    <Card className="max-w-2xl">
      <CardHeader><CardTitle className="font-display text-xl">New Fermentation</CardTitle></CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(d => mutation.mutate(d))} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField control={form.control} name="vessel_code" render={({ field }) => (
                <FormItem><FormLabel>Vessel Code</FormLabel><FormControl><Input placeholder="V-01" {...field} /></FormControl><FormMessage /></FormItem>
              )} />
              <FormField control={form.control} name="vintage_year" render={({ field }) => (
                <FormItem><FormLabel>Vintage Year</FormLabel><FormControl><Input type="number" {...field} onChange={e => field.onChange(Number(e.target.value))} /></FormControl><FormMessage /></FormItem>
              )} />
            </div>
            <FormField control={form.control} name="yeast_strain" render={({ field }) => (
              <FormItem><FormLabel>Yeast Strain</FormLabel><FormControl><Input placeholder="EC-1118" {...field} /></FormControl><FormMessage /></FormItem>
            )} />
            <div className="grid grid-cols-2 gap-4">
              <FormField control={form.control} name="input_mass_kg" render={({ field }) => (
                <FormItem><FormLabel>Input Mass (kg)</FormLabel><FormControl><Input type="number" {...field} onChange={e => field.onChange(Number(e.target.value))} /></FormControl><FormMessage /></FormItem>
              )} />
              <FormField control={form.control} name="initial_sugar_brix" render={({ field }) => (
                <FormItem><FormLabel>Initial Brix</FormLabel><FormControl><Input type="number" step="0.1" {...field} onChange={e => field.onChange(Number(e.target.value))} /></FormControl><FormMessage /></FormItem>
              )} />
            </div>
            {mutation.isError && <p className="text-sm text-danger">Failed to create fermentation.</p>}
            <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Creating…' : 'Create Fermentation'}</Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 6: Create fermentations/new/page.tsx**

```tsx
// apps/web/src/app/(dashboard)/fermentations/new/page.tsx
'use client'
import { CreateFermentationForm } from '@/components/fermentation/CreateFermentationForm'
export default function NewFermentationPage() {
  return <div><h1 className="text-2xl font-display font-semibold mb-6">New Fermentation</h1><CreateFermentationForm /></div>
}
```

- [ ] **Step 7: Run — expect PASS**

```bash
cd frontend/apps/web && pnpm test fermentation-list
```

- [ ] **Step 8: Commit**

```bash
git add frontend/apps/web/src/components/fermentation/FermentationTable.tsx frontend/apps/web/src/components/fermentation/CreateFermentationForm.tsx frontend/apps/web/src/app/(dashboard)/fermentations/
git commit -m "feat: fermentation list with filter/search and create form"
```

---

## Task 5: Fermentation detail — 5-tab layout + AlertRow

**Files:**
- Create: `apps/web/src/components/fermentation/ReadingsCard.tsx`
- Create: `apps/web/src/components/fermentation/SampleForm.tsx`
- Create: `apps/web/src/components/fermentation/AddSampleDrawer.tsx`
- Create: `apps/web/src/components/fermentation/OverviewTab.tsx`
- Create: `apps/web/src/components/fermentation/AlertRow.tsx`
- Create: `apps/web/src/components/fermentation/AlertsTab.tsx`
- Create: `apps/web/src/components/fermentation/ActionsTab.tsx`
- Create: `apps/web/src/components/fermentation/HistoryTab.tsx`
- Create: `apps/web/src/components/fermentation/ProtocolTab.tsx`
- Create: `apps/web/src/components/fermentation/FermentationDetailTabs.tsx`
- Create: `apps/web/src/app/(dashboard)/fermentations/[id]/page.tsx`
- Create: `apps/web/__tests__/fermentation-detail.test.tsx`
- Create: `apps/web/__tests__/alert-row.test.tsx`

- [ ] **Step 1: Write failing tests**

```tsx
// apps/web/__tests__/fermentation-detail.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import FermentationDetailPage from '../src/app/(dashboard)/fermentations/[id]/page'

vi.mock('../src/lib/api-client', () => ({ apiClient: {} }))
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }), useParams: () => ({ id: 'f-1' }) }))

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{children}</QueryClientProvider>
)

describe('FermentationDetailPage', () => {
  it('renders all 5 tabs', () => {
    render(<FermentationDetailPage params={{ id: 'f-1' }} />, { wrapper })
    expect(screen.getByRole('tab', { name: /overview/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /protocol/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /alerts/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /actions/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /history/i })).toBeInTheDocument()
  })
})
```

```tsx
// apps/web/__tests__/alert-row.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AlertRow } from '../src/components/fermentation/AlertRow'

vi.mock('../src/lib/api-client', () => ({ apiClient: {} }))

const pendingAlert = {
  id: 'a-1', execution_id: 'e-1', alert_type: 'TEMPERATURE_WARNING' as const,
  status: 'PENDING' as const, message: 'Temperature too low',
  created_at: new Date().toISOString(), acknowledged_at: null, dismissed_at: null,
}
const ackedAlert = { ...pendingAlert, status: 'ACKNOWLEDGED' as const }

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient()}>{children}</QueryClientProvider>
)

describe('AlertRow — CRITICAL: both buttons always visible', () => {
  it('pending alert shows Acknowledge button', () => {
    render(<AlertRow alert={pendingAlert} executionId="e-1" />, { wrapper })
    expect(screen.getByRole('button', { name: /acknowledge/i })).toBeInTheDocument()
  })
  it('pending alert shows Dismiss button', () => {
    render(<AlertRow alert={pendingAlert} executionId="e-1" />, { wrapper })
    expect(screen.getByRole('button', { name: /dismiss/i })).toBeInTheDocument()
  })
  it('both buttons visible simultaneously — never collapsed', () => {
    render(<AlertRow alert={pendingAlert} executionId="e-1" />, { wrapper })
    expect(screen.getByRole('button', { name: /acknowledge/i })).toBeVisible()
    expect(screen.getByRole('button', { name: /dismiss/i })).toBeVisible()
  })
  it('acknowledged alert STILL shows Dismiss button', () => {
    render(<AlertRow alert={ackedAlert} executionId="e-1" />, { wrapper })
    expect(screen.getByRole('button', { name: /dismiss/i })).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd frontend/apps/web && pnpm test fermentation-detail alert-row
```

- [ ] **Step 3: Create ReadingsCard.tsx**

```tsx
// apps/web/src/components/fermentation/ReadingsCard.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import { createSampleApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { formatDensity, formatCelsius, formatBrix, formatRelative } from '@wine/ui'
import { Card, CardContent } from '@/components/ui/card'

const sampleApi = createSampleApi(apiClient)

export function ReadingsCard({ fermentationId, status }: { fermentationId: string; status: string }) {
  const { data: latest } = useQuery({
    queryKey: ['samples', fermentationId, 'latest'],
    queryFn: () => sampleApi.getLatest(fermentationId),
    refetchInterval: status !== 'COMPLETED' ? 30_000 : false,
  })
  if (!latest) return (
    <Card><CardContent className="py-6 text-sm text-muted text-center">No samples yet</CardContent></Card>
  )
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex justify-between mb-1">
          <span className="text-xs text-muted uppercase tracking-wide">Latest Reading</span>
          <span className="text-xs text-muted">{formatRelative(latest.recorded_at)}</span>
        </div>
        <p className="text-4xl font-mono text-text-primary">
          {latest.sample_type === 'DENSITY' && formatDensity(latest.value)}
          {latest.sample_type === 'TEMPERATURE' && formatCelsius(latest.value)}
          {latest.sample_type === 'BRIX' && formatBrix(latest.value)}
        </p>
        <p className="text-xs text-muted mt-1">{latest.sample_type.toLowerCase()}</p>
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 4: Create SampleForm.tsx and AddSampleDrawer.tsx**

```tsx
// apps/web/src/components/fermentation/SampleForm.tsx
'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { SampleSchema, type SampleFormData, SAMPLE_TYPE_LABEL } from '@wine/ui'
import { createSampleApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'

const sampleApi = createSampleApi(apiClient)

export function SampleForm({ fermentationId, onSuccess }: { fermentationId: string; onSuccess: () => void }) {
  const queryClient = useQueryClient()
  const form = useForm<SampleFormData>({ resolver: zodResolver(SampleSchema), defaultValues: { recorded_at: new Date().toISOString() } })
  const mutation = useMutation({
    mutationFn: (data: SampleFormData) => sampleApi.create(fermentationId, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['samples', fermentationId] }); onSuccess() },
  })
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(d => mutation.mutate(d))} className="space-y-4">
        <FormField control={form.control} name="sample_type" render={({ field }) => (
          <FormItem><FormLabel>Sample Type</FormLabel>
            <Select onValueChange={field.onChange} defaultValue={field.value}>
              <FormControl><SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger></FormControl>
              <SelectContent>{Object.entries(SAMPLE_TYPE_LABEL).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}</SelectContent>
            </Select><FormMessage />
          </FormItem>
        )} />
        <FormField control={form.control} name="value" render={({ field }) => (
          <FormItem><FormLabel>Value</FormLabel>
            <FormControl><Input type="number" step="0.0001" className="font-mono" {...field} onChange={e => field.onChange(Number(e.target.value))} /></FormControl>
            <FormMessage />
          </FormItem>
        )} />
        {mutation.isError && <p className="text-sm text-danger">Failed to save sample.</p>}
        <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Saving…' : 'Record Sample'}</Button>
      </form>
    </Form>
  )
}
```

```tsx
// apps/web/src/components/fermentation/AddSampleDrawer.tsx
'use client'
import { useState } from 'react'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { SampleForm } from './SampleForm'
import { Plus } from 'lucide-react'

export function AddSampleDrawer({ fermentationId }: { fermentationId: string }) {
  const [open, setOpen] = useState(false)
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button size="sm" variant="outline"><Plus size={14} className="mr-1" />Add Sample</Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader><SheetTitle className="font-display">Record Sample</SheetTitle></SheetHeader>
        <div className="mt-6"><SampleForm fermentationId={fermentationId} onSuccess={() => setOpen(false)} /></div>
      </SheetContent>
    </Sheet>
  )
}
```

- [ ] **Step 5: Create OverviewTab.tsx**

```tsx
// apps/web/src/components/fermentation/OverviewTab.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import { createSampleApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { DensityLineChart } from '@/components/charts/DensityLineChart'
import { StatCard } from '@/components/charts/StatCard'
import { ReadingsCard } from './ReadingsCard'
import { AddSampleDrawer } from './AddSampleDrawer'
import type { FermentationDto } from '@wine/shared'

const sampleApi = createSampleApi(apiClient)

export function OverviewTab({ fermentation }: { fermentation: FermentationDto }) {
  const { data: samples = [], isLoading } = useQuery({
    queryKey: ['samples', fermentation.id],
    queryFn: () => sampleApi.list(fermentation.id),
  })
  const daysRunning = Math.floor((Date.now() - new Date(fermentation.start_date).getTime()) / 86_400_000)
  return (
    <div className="space-y-6">
      <div className="flex justify-end"><AddSampleDrawer fermentationId={fermentation.id} /></div>
      <div className="grid grid-cols-3 gap-4">
        <ReadingsCard fermentationId={fermentation.id} status={fermentation.status} />
        <StatCard label="Days Fermenting" value={daysRunning} unit="days" />
        <StatCard label="Input Mass" value={fermentation.input_mass_kg.toLocaleString()} unit="kg" />
      </div>
      <div>
        <p className="text-sm font-medium mb-3">Density Trend</p>
        <DensityLineChart samples={samples} isLoading={isLoading} />
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Create AlertRow.tsx**

```tsx
// apps/web/src/components/fermentation/AlertRow.tsx
'use client'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createAlertApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ALERT_TYPE_LABEL, formatRelative } from '@wine/ui'
import { cn } from '@/lib/utils'
import type { AlertDto } from '@wine/shared'

const alertApi = createAlertApi(apiClient)

export function AlertRow({ alert, executionId }: { alert: AlertDto; executionId: string }) {
  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['alerts', executionId] })
  const acknowledge = useMutation({ mutationFn: () => alertApi.acknowledge(alert.id), onSuccess: invalidate })
  const dismiss = useMutation({ mutationFn: () => alertApi.dismiss(alert.id), onSuccess: invalidate })
  const isAcknowledged = alert.status === 'ACKNOWLEDGED'

  return (
    <div className={cn('flex items-start justify-between py-3 border-b border-border last:border-0', isAcknowledged && 'opacity-60')}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <Badge variant="outline" className="text-xs">{ALERT_TYPE_LABEL[alert.alert_type] ?? alert.alert_type}</Badge>
          <span className="text-xs text-muted">{formatRelative(alert.created_at)}</span>
        </div>
        <p className="text-sm">{alert.message}</p>
      </div>
      {/* CRITICAL: BOTH buttons ALWAYS rendered — acknowledge ≠ dismiss */}
      <div className="flex gap-2 ml-4 shrink-0">
        <Button size="sm" variant="outline"
          disabled={isAcknowledged || acknowledge.isPending}
          onClick={() => acknowledge.mutate()}>
          Acknowledge
        </Button>
        <Button size="sm" variant="destructive"
          disabled={dismiss.isPending}
          onClick={() => dismiss.mutate()}>
          Dismiss
        </Button>
      </div>
    </div>
  )
}
```

- [ ] **Step 7: Create AlertsTab, ActionsTab, HistoryTab, ProtocolTab**

```tsx
// apps/web/src/components/fermentation/AlertsTab.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import { createAlertApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { AlertRow } from './AlertRow'
import type { FermentationDto } from '@wine/shared'

const alertApi = createAlertApi(apiClient)

export function AlertsTab({ fermentation, executionId }: { fermentation: FermentationDto; executionId: string | null }) {
  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ['alerts', executionId],
    queryFn: () => executionId ? alertApi.listForExecution(executionId) : Promise.resolve([]),
    enabled: !!executionId,
    refetchInterval: fermentation.status !== 'COMPLETED' ? 30_000 : false,
  })
  if (!executionId) return <p className="text-sm text-muted py-4">No active protocol execution.</p>
  if (isLoading) return <div className="h-24 bg-secondary animate-pulse rounded" />
  if (!alerts.length) return <p className="text-sm text-muted py-4">No alerts at this time.</p>
  return <div>{alerts.map(a => <AlertRow key={a.id} alert={a} executionId={executionId} />)}</div>
}
```

```tsx
// apps/web/src/components/fermentation/ProtocolTab.tsx
'use client'
import type { FermentationDto } from '@wine/shared'
export function ProtocolTab({ fermentation }: { fermentation: FermentationDto }) {
  return <p className="text-sm text-muted py-4">Protocol execution tracking — implementation in next iteration.</p>
}
```

```tsx
// apps/web/src/components/fermentation/ActionsTab.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import { createActionApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { ACTION_TYPE_LABEL, formatDateTime } from '@wine/ui'
import type { FermentationDto } from '@wine/shared'
const actionApi = createActionApi(apiClient)
export function ActionsTab({ fermentation }: { fermentation: FermentationDto }) {
  const { data: actions = [] } = useQuery({ queryKey: ['actions', fermentation.id], queryFn: () => actionApi.listForFermentation(fermentation.id) })
  if (!actions.length) return <p className="text-sm text-muted py-4">No actions recorded.</p>
  return (
    <div className="space-y-3">
      {actions.map(a => (
        <div key={a.id} className="border-b border-border pb-3">
          <div className="flex gap-2 items-center">
            <span className="text-sm font-medium">{ACTION_TYPE_LABEL[a.action_type] ?? a.action_type}</span>
            <span className="text-xs text-muted font-mono">{formatDateTime(a.taken_at)}</span>
          </div>
          <p className="text-sm text-muted mt-1">{a.description}</p>
        </div>
      ))}
    </div>
  )
}
```

```tsx
// apps/web/src/components/fermentation/HistoryTab.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import { createFermentationApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { formatRelative } from '@wine/ui'
import type { FermentationDto } from '@wine/shared'
const fermentationApi = createFermentationApi(apiClient)
export function HistoryTab({ fermentation }: { fermentation: FermentationDto }) {
  const { data: events = [] } = useQuery({ queryKey: ['timeline', fermentation.id], queryFn: () => fermentationApi.getTimeline(fermentation.id) })
  if (!events.length) return <p className="text-sm text-muted py-4">No timeline events.</p>
  return (
    <div className="space-y-2">
      {(events as Array<{ id: string; description: string; occurred_at: string }>).map(e => (
        <div key={e.id} className="flex gap-3 pb-2 border-b border-border">
          <div className="w-2 h-2 rounded-full bg-accent mt-1.5 shrink-0" />
          <div><p className="text-sm">{e.description}</p><p className="text-xs text-muted font-mono">{formatRelative(e.occurred_at)}</p></div>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 8: Create FermentationDetailTabs.tsx**

```tsx
// apps/web/src/components/fermentation/FermentationDetailTabs.tsx
'use client'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { OverviewTab } from './OverviewTab'
import { ProtocolTab } from './ProtocolTab'
import { AlertsTab } from './AlertsTab'
import { ActionsTab } from './ActionsTab'
import { HistoryTab } from './HistoryTab'
import type { FermentationDto } from '@wine/shared'

export function FermentationDetailTabs({ fermentation, executionId }: { fermentation: FermentationDto; executionId: string | null }) {
  return (
    <Tabs defaultValue="overview">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="protocol">Protocol</TabsTrigger>
        <TabsTrigger value="alerts">Alerts</TabsTrigger>
        <TabsTrigger value="actions">Actions</TabsTrigger>
        <TabsTrigger value="history">History</TabsTrigger>
      </TabsList>
      <TabsContent value="overview" className="mt-6"><OverviewTab fermentation={fermentation} /></TabsContent>
      <TabsContent value="protocol" className="mt-6"><ProtocolTab fermentation={fermentation} /></TabsContent>
      <TabsContent value="alerts" className="mt-6"><AlertsTab fermentation={fermentation} executionId={executionId} /></TabsContent>
      <TabsContent value="actions" className="mt-6"><ActionsTab fermentation={fermentation} /></TabsContent>
      <TabsContent value="history" className="mt-6"><HistoryTab fermentation={fermentation} /></TabsContent>
    </Tabs>
  )
}
```

- [ ] **Step 9: Create fermentations/[id]/page.tsx**

```tsx
// apps/web/src/app/(dashboard)/fermentations/[id]/page.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import { createFermentationApi, createExecutionApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { FERMENTATION_STATUS_LABEL, FERMENTATION_STATUS_COLOR } from '@wine/ui'
import { FermentationDetailTabs } from '@/components/fermentation/FermentationDetailTabs'
import { Badge } from '@/components/ui/badge'

const fermentationApi = createFermentationApi(apiClient)
const executionApi = createExecutionApi(apiClient)

export default function FermentationDetailPage({ params }: { params: { id: string } }) {
  const { data: fermentation, isLoading } = useQuery({
    queryKey: ['fermentation', params.id],
    queryFn: () => fermentationApi.get(params.id),
  })
  const { data: executions = [] } = useQuery({
    queryKey: ['executions'],
    queryFn: () => executionApi.list(),
    enabled: !!fermentation,
  })
  const activeExecution = executions.find(e => e.fermentation_id === params.id && e.status === 'ACTIVE') ?? null

  if (isLoading) return <div className="h-64 bg-secondary animate-pulse rounded" />
  if (!fermentation) return <p className="text-sm text-danger">Fermentation not found.</p>

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-display font-semibold text-text-primary">{fermentation.vessel_code}</h1>
        <Badge variant="outline" style={{ color: FERMENTATION_STATUS_COLOR[fermentation.status], borderColor: FERMENTATION_STATUS_COLOR[fermentation.status] }}>
          {FERMENTATION_STATUS_LABEL[fermentation.status]}
        </Badge>
        <span className="text-sm text-muted">Vintage {fermentation.vintage_year}</span>
      </div>
      <FermentationDetailTabs fermentation={fermentation} executionId={activeExecution?.id ?? null} />
    </div>
  )
}
```

- [ ] **Step 10: Run tests — expect PASS**

```bash
cd frontend/apps/web && pnpm test fermentation-detail alert-row
```

Expected: PASS — all 5 tests pass (1 tabs test + 4 alert button tests)

- [ ] **Step 11: Commit**

```bash
git add frontend/apps/web/src/components/fermentation/ frontend/apps/web/src/app/(dashboard)/fermentations/[id]/ frontend/apps/web/__tests__/fermentation-detail.test.tsx frontend/apps/web/__tests__/alert-row.test.tsx
git commit -m "feat: fermentation detail 5-tab layout; alert rows with both Acknowledge and Dismiss buttons"
```

---

## Task 6: Analysis screens

**Files:**
- Create: `apps/web/src/components/analysis/AnalysisListTable.tsx`
- Create: `apps/web/src/components/analysis/AnalysisReport.tsx`
- Create: `apps/web/src/components/analysis/RecommendationDetail.tsx`
- Create: pages for analyses

- [ ] **Step 1: Create AnalysisListTable.tsx**

```tsx
// apps/web/src/components/analysis/AnalysisListTable.tsx
'use client'
import Link from 'next/link'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createAnalysisApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { formatDateTime } from '@wine/ui'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { AnalysisDto } from '@wine/shared'

const analysisApi = createAnalysisApi(apiClient)

export function AnalysisListTable({ analyses, fermentationId }: { analyses: AnalysisDto[]; fermentationId: string }) {
  const queryClient = useQueryClient()
  const trigger = useMutation({
    mutationFn: () => analysisApi.trigger(fermentationId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['analyses', fermentationId] }),
  })
  return (
    <div>
      <div className="flex justify-end mb-4">
        <Button size="sm" onClick={() => trigger.mutate()} disabled={trigger.isPending}>
          {trigger.isPending ? 'Running…' : 'Run New Analysis'}
        </Button>
      </div>
      {!analyses.length ? <p className="text-sm text-muted">No analyses yet.</p> : (
        <Table>
          <TableHeader><TableRow><TableHead>Date</TableHead><TableHead>Status</TableHead><TableHead>Confidence</TableHead><TableHead /></TableRow></TableHeader>
          <TableBody>
            {analyses.map(a => (
              <TableRow key={a.id}>
                <TableCell className="font-mono text-sm">{formatDateTime(a.created_at)}</TableCell>
                <TableCell><Badge variant={a.status === 'COMPLETED' ? 'default' : 'outline'}>{a.status}</Badge></TableCell>
                <TableCell className="text-sm text-muted">{a.overall_confidence ?? '—'}</TableCell>
                <TableCell><Button asChild variant="ghost" size="sm"><Link href={`/fermentations/${fermentationId}/analyses/${a.id}`}>View</Link></Button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Create AnalysisReport.tsx**

```tsx
// apps/web/src/components/analysis/AnalysisReport.tsx
'use client'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createRecommendationApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { formatDateTime, RECOMMENDATION_CATEGORY_LABEL, RECOMMENDATION_CATEGORY_COLOR } from '@wine/ui'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import type { AnalysisDto, RecommendationDto, AnomalyDto } from '@wine/shared'

const recommendationApi = createRecommendationApi(apiClient)
const SEVERITY_COLOR = { CRITICAL: '#DC2626', WARNING: '#D97706', INFO: '#6B7280' } as const

function AnomalyCard({ a }: { a: AnomalyDto }) {
  return (
    <div className="border-l-2 pl-3 py-1" style={{ borderColor: SEVERITY_COLOR[a.severity as keyof typeof SEVERITY_COLOR] ?? '#6B7280' }}>
      <div className="flex gap-2 items-center">
        <Badge variant="outline" style={{ color: SEVERITY_COLOR[a.severity as keyof typeof SEVERITY_COLOR] }}>{a.severity}</Badge>
        <span className="text-sm font-medium">{a.anomaly_type.replace(/_/g, ' ')}</span>
      </div>
      <p className="text-sm text-muted mt-1">{a.description}</p>
    </div>
  )
}

function RecCard({ rec, analysisId }: { rec: RecommendationDto; analysisId: string }) {
  const qc = useQueryClient()
  const apply = useMutation({ mutationFn: () => recommendationApi.apply(rec.id), onSuccess: () => qc.invalidateQueries({ queryKey: ['analysis', analysisId] }) })
  const catLabel = RECOMMENDATION_CATEGORY_LABEL[rec.category as keyof typeof RECOMMENDATION_CATEGORY_LABEL]
  const catColor = RECOMMENDATION_CATEGORY_COLOR[rec.category as keyof typeof RECOMMENDATION_CATEGORY_COLOR]
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex gap-4 items-start">
          <div className="flex-1">
            <Badge variant="outline" style={{ color: catColor }}>{catLabel ?? rec.category}</Badge>
            <p className="text-sm font-medium mt-1">{rec.title}</p>
            <p className="text-sm text-muted">{rec.description}</p>
            {rec.applied && <p className="text-xs text-success mt-1">Applied {formatDateTime(rec.applied_at!)}</p>}
          </div>
          {!rec.applied && <Button size="sm" onClick={() => apply.mutate()} disabled={apply.isPending}>{apply.isPending ? 'Applying…' : 'Apply'}</Button>}
        </div>
      </CardContent>
    </Card>
  )
}

export function AnalysisReport({ analysis, anomalies, recommendations, fermentationId }: {
  analysis: AnalysisDto; anomalies: AnomalyDto[]; recommendations: RecommendationDto[]; fermentationId: string
}) {
  return (
    <div className="space-y-8">
      <div><p className="text-sm text-muted font-mono">{formatDateTime(analysis.created_at)}</p>
        <Badge variant={analysis.status === 'COMPLETED' ? 'default' : 'outline'} className="mt-1">{analysis.status}</Badge></div>
      {anomalies.length > 0 && (
        <div><h2 className="text-lg font-display font-semibold mb-3">Anomalies</h2>
          <div className="space-y-3">{anomalies.map(a => <AnomalyCard key={a.id} a={a} />)}</div></div>
      )}
      {recommendations.length > 0 && (
        <div><h2 className="text-lg font-display font-semibold mb-3">Recommendations</h2>
          <div className="space-y-3">{recommendations.map(r => <RecCard key={r.id} rec={r} analysisId={analysis.id} />)}</div></div>
      )}
      {!anomalies.length && !recommendations.length && <p className="text-sm text-muted">No anomalies or recommendations.</p>}
    </div>
  )
}
```

- [ ] **Step 3: Create analysis pages**

```tsx
// apps/web/src/app/(dashboard)/fermentations/[id]/analyses/page.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import { createAnalysisApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { AnalysisListTable } from '@/components/analysis/AnalysisListTable'
const analysisApi = createAnalysisApi(apiClient)
export default function AnalysesPage({ params }: { params: { id: string } }) {
  const { data: analyses = [], isLoading } = useQuery({ queryKey: ['analyses', params.id], queryFn: () => analysisApi.listForFermentation(params.id) })
  return (
    <div>
      <h1 className="text-2xl font-display font-semibold mb-6">Analyses</h1>
      {isLoading ? <div className="h-32 bg-secondary animate-pulse rounded" /> : <AnalysisListTable analyses={analyses} fermentationId={params.id} />}
    </div>
  )
}
```

```tsx
// apps/web/src/app/(dashboard)/fermentations/[id]/analyses/[aid]/page.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import { createAnalysisApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { AnalysisReport } from '@/components/analysis/AnalysisReport'
const analysisApi = createAnalysisApi(apiClient)
export default function AnalysisDetailPage({ params }: { params: { id: string; aid: string } }) {
  const { data: analysis, isLoading } = useQuery({ queryKey: ['analysis', params.aid], queryFn: () => analysisApi.get(params.aid) })
  if (isLoading) return <div className="h-64 bg-secondary animate-pulse rounded" />
  if (!analysis) return <p className="text-danger text-sm">Analysis not found.</p>
  return (
    <div>
      <h1 className="text-2xl font-display font-semibold mb-6">Analysis Report</h1>
      <AnalysisReport analysis={analysis} anomalies={[]} recommendations={[]} fermentationId={params.id} />
    </div>
  )
}
```

```tsx
// apps/web/src/app/(dashboard)/fermentations/[id]/analyses/[aid]/recommendations/[rid]/page.tsx
'use client'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { createRecommendationApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { RECOMMENDATION_CATEGORY_LABEL, formatDateTime } from '@wine/ui'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
const recommendationApi = createRecommendationApi(apiClient)
export default function RecommendationDetailPage({ params }: { params: { id: string; aid: string; rid: string } }) {
  const qc = useQueryClient()
  const { data: rec, isLoading } = useQuery({ queryKey: ['recommendation', params.rid], queryFn: () => recommendationApi.get(params.rid) })
  const apply = useMutation({ mutationFn: () => recommendationApi.apply(params.rid), onSuccess: () => qc.invalidateQueries({ queryKey: ['recommendation', params.rid] }) })
  if (isLoading) return <div className="h-40 bg-secondary animate-pulse rounded" />
  if (!rec) return <p className="text-danger text-sm">Recommendation not found.</p>
  return (
    <div>
      <h1 className="text-2xl font-display font-semibold mb-6">Recommendation</h1>
      <Card className="max-w-2xl">
        <CardHeader><CardTitle className="font-sans text-base">{rec.title}</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <Badge variant="outline">{RECOMMENDATION_CATEGORY_LABEL[rec.category as keyof typeof RECOMMENDATION_CATEGORY_LABEL] ?? rec.category}</Badge>
          <p className="text-sm">{rec.description}</p>
          {rec.applied ? <p className="text-sm text-success">Applied {formatDateTime(rec.applied_at!)}</p>
            : <Button onClick={() => apply.mutate()} disabled={apply.isPending}>{apply.isPending ? 'Applying…' : 'Apply Recommendation'}</Button>}
        </CardContent>
      </Card>
    </div>
  )
}
```

- [ ] **Step 4: Run tests and commit**

```bash
cd frontend/apps/web && pnpm test
git add frontend/apps/web/src/components/analysis/ frontend/apps/web/src/app/(dashboard)/fermentations/[id]/analyses/
git commit -m "feat: analysis list, report, and recommendation detail pages"
```

---

## Task 7: Protocols pages

**Files:**
- Create: `apps/web/src/components/protocols/ProtocolTable.tsx`
- Create: `apps/web/src/components/protocols/ProtocolForm.tsx`
- Create: protocol pages

- [ ] **Step 1: Create ProtocolTable.tsx**

```tsx
// apps/web/src/components/protocols/ProtocolTable.tsx
'use client'
import Link from 'next/link'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createProtocolApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { ProtocolDto } from '@wine/shared'
const protocolApi = createProtocolApi(apiClient)
export function ProtocolTable({ protocols }: { protocols: ProtocolDto[] }) {
  const qc = useQueryClient()
  const clone = useMutation({ mutationFn: (id: string) => protocolApi.clone(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['protocols'] }) })
  if (!protocols.length) return <p className="text-sm text-muted py-4">No protocols yet.</p>
  return (
    <Table>
      <TableHeader><TableRow><TableHead>Varietal</TableHead><TableHead>Code</TableHead><TableHead>Version</TableHead><TableHead>Duration</TableHead><TableHead /></TableRow></TableHeader>
      <TableBody>
        {protocols.map(p => (
          <TableRow key={p.id}>
            <TableCell className="font-medium">{p.varietal_name}</TableCell>
            <TableCell className="font-mono text-sm">{p.varietal_code}</TableCell>
            <TableCell className="font-mono text-sm">{p.version}</TableCell>
            <TableCell className="text-sm text-muted">{p.expected_duration_days}d</TableCell>
            <TableCell className="flex gap-2">
              <Button asChild variant="ghost" size="sm"><Link href={`/protocols/${p.id}`}>Edit</Link></Button>
              <Button variant="outline" size="sm" onClick={() => clone.mutate(p.id)} disabled={clone.isPending}>Clone</Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

- [ ] **Step 2: Create ProtocolForm.tsx**

```tsx
// apps/web/src/components/protocols/ProtocolForm.tsx
'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { ProtocolSchema, type ProtocolFormData } from '@wine/ui'
import { createProtocolApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { ProtocolDto } from '@wine/shared'

const protocolApi = createProtocolApi(apiClient)
export function ProtocolForm({ protocol }: { protocol?: ProtocolDto }) {
  const router = useRouter()
  const qc = useQueryClient()
  const form = useForm<ProtocolFormData>({
    resolver: zodResolver(ProtocolSchema),
    defaultValues: protocol ? { varietal_code: protocol.varietal_code, varietal_name: protocol.varietal_name, version: protocol.version, expected_duration_days: protocol.expected_duration_days, description: protocol.description ?? undefined } : undefined,
  })
  const mutation = useMutation({
    mutationFn: (data: ProtocolFormData) => protocol ? protocolApi.update(protocol.id, data) : protocolApi.create(data),
    onSuccess: (p) => { qc.invalidateQueries({ queryKey: ['protocols'] }); router.push(`/protocols/${p.id}`) },
  })
  return (
    <Card className="max-w-2xl">
      <CardHeader><CardTitle className="font-display text-xl">{protocol ? 'Edit Protocol' : 'New Protocol'}</CardTitle></CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(d => mutation.mutate(d))} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField control={form.control} name="varietal_code" render={({ field }) => (<FormItem><FormLabel>Varietal Code</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="varietal_name" render={({ field }) => (<FormItem><FormLabel>Varietal Name</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>)} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField control={form.control} name="version" render={({ field }) => (<FormItem><FormLabel>Version</FormLabel><FormControl><Input placeholder="1.0.0" {...field} /></FormControl><FormMessage /></FormItem>)} />
              <FormField control={form.control} name="expected_duration_days" render={({ field }) => (<FormItem><FormLabel>Duration (days)</FormLabel><FormControl><Input type="number" {...field} onChange={e => field.onChange(Number(e.target.value))} /></FormControl><FormMessage /></FormItem>)} />
            </div>
            <FormField control={form.control} name="description" render={({ field }) => (<FormItem><FormLabel>Description</FormLabel><FormControl><Textarea rows={3} {...field} /></FormControl><FormMessage /></FormItem>)} />
            {mutation.isError && <p className="text-sm text-danger">Failed to save protocol.</p>}
            <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Saving…' : 'Save Protocol'}</Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 3: Create protocol pages**

```tsx
// apps/web/src/app/(dashboard)/protocols/page.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { createProtocolApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { ProtocolTable } from '@/components/protocols/ProtocolTable'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
const protocolApi = createProtocolApi(apiClient)
export default function ProtocolsPage() {
  const { data: protocols = [], isLoading } = useQuery({ queryKey: ['protocols'], queryFn: () => protocolApi.list() })
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-display font-semibold">Protocols</h1>
        <Button asChild size="sm"><Link href="/protocols/new"><Plus size={14} className="mr-1" />New Protocol</Link></Button>
      </div>
      {isLoading ? <div className="h-32 bg-secondary animate-pulse rounded" /> : <ProtocolTable protocols={protocols} />}
    </div>
  )
}
```

```tsx
// apps/web/src/app/(dashboard)/protocols/new/page.tsx
'use client'
import { ProtocolForm } from '@/components/protocols/ProtocolForm'
export default function NewProtocolPage() {
  return <div><h1 className="text-2xl font-display font-semibold mb-6">New Protocol</h1><ProtocolForm /></div>
}
```

```tsx
// apps/web/src/app/(dashboard)/protocols/[id]/page.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import { createProtocolApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { ProtocolForm } from '@/components/protocols/ProtocolForm'
const protocolApi = createProtocolApi(apiClient)
export default function ProtocolDetailPage({ params }: { params: { id: string } }) {
  const { data: protocol, isLoading } = useQuery({ queryKey: ['protocol', params.id], queryFn: () => protocolApi.get(params.id) })
  if (isLoading) return <div className="h-40 bg-secondary animate-pulse rounded" />
  if (!protocol) return <p className="text-danger text-sm">Protocol not found.</p>
  return <div><h1 className="text-2xl font-display font-semibold mb-6">Edit Protocol</h1><ProtocolForm protocol={protocol} /></div>
}
```

- [ ] **Step 4: Run and commit**

```bash
cd frontend/apps/web && pnpm test
git add frontend/apps/web/src/components/protocols/ frontend/apps/web/src/app/(dashboard)/protocols/
git commit -m "feat: protocols list, create, and edit pages"
```

---

## Task 8: Fruit origin + admin winery pages

**Files:**
- Create: `apps/web/src/components/fruit-origin/VineyardTable.tsx`
- Create: `apps/web/src/components/fruit-origin/VineyardForm.tsx`
- Create: `apps/web/src/components/fruit-origin/HarvestLotForm.tsx`
- Create: `apps/web/src/components/admin/WineryForm.tsx`
- Create: fruit-origin and admin pages

- [ ] **Step 1: Create VineyardTable.tsx**

```tsx
// apps/web/src/components/fruit-origin/VineyardTable.tsx
'use client'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { VineyardDto } from '@wine/shared'
export function VineyardTable({ vineyards }: { vineyards: VineyardDto[] }) {
  if (!vineyards.length) return <p className="text-sm text-muted py-4">No vineyards yet.</p>
  return (
    <Table>
      <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Location</TableHead><TableHead>Hectares</TableHead><TableHead /></TableRow></TableHeader>
      <TableBody>
        {vineyards.map(v => (
          <TableRow key={v.id}>
            <TableCell className="font-medium">{v.name}</TableCell>
            <TableCell className="text-sm text-muted">{v.location ?? '—'}</TableCell>
            <TableCell className="font-mono text-sm">{v.hectares ?? '—'}</TableCell>
            <TableCell><Button asChild variant="ghost" size="sm"><Link href={`/fruit-origin/vineyards/${v.id}`}>View</Link></Button></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

- [ ] **Step 2: Create VineyardForm.tsx**

```tsx
// apps/web/src/components/fruit-origin/VineyardForm.tsx
'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { createVineyardApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const vineyardApi = createVineyardApi(apiClient)
const Schema = z.object({ name: z.string().min(1), location: z.string().optional(), hectares: z.number().positive().optional() })
type FormData = z.infer<typeof Schema>
export function VineyardForm() {
  const router = useRouter()
  const qc = useQueryClient()
  const form = useForm<FormData>({ resolver: zodResolver(Schema) })
  const mutation = useMutation({ mutationFn: (d: FormData) => vineyardApi.create(d), onSuccess: (v) => { qc.invalidateQueries({ queryKey: ['vineyards'] }); router.push(`/fruit-origin/vineyards/${v.id}`) } })
  return (
    <Card className="max-w-lg"><CardHeader><CardTitle className="font-display text-xl">New Vineyard</CardTitle></CardHeader><CardContent>
      <Form {...form}><form onSubmit={form.handleSubmit(d => mutation.mutate(d))} className="space-y-4">
        <FormField control={form.control} name="name" render={({ field }) => (<FormItem><FormLabel>Name</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>)} />
        <FormField control={form.control} name="location" render={({ field }) => (<FormItem><FormLabel>Location</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>)} />
        <FormField control={form.control} name="hectares" render={({ field }) => (<FormItem><FormLabel>Hectares</FormLabel><FormControl><Input type="number" step="0.1" {...field} onChange={e => field.onChange(e.target.value ? Number(e.target.value) : undefined)} /></FormControl><FormMessage /></FormItem>)} />
        <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Creating…' : 'Create Vineyard'}</Button>
      </form></Form>
    </CardContent></Card>
  )
}
```

- [ ] **Step 3: Create HarvestLotForm.tsx**

```tsx
// apps/web/src/components/fruit-origin/HarvestLotForm.tsx
'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { createHarvestLotApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const harvestLotApi = createHarvestLotApi(apiClient)
const Schema = z.object({ vintage_year: z.number().int().min(1900), variety_name: z.string().min(1), mass_kg: z.number().positive(), harvest_date: z.string().datetime(), notes: z.string().optional() })
type FormData = z.infer<typeof Schema>
export function HarvestLotForm({ vineyardId }: { vineyardId: string }) {
  const router = useRouter()
  const qc = useQueryClient()
  const form = useForm<FormData>({ resolver: zodResolver(Schema), defaultValues: { harvest_date: new Date().toISOString() } })
  const mutation = useMutation({ mutationFn: (d: FormData) => harvestLotApi.create({ ...d, vineyard_id: vineyardId }), onSuccess: () => { qc.invalidateQueries({ queryKey: ['harvest-lots', vineyardId] }); router.push(`/fruit-origin/vineyards/${vineyardId}`) } })
  return (
    <Card className="max-w-lg"><CardHeader><CardTitle className="font-display text-xl">New Harvest Lot</CardTitle></CardHeader><CardContent>
      <Form {...form}><form onSubmit={form.handleSubmit(d => mutation.mutate(d))} className="space-y-4">
        <FormField control={form.control} name="variety_name" render={({ field }) => (<FormItem><FormLabel>Variety</FormLabel><FormControl><Input placeholder="Cabernet Sauvignon" {...field} /></FormControl><FormMessage /></FormItem>)} />
        <div className="grid grid-cols-2 gap-4">
          <FormField control={form.control} name="vintage_year" render={({ field }) => (<FormItem><FormLabel>Vintage Year</FormLabel><FormControl><Input type="number" {...field} onChange={e => field.onChange(Number(e.target.value))} /></FormControl><FormMessage /></FormItem>)} />
          <FormField control={form.control} name="mass_kg" render={({ field }) => (<FormItem><FormLabel>Mass (kg)</FormLabel><FormControl><Input type="number" {...field} onChange={e => field.onChange(Number(e.target.value))} /></FormControl><FormMessage /></FormItem>)} />
        </div>
        <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Creating…' : 'Create Lot'}</Button>
      </form></Form>
    </CardContent></Card>
  )
}
```

- [ ] **Step 4: Create WineryForm.tsx**

```tsx
// apps/web/src/components/admin/WineryForm.tsx
'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { WinerySchema, type WineryFormData } from '@wine/ui'
import { createWineryApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { WineryDto } from '@wine/shared'

const wineryApi = createWineryApi(apiClient)
export function WineryForm({ winery }: { winery?: WineryDto }) {
  const router = useRouter()
  const qc = useQueryClient()
  const form = useForm<WineryFormData>({ resolver: zodResolver(WinerySchema), defaultValues: winery ? { name: winery.name, code: winery.code, location: winery.location ?? undefined } : undefined })
  const mutation = useMutation({ mutationFn: (d: WineryFormData) => winery ? wineryApi.update(winery.id, d) : wineryApi.create(d), onSuccess: () => { qc.invalidateQueries({ queryKey: ['wineries'] }); router.push('/admin/wineries') } })
  return (
    <Card className="max-w-lg"><CardHeader><CardTitle className="font-display text-xl">{winery ? 'Edit Winery' : 'New Winery'}</CardTitle></CardHeader><CardContent>
      <Form {...form}><form onSubmit={form.handleSubmit(d => mutation.mutate(d))} className="space-y-4">
        <FormField control={form.control} name="name" render={({ field }) => (<FormItem><FormLabel>Name</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>)} />
        <FormField control={form.control} name="code" render={({ field }) => (<FormItem><FormLabel>Code</FormLabel><FormControl><Input placeholder="WINERY01" {...field} /></FormControl><FormMessage /></FormItem>)} />
        <FormField control={form.control} name="location" render={({ field }) => (<FormItem><FormLabel>Location</FormLabel><FormControl><Input {...field} /></FormControl><FormMessage /></FormItem>)} />
        {mutation.isError && <p className="text-sm text-danger">Failed to save.</p>}
        <Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Saving…' : 'Save Winery'}</Button>
      </form></Form>
    </CardContent></Card>
  )
}
```

- [ ] **Step 5: Create fruit-origin and admin pages**

```tsx
// apps/web/src/app/(dashboard)/fruit-origin/page.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { createVineyardApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { VineyardTable } from '@/components/fruit-origin/VineyardTable'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
const vineyardApi = createVineyardApi(apiClient)
export default function FruitOriginPage() {
  const { data: vineyards = [], isLoading } = useQuery({ queryKey: ['vineyards'], queryFn: () => vineyardApi.list() })
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-display font-semibold">Fruit Origin</h1>
        <Button asChild size="sm"><Link href="/fruit-origin/vineyards/new"><Plus size={14} className="mr-1" />New Vineyard</Link></Button>
      </div>
      {isLoading ? <div className="h-32 bg-secondary animate-pulse rounded" /> : <VineyardTable vineyards={vineyards} />}
    </div>
  )
}
```

```tsx
// apps/web/src/app/(dashboard)/fruit-origin/vineyards/new/page.tsx
'use client'
import { VineyardForm } from '@/components/fruit-origin/VineyardForm'
export default function NewVineyardPage() {
  return <div><h1 className="text-2xl font-display font-semibold mb-6">New Vineyard</h1><VineyardForm /></div>
}
```

```tsx
// apps/web/src/app/(dashboard)/fruit-origin/vineyards/[id]/page.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { createVineyardApi, createHarvestLotApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Plus } from 'lucide-react'
const vineyardApi = createVineyardApi(apiClient)
const harvestLotApi = createHarvestLotApi(apiClient)
export default function VineyardDetailPage({ params }: { params: { id: string } }) {
  const { data: vineyard } = useQuery({ queryKey: ['vineyard', params.id], queryFn: () => vineyardApi.get(params.id) })
  const { data: lots = [] } = useQuery({ queryKey: ['harvest-lots', params.id], queryFn: () => harvestLotApi.list(params.id) })
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-display font-semibold">{vineyard?.name ?? 'Vineyard'}</h1>
        <Button asChild size="sm"><Link href={`/fruit-origin/vineyards/${params.id}/lots/new`}><Plus size={14} className="mr-1" />Add Lot</Link></Button>
      </div>
      {!lots.length ? <p className="text-sm text-muted">No harvest lots yet.</p> : (
        <Table>
          <TableHeader><TableRow><TableHead>Variety</TableHead><TableHead>Year</TableHead><TableHead>Mass</TableHead></TableRow></TableHeader>
          <TableBody>{lots.map(l => <TableRow key={l.id}><TableCell>{l.variety_name}</TableCell><TableCell className="font-mono">{l.vintage_year}</TableCell><TableCell className="font-mono">{l.mass_kg.toLocaleString()} kg</TableCell></TableRow>)}</TableBody>
        </Table>
      )}
    </div>
  )
}
```

```tsx
// apps/web/src/app/(dashboard)/fruit-origin/vineyards/[id]/lots/new/page.tsx
'use client'
import { HarvestLotForm } from '@/components/fruit-origin/HarvestLotForm'
export default function NewLotPage({ params }: { params: { id: string } }) {
  return <div><h1 className="text-2xl font-display font-semibold mb-6">New Harvest Lot</h1><HarvestLotForm vineyardId={params.id} /></div>
}
```

```tsx
// apps/web/src/app/(dashboard)/admin/wineries/page.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { createWineryApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth.store'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Plus } from 'lucide-react'
const wineryApi = createWineryApi(apiClient)
export default function WineriesPage() {
  const user = useAuthStore(s => s.user)
  if (user && user.role !== 'ADMIN') return null  // layout guard handles redirect; this is a secondary guard
  const { data: wineries = [], isLoading } = useQuery({ queryKey: ['wineries'], queryFn: () => wineryApi.list() })
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-display font-semibold">Wineries</h1>
        <Button asChild size="sm"><Link href="/admin/wineries/new"><Plus size={14} className="mr-1" />New Winery</Link></Button>
      </div>
      {isLoading ? <div className="h-32 bg-secondary animate-pulse rounded" /> : (
        !wineries.length ? <p className="text-sm text-muted">No wineries.</p> : (
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Code</TableHead><TableHead>Location</TableHead><TableHead /></TableRow></TableHeader>
            <TableBody>{wineries.map(w => (<TableRow key={w.id}><TableCell className="font-medium">{w.name}</TableCell><TableCell className="font-mono text-sm">{w.code}</TableCell><TableCell className="text-sm text-muted">{w.location ?? '—'}</TableCell><TableCell><Button asChild variant="ghost" size="sm"><Link href={`/admin/wineries/${w.id}`}>Edit</Link></Button></TableCell></TableRow>))}</TableBody>
          </Table>
        )
      )}
    </div>
  )
}
```

```tsx
// apps/web/src/app/(dashboard)/admin/wineries/new/page.tsx
'use client'
import { WineryForm } from '@/components/admin/WineryForm'
export default function NewWineryPage() {
  return <div><h1 className="text-2xl font-display font-semibold mb-6">New Winery</h1><WineryForm /></div>
}
```

```tsx
// apps/web/src/app/(dashboard)/admin/wineries/[id]/page.tsx
'use client'
import { useQuery } from '@tanstack/react-query'
import { createWineryApi } from '@wine/shared'
import { apiClient } from '@/lib/api-client'
import { WineryForm } from '@/components/admin/WineryForm'
const wineryApi = createWineryApi(apiClient)
export default function EditWineryPage({ params }: { params: { id: string } }) {
  const { data: winery, isLoading } = useQuery({ queryKey: ['winery', params.id], queryFn: () => wineryApi.get(params.id) })
  if (isLoading) return <div className="h-40 bg-secondary animate-pulse rounded" />
  if (!winery) return <p className="text-danger text-sm">Winery not found.</p>
  return <div><h1 className="text-2xl font-display font-semibold mb-6">Edit Winery</h1><WineryForm winery={winery} /></div>
}
```

- [ ] **Step 6: Run all tests**

```bash
cd frontend/apps/web && pnpm test
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add frontend/apps/web/src/components/fruit-origin/ frontend/apps/web/src/components/admin/ frontend/apps/web/src/app/(dashboard)/fruit-origin/ frontend/apps/web/src/app/(dashboard)/admin/
git commit -m "feat: fruit origin pages (vineyard + harvest lot) and admin winery pages"
```

---

## Task 9: Final verification

- [ ] **Step 1: Full test suite**

```bash
cd frontend && pnpm turbo test
```

Expected: all tests pass across packages/ui, packages/shared, apps/web.

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && pnpm turbo type-check
```

Expected: zero errors.

- [ ] **Step 3: Build**

```bash
cd frontend && pnpm turbo build
```

Expected: `.next/` produced, zero compile errors.

- [ ] **Step 4: Dev server smoke test**

```bash
cd frontend/apps/web && pnpm dev
```

Walk through:
- [ ] `/login` — form renders, empty submit shows validation errors
- [ ] Login → dashboard shows KPI cards + recent fermentations
- [ ] `/fermentations` — list with ALL/ACTIVE/SLOW/STUCK/COMPLETED filter chips
- [ ] `/fermentations/new` — form validates (vessel code, vintage year, yeast, etc.)
- [ ] `/fermentations/{id}` — 5 tabs: Overview, Protocol, Alerts, Actions, History
- [ ] Overview tab: "Add Sample" drawer opens, sample form validates
- [ ] Alerts tab: each alert row shows BOTH Acknowledge AND Dismiss buttons
- [ ] `/fermentations/{id}/analyses` — list + "Run New Analysis" button
- [ ] `/protocols` — list with Clone button per row
- [ ] `/fruit-origin` — vineyard list
- [ ] WINEMAKER navigating to `/admin/wineries` redirects to `/403`
- [ ] 30s polling visible in Network tab on fermentation list and alerts
- [ ] Density values displayed in DM Mono font

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat: Phase 3 complete — all 19 admin web screens implemented and tested"
```

---

## Verification Checklist

- [ ] `pnpm turbo test` — zero failures
- [ ] `pnpm turbo type-check` — zero TypeScript errors
- [ ] `pnpm turbo build` — successful `.next/` build
- [ ] Login → dashboard → fermentation list → fermentation detail navigable
- [ ] 5 tabs render on fermentation detail without errors
- [ ] Alert rows: BOTH Acknowledge AND Dismiss always visible (never collapsed)
- [ ] Analysis: Run New Analysis triggers POST, result page navigable
- [ ] Recommendation: Apply button changes state after success
- [ ] Protocols: Clone duplicates protocol in list
- [ ] WINEMAKER role blocked from `/admin/wineries` → `/403`
- [ ] Polling: 30s refetch on fermentation list and alerts (verify Network tab)
- [ ] All measurement values use DM Mono font
- [ ] Density chart renders for fermentations with DENSITY samples
