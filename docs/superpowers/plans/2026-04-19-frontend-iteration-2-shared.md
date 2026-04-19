# Frontend Foundation — Iteration 2: packages/shared

> **Source plan:** `docs/superpowers/plans/2026-04-18-frontend-foundation.md` (Tasks 6–9)  
> **Governing ADR:** [ADR-045](../../.ai-context/adr/ADR-045-frontend-architecture.md)  
> **Skills to load before starting:**  
> - `wine-frontend-context` → `.github/skills/wine-frontend-context/SKILL.md`  
> - `tanstack-query-v5` → `.github/skills/tanstack-query-v5/SKILL.md`

**Goal:** Deliver a fully working `packages/shared` — TypeScript DTO types, `ApiClient` with 401 auto-refresh, all typed API function factories, and auth/polling hooks. Works in both Next.js and Expo. All tests green.

**Deliverable:** `packages/shared` exports `ApiClient`, `TokenStorage`, all API factories, and hooks. Tests pass. Zero TypeScript errors.

**Prerequisite:** Iteration 1 complete — `@wine/ui` resolves as a workspace dependency.

**Branch:** `feat/frontend-foundation-iteration-2` (branch from main after Iteration 1 is merged)

---

## Pre-flight

- [ ] Read `.github/skills/wine-frontend-context/SKILL.md`
- [ ] Read `.github/skills/tanstack-query-v5/SKILL.md`
- [ ] Confirm Iteration 1 is merged: `git log --oneline -3`
- [ ] Create branch: `git checkout -b feat/frontend-foundation-iteration-2`
- [ ] Confirm `@wine/ui` resolves: `cd frontend && pnpm install`

---

## Task 6: packages/shared — TypeScript DTO types

**Files to create:**
- `frontend/packages/shared/package.json`
- `frontend/packages/shared/tsconfig.json`
- `frontend/packages/shared/vitest.config.ts`
- `frontend/packages/shared/__tests__/types.test.ts`
- `frontend/packages/shared/src/types/auth.ts`
- `frontend/packages/shared/src/types/fermentation.ts`
- `frontend/packages/shared/src/types/sample.ts`
- `frontend/packages/shared/src/types/protocol.ts`
- `frontend/packages/shared/src/types/analysis.ts`
- `frontend/packages/shared/src/types/alert.ts`
- `frontend/packages/shared/src/types/action.ts`
- `frontend/packages/shared/src/types/winery.ts`
- `frontend/packages/shared/src/types/vineyard.ts`
- `frontend/packages/shared/src/types/index.ts`

- [ ] **Step 1: Write failing type tests**

```typescript
// frontend/packages/shared/__tests__/types.test.ts
import { describe, it, expectTypeOf } from 'vitest'
import type { FermentationDto, PaginatedResponse } from '../src/types/fermentation'
import type { UserDto } from '../src/types/auth'

describe('FermentationDto', () => {
  it('has required fields', () => {
    expectTypeOf<FermentationDto>().toHaveProperty('id')
    expectTypeOf<FermentationDto>().toHaveProperty('status')
    expectTypeOf<FermentationDto>().toHaveProperty('winery_id')
  })
})

describe('PaginatedResponse', () => {
  it('is generic', () => {
    type T = PaginatedResponse<FermentationDto>
    expectTypeOf<T>().toHaveProperty('items')
    expectTypeOf<T>().toHaveProperty('total')
  })
})

describe('UserDto', () => {
  it('has role and winery_id', () => {
    expectTypeOf<UserDto>().toHaveProperty('role')
    expectTypeOf<UserDto>().toHaveProperty('winery_id')
  })
})
```

- [ ] **Step 2: Create `package.json`**

```json
{
  "name": "@wine/shared",
  "version": "0.0.1",
  "private": true,
  "main": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./api": "./src/api/index.ts",
    "./hooks": "./src/hooks/index.ts",
    "./storage": "./src/storage/index.ts",
    "./sync": "./src/sync/index.ts",
    "./types": "./src/types/index.ts"
  },
  "scripts": {
    "test": "vitest run",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "@wine/ui": "workspace:*",
    "axios": "^1.7.0",
    "@tanstack/react-query": "^5.40.0",
    "zustand": "^4.5.0",
    "js-cookie": "^3.0.5"
  },
  "devDependencies": {
    "vitest": "^1.6.0",
    "typescript": "^5.4.0",
    "@types/js-cookie": "^3.0.6",
    "react": "^18.3.0",
    "@types/react": "^18.3.0"
  },
  "peerDependencies": {
    "react": "^18.0.0"
  }
}
```

- [ ] **Step 3: Create `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "declaration": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "jsx": "react-jsx"
  },
  "include": ["src/**/*", "__tests__/**/*"]
}
```

- [ ] **Step 4: Create `vitest.config.ts`**

```typescript
// frontend/packages/shared/vitest.config.ts
import { defineConfig } from 'vitest/config'
export default defineConfig({
  test: { environment: 'jsdom', globals: true },
})
```

- [ ] **Step 5: Create `src/types/auth.ts`**

```typescript
export type UserRole = 'ADMIN' | 'WINEMAKER'

export interface UserDto {
  id: number
  email: string
  role: UserRole
  winery_id: string
}

export interface LoginResponseDto {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export interface RefreshResponseDto {
  access_token: string
  token_type: 'bearer'
}
```

- [ ] **Step 6: Create `src/types/fermentation.ts`**

```typescript
import type { FermentationStatus } from '@wine/ui/constants'

export interface FermentationDto {
  id: string
  winery_id: string
  vintage_year: number
  yeast_strain: string
  vessel_code: string
  input_mass_kg: number
  initial_sugar_brix: number
  initial_density: number | null
  start_date: string
  status: FermentationStatus
  notes: string | null
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface FermentationStatisticsDto {
  days_fermenting: number
  current_density: number | null
  temperature_current: number | null
  density_drop_percent: number | null
  estimated_alcohol: number | null
}
```

- [ ] **Step 7: Create remaining type files**

```typescript
// src/types/sample.ts
import type { SampleTypeKey } from '@wine/ui/constants'

export interface SampleDto {
  id: string
  fermentation_id: string
  sample_type: SampleTypeKey
  value: number
  recorded_at: string
  notes: string | null
  created_at: string
}
```

```typescript
// src/types/protocol.ts
export interface ProtocolDto {
  id: string
  winery_id: string
  varietal_code: string
  varietal_name: string
  version: string
  expected_duration_days: number
  description: string | null
  created_at: string
}

export interface ProtocolStepDto {
  id: string
  protocol_id: string
  step_type: string
  sequence: number
  duration_hours: number
  threshold_values: Record<string, number> | null
  notes: string | null
}

export interface ProtocolExecutionDto {
  id: string
  fermentation_id: string
  protocol_id: string
  status: 'ACTIVE' | 'COMPLETED' | 'ABANDONED'
  started_at: string
  completed_at: string | null
}

export interface StepCompletionDto {
  id: string
  execution_id: string
  step_id: string
  completed_by: number
  completion_date: string
  notes: string | null
}
```

```typescript
// src/types/analysis.ts
import type { ConfidenceLevel } from '@wine/ui/constants'

export interface AnalysisDto {
  id: string
  fermentation_id: string
  winery_id: string
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'
  overall_confidence: ConfidenceLevel | null
  created_at: string
  completed_at: string | null
}

export interface AnomalyDto {
  id: string
  analysis_id: string
  anomaly_type: string
  severity: 'CRITICAL' | 'WARNING' | 'INFO'
  description: string
  detected_at: string
}

export interface RecommendationDto {
  id: string
  analysis_id: string
  category: string
  title: string
  description: string
  applied: boolean
  applied_at: string | null
}

export interface AdvisoryDto {
  id: string
  fermentation_id: string
  message: string
  acknowledged: boolean
  created_at: string
}
```

```typescript
// src/types/alert.ts
import type { AlertType, AlertStatus } from '@wine/ui/constants'

export interface AlertDto {
  id: string
  execution_id: string
  alert_type: AlertType
  status: AlertStatus
  message: string
  created_at: string
  acknowledged_at: string | null
  dismissed_at: string | null
}
```

```typescript
// src/types/action.ts
import type { ActionType } from '@wine/ui/constants'

export interface ActionDto {
  id: string
  fermentation_id: string
  execution_id: string | null
  action_type: ActionType
  description: string
  taken_at: string
  outcome: string | null
  alert_id: string | null
  recommendation_id: string | null
}
```

```typescript
// src/types/winery.ts
export interface WineryDto {
  id: string
  name: string
  code: string
  location: string | null
  created_at: string
}
```

```typescript
// src/types/vineyard.ts
export interface VineyardDto {
  id: string
  winery_id: string
  name: string
  location: string | null
  hectares: number | null
  created_at: string
}

export interface HarvestLotDto {
  id: string
  vineyard_id: string
  vintage_year: number
  variety_name: string
  mass_kg: number
  harvest_date: string
  notes: string | null
}
```

- [ ] **Step 8: Create `src/types/index.ts`**

```typescript
export * from './auth'
export * from './fermentation'
export * from './sample'
export * from './protocol'
export * from './alert'
export * from './analysis'
export * from './action'
export * from './winery'
export * from './vineyard'
```

- [ ] **Step 9: Install and run tests**

```bash
cd frontend && pnpm install
cd packages/shared && pnpm test
```

Expected: PASS — type tests pass.

- [ ] **Step 10: Commit**

```bash
git add frontend/packages/shared/
git commit -m "feat(shared): add TypeScript DTO types matching all backend response shapes"
```

---

## Task 7: packages/shared — TokenStorage + ApiClient

**Files to create:**
- `frontend/packages/shared/src/storage/index.ts`
- `frontend/packages/shared/src/storage/cookie.ts`
- `frontend/packages/shared/src/api/client.ts`
- `frontend/packages/shared/__tests__/client.test.ts`

- [ ] **Step 1: Write failing ApiClient test**

```typescript
// frontend/packages/shared/__tests__/client.test.ts
import { describe, it, expect, vi } from 'vitest'
import { ApiClient, AuthExpiredError } from '../src/api/client'
import type { TokenStorage } from '../src/storage/index'

const makeStorage = (accessToken: string | null = 'test-token'): TokenStorage => ({
  getAccessToken: vi.fn().mockResolvedValue(accessToken),
  setAccessToken: vi.fn().mockResolvedValue(undefined),
  getRefreshToken: vi.fn().mockResolvedValue('refresh-token'),
  setRefreshToken: vi.fn().mockResolvedValue(undefined),
  clear: vi.fn().mockResolvedValue(undefined),
})

describe('ApiClient', () => {
  it('can be instantiated with base URLs and storage', () => {
    const client = new ApiClient({
      baseURLs: {
        fermentation: 'http://localhost:8000',
        winery: 'http://localhost:8001',
        fruitOrigin: 'http://localhost:8002',
        analysis: 'http://localhost:8003',
      },
      tokenStorage: makeStorage(),
    })
    expect(client).toBeDefined()
    expect(client.fermentation).toBeDefined()
    expect(client.winery).toBeDefined()
    expect(client.fruitOrigin).toBeDefined()
    expect(client.analysis).toBeDefined()
  })

  it('exports AuthExpiredError', () => {
    expect(AuthExpiredError).toBeDefined()
    const err = new AuthExpiredError()
    expect(err).toBeInstanceOf(Error)
    expect(err.message).toBe('Authentication expired')
  })
})
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd frontend/packages/shared && pnpm test
```

Expected: FAIL — `Cannot find module '../src/api/client'`

- [ ] **Step 3: Create `src/storage/index.ts`**

```typescript
export interface TokenStorage {
  getAccessToken(): Promise<string | null>
  setAccessToken(token: string): Promise<void>
  getRefreshToken(): Promise<string | null>
  setRefreshToken(token: string): Promise<void>
  clear(): Promise<void>
}
```

- [ ] **Step 4: Create `src/storage/cookie.ts`**

```typescript
import Cookies from 'js-cookie'
import type { TokenStorage } from './index'

const ACCESS_TOKEN_KEY = 'wine_access_token'
const REFRESH_TOKEN_KEY = 'wine_refresh_token'

export class CookieTokenStorage implements TokenStorage {
  async getAccessToken(): Promise<string | null> {
    return Cookies.get(ACCESS_TOKEN_KEY) ?? null
  }

  async setAccessToken(token: string): Promise<void> {
    Cookies.set(ACCESS_TOKEN_KEY, token, { sameSite: 'strict' })
  }

  async getRefreshToken(): Promise<string | null> {
    return Cookies.get(REFRESH_TOKEN_KEY) ?? null
  }

  async setRefreshToken(token: string): Promise<void> {
    Cookies.set(REFRESH_TOKEN_KEY, token, { expires: 7, sameSite: 'strict' })
  }

  async clear(): Promise<void> {
    Cookies.remove(ACCESS_TOKEN_KEY)
    Cookies.remove(REFRESH_TOKEN_KEY)
  }
}
```

- [ ] **Step 5: Create `src/api/client.ts`**

```typescript
import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios'
import type { TokenStorage } from '../storage/index'
import type { LoginResponseDto, RefreshResponseDto, UserDto } from '../types/auth'

export class AuthExpiredError extends Error {
  constructor() {
    super('Authentication expired')
    this.name = 'AuthExpiredError'
  }
}

interface ApiClientConfig {
  baseURLs: {
    fermentation: string
    winery: string
    fruitOrigin: string
    analysis: string
  }
  tokenStorage: TokenStorage
}

export class ApiClient {
  public fermentation: AxiosInstance
  public winery: AxiosInstance
  public fruitOrigin: AxiosInstance
  public analysis: AxiosInstance

  private tokenStorage: TokenStorage
  private isRefreshing = false
  private refreshSubscribers: Array<(token: string) => void> = []

  constructor(config: ApiClientConfig) {
    this.tokenStorage = config.tokenStorage
    this.fermentation = this.createInstance(config.baseURLs.fermentation)
    this.winery = this.createInstance(config.baseURLs.winery)
    this.fruitOrigin = this.createInstance(config.baseURLs.fruitOrigin)
    this.analysis = this.createInstance(config.baseURLs.analysis)
  }

  private createInstance(baseURL: string): AxiosInstance {
    const instance = axios.create({ baseURL })

    instance.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
      const token = await this.tokenStorage.getAccessToken()
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`
      }
      return config
    })

    instance.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token) => {
                originalRequest.headers = {
                  ...originalRequest.headers,
                  Authorization: `Bearer ${token}`,
                }
                originalRequest._retry = true
                resolve(instance(originalRequest))
              })
            })
          }

          originalRequest._retry = true
          this.isRefreshing = true

          try {
            const refreshToken = await this.tokenStorage.getRefreshToken()
            const response = await axios.post<RefreshResponseDto>(
              `${this.fermentation.defaults.baseURL}/api/v1/auth/refresh`,
              { refresh_token: refreshToken }
            )
            const newToken = response.data.access_token
            await this.tokenStorage.setAccessToken(newToken)

            this.refreshSubscribers.forEach((cb) => cb(newToken))
            this.refreshSubscribers = []
            this.isRefreshing = false

            originalRequest.headers = {
              ...originalRequest.headers,
              Authorization: `Bearer ${newToken}`,
            }
            return instance(originalRequest)
          } catch {
            this.isRefreshing = false
            this.refreshSubscribers = []
            await this.tokenStorage.clear()
            throw new AuthExpiredError()
          }
        }
        return Promise.reject(error)
      }
    )

    return instance
  }

  async login(username: string, password: string): Promise<LoginResponseDto> {
    const response = await this.fermentation.post<LoginResponseDto>(
      '/api/v1/auth/login',
      { username, password }
    )
    await this.tokenStorage.setAccessToken(response.data.access_token)
    await this.tokenStorage.setRefreshToken(response.data.refresh_token)
    return response.data
  }

  async logout(): Promise<void> {
    await this.tokenStorage.clear()
  }

  async getCurrentUser(): Promise<UserDto> {
    const response = await this.fermentation.get<UserDto>('/api/v1/auth/me')
    return response.data
  }
}
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
cd frontend/packages/shared && pnpm test
```

Expected: PASS — 2 ApiClient tests pass.

- [ ] **Step 7: Commit**

```bash
git add frontend/packages/shared/src/storage/ frontend/packages/shared/src/api/client.ts frontend/packages/shared/__tests__/client.test.ts
git commit -m "feat(shared): add TokenStorage interface, CookieTokenStorage, and ApiClient with 401 auto-refresh"
```

---

## Task 8: packages/shared — API function factories

**Files to create:** All files under `frontend/packages/shared/src/api/` (14 domain files + index)

- [ ] **Step 1: Create `src/api/fermentation.ts`**

```typescript
import type { ApiClient } from './client'
import type { FermentationDto, PaginatedResponse, FermentationStatisticsDto } from '../types/fermentation'
import type { CreateFermentationData, BlendFermentationData, UpdateFermentationData } from '@wine/ui/schemas'

export function createFermentationApi(client: ApiClient) {
  return {
    list(params?: { page?: number; size?: number; status?: string }): Promise<PaginatedResponse<FermentationDto>> {
      return client.fermentation.get('/api/v1/fermentations', { params }).then(r => r.data)
    },
    get(id: string): Promise<FermentationDto> {
      return client.fermentation.get(`/api/v1/fermentations/${id}`).then(r => r.data)
    },
    create(data: CreateFermentationData): Promise<FermentationDto> {
      return client.fermentation.post('/api/v1/fermentations', data).then(r => r.data)
    },
    createBlend(data: BlendFermentationData): Promise<FermentationDto> {
      return client.fermentation.post('/api/v1/fermentations/blends', data).then(r => r.data)
    },
    update(id: string, data: UpdateFermentationData): Promise<FermentationDto> {
      return client.fermentation.patch(`/api/v1/fermentations/${id}`, data).then(r => r.data)
    },
    complete(id: string): Promise<FermentationDto> {
      return client.fermentation.post(`/api/v1/fermentations/${id}/complete`).then(r => r.data)
    },
    getStatistics(id: string): Promise<FermentationStatisticsDto> {
      return client.fermentation.get(`/api/v1/fermentations/${id}/statistics`).then(r => r.data)
    },
    getTimeline(id: string): Promise<unknown[]> {
      return client.fermentation.get(`/api/v1/fermentations/${id}/timeline`).then(r => r.data)
    },
  }
}
```

- [ ] **Step 2: Create `src/api/sample.ts`, `src/api/alert.ts`**

```typescript
// sample.ts
import type { ApiClient } from './client'
import type { SampleDto } from '../types/sample'
import type { SampleFormData } from '@wine/ui/schemas'

export function createSampleApi(client: ApiClient) {
  return {
    create(fermentationId: string, data: SampleFormData): Promise<SampleDto> {
      return client.fermentation.post(`/api/v1/fermentations/${fermentationId}/samples`, data).then(r => r.data)
    },
    list(fermentationId: string): Promise<SampleDto[]> {
      return client.fermentation.get(`/api/v1/fermentations/${fermentationId}/samples`).then(r => r.data)
    },
    getLatest(fermentationId: string): Promise<SampleDto | null> {
      return client.fermentation
        .get(`/api/v1/fermentations/${fermentationId}/samples/latest`)
        .then(r => r.data)
        .catch(() => null)
    },
  }
}
```

```typescript
// alert.ts
import type { ApiClient } from './client'
import type { AlertDto } from '../types/alert'

export function createAlertApi(client: ApiClient) {
  return {
    listForExecution(executionId: string): Promise<AlertDto[]> {
      return client.fermentation.get(`/api/v1/executions/${executionId}/alerts`).then(r => r.data)
    },
    acknowledge(alertId: string): Promise<AlertDto> {
      return client.fermentation.post(`/api/v1/alerts/${alertId}/acknowledge`).then(r => r.data)
    },
    dismiss(alertId: string): Promise<AlertDto> {
      return client.fermentation.post(`/api/v1/alerts/${alertId}/dismiss`).then(r => r.data)
    },
  }
}
```

- [ ] **Step 3: Create analysis, recommendation, advisory API files**

```typescript
// analysis.ts
import type { ApiClient } from './client'
import type { AnalysisDto, AnomalyDto } from '../types/analysis'

export function createAnalysisApi(client: ApiClient) {
  return {
    trigger(fermentationId: string): Promise<AnalysisDto> {
      return client.analysis.post('/api/v1/analyses', { fermentation_id: fermentationId }).then(r => r.data)
    },
    get(id: string): Promise<AnalysisDto> {
      return client.analysis.get(`/api/v1/analyses/${id}`).then(r => r.data)
    },
    listForFermentation(fermentationId: string): Promise<AnalysisDto[]> {
      return client.analysis.get(`/api/v1/analyses/fermentation/${fermentationId}`).then(r => r.data)
    },
  }
}
```

```typescript
// recommendation.ts
import type { ApiClient } from './client'
import type { RecommendationDto } from '../types/analysis'

export function createRecommendationApi(client: ApiClient) {
  return {
    get(id: string): Promise<RecommendationDto> {
      return client.analysis.get(`/api/v1/recommendations/${id}`).then(r => r.data)
    },
    apply(id: string): Promise<RecommendationDto> {
      return client.analysis.put(`/api/v1/recommendations/${id}/apply`).then(r => r.data)
    },
  }
}
```

```typescript
// advisory.ts
import type { ApiClient } from './client'
import type { AdvisoryDto } from '../types/analysis'

export function createAdvisoryApi(client: ApiClient) {
  return {
    listForFermentation(fermentationId: string): Promise<AdvisoryDto[]> {
      return client.fermentation.get(`/api/v1/fermentations/${fermentationId}/advisories`).then(r => r.data)
    },
    acknowledge(id: string): Promise<AdvisoryDto> {
      return client.analysis.post(`/api/v1/advisories/${id}/acknowledge`).then(r => r.data)
    },
  }
}
```

- [ ] **Step 4: Create protocol, execution, step-completion, action API files**

```typescript
// protocol.ts
import type { ApiClient } from './client'
import type { ProtocolDto } from '../types/protocol'
import type { ProtocolFormData } from '@wine/ui/schemas'

export function createProtocolApi(client: ApiClient) {
  return {
    list(): Promise<ProtocolDto[]> {
      return client.fermentation.get('/api/v1/protocols').then(r => r.data)
    },
    get(id: string): Promise<ProtocolDto> {
      return client.fermentation.get(`/api/v1/protocols/${id}`).then(r => r.data)
    },
    create(data: ProtocolFormData): Promise<ProtocolDto> {
      return client.fermentation.post('/api/v1/protocols', data).then(r => r.data)
    },
    update(id: string, data: Partial<ProtocolFormData>): Promise<ProtocolDto> {
      return client.fermentation.patch(`/api/v1/protocols/${id}`, data).then(r => r.data)
    },
    delete(id: string): Promise<void> {
      return client.fermentation.delete(`/api/v1/protocols/${id}`).then(() => undefined)
    },
    clone(id: string): Promise<ProtocolDto> {
      return client.fermentation.post(`/api/v1/protocols/${id}/clone`).then(r => r.data)
    },
  }
}
```

```typescript
// protocol-steps.ts
import type { ApiClient } from './client'
import type { ProtocolStepDto } from '../types/protocol'
import type { ProtocolStepFormData } from '@wine/ui/schemas'

export function createProtocolStepsApi(client: ApiClient) {
  return {
    list(protocolId: string): Promise<ProtocolStepDto[]> {
      return client.fermentation.get(`/api/v1/protocols/${protocolId}/steps`).then(r => r.data)
    },
    add(protocolId: string, data: ProtocolStepFormData): Promise<ProtocolStepDto> {
      return client.fermentation.post(`/api/v1/protocols/${protocolId}/steps`, data).then(r => r.data)
    },
    update(protocolId: string, stepId: string, data: Partial<ProtocolStepFormData>): Promise<ProtocolStepDto> {
      return client.fermentation.patch(`/api/v1/protocols/${protocolId}/steps/${stepId}`, data).then(r => r.data)
    },
    delete(protocolId: string, stepId: string): Promise<void> {
      return client.fermentation.delete(`/api/v1/protocols/${protocolId}/steps/${stepId}`).then(() => undefined)
    },
  }
}
```

```typescript
// execution.ts
import type { ApiClient } from './client'
import type { ProtocolExecutionDto } from '../types/protocol'

export function createExecutionApi(client: ApiClient) {
  return {
    start(fermentationId: string, protocolId: string): Promise<ProtocolExecutionDto> {
      return client.fermentation
        .post(`/api/v1/fermentations/${fermentationId}/execute`, { protocol_id: protocolId })
        .then(r => r.data)
    },
    get(id: string): Promise<ProtocolExecutionDto> {
      return client.fermentation.get(`/api/v1/executions/${id}`).then(r => r.data)
    },
    list(): Promise<ProtocolExecutionDto[]> {
      return client.fermentation.get('/api/v1/executions').then(r => r.data)
    },
  }
}
```

```typescript
// step-completion.ts
import type { ApiClient } from './client'
import type { StepCompletionDto } from '../types/protocol'
import type { StepCompletionFormData } from '@wine/ui/schemas'

export function createStepCompletionApi(client: ApiClient) {
  return {
    complete(executionId: string, data: StepCompletionFormData): Promise<StepCompletionDto> {
      return client.fermentation.post(`/api/v1/executions/${executionId}/complete`, data).then(r => r.data)
    },
    list(executionId: string): Promise<StepCompletionDto[]> {
      return client.fermentation.get(`/api/v1/executions/${executionId}/completions`).then(r => r.data)
    },
    get(id: string): Promise<StepCompletionDto> {
      return client.fermentation.get(`/api/v1/completions/${id}`).then(r => r.data)
    },
  }
}
```

```typescript
// action.ts
import type { ApiClient } from './client'
import type { ActionDto } from '../types/action'
import type { ActionFormData, UpdateActionOutcomeData } from '@wine/ui/schemas'

export function createActionApi(client: ApiClient) {
  return {
    create(fermentationId: string, data: ActionFormData): Promise<ActionDto> {
      return client.fermentation.post(`/api/v1/fermentations/${fermentationId}/actions`, data).then(r => r.data)
    },
    listForFermentation(fermentationId: string): Promise<ActionDto[]> {
      return client.fermentation.get(`/api/v1/fermentations/${fermentationId}/actions`).then(r => r.data)
    },
    updateOutcome(id: string, data: UpdateActionOutcomeData): Promise<ActionDto> {
      return client.fermentation.patch(`/api/v1/actions/${id}/outcome`, data).then(r => r.data)
    },
  }
}
```

- [ ] **Step 5: Create winery, vineyard, harvest-lot API files**

```typescript
// winery.ts
import type { ApiClient } from './client'
import type { WineryDto } from '../types/winery'
import type { WineryFormData } from '@wine/ui/schemas'

export function createWineryApi(client: ApiClient) {
  return {
    list(): Promise<WineryDto[]> {
      return client.winery.get('/api/v1/admin/wineries').then(r => r.data)
    },
    get(id: string): Promise<WineryDto> {
      return client.winery.get(`/api/v1/admin/wineries/${id}`).then(r => r.data)
    },
    create(data: WineryFormData): Promise<WineryDto> {
      return client.winery.post('/api/v1/admin/wineries', data).then(r => r.data)
    },
    update(id: string, data: Partial<WineryFormData>): Promise<WineryDto> {
      return client.winery.patch(`/api/v1/admin/wineries/${id}`, data).then(r => r.data)
    },
    delete(id: string): Promise<void> {
      return client.winery.delete(`/api/v1/admin/wineries/${id}`).then(() => undefined)
    },
  }
}
```

```typescript
// vineyard.ts
import type { ApiClient } from './client'
import type { VineyardDto } from '../types/vineyard'

export function createVineyardApi(client: ApiClient) {
  return {
    list(): Promise<VineyardDto[]> {
      return client.fruitOrigin.get('/api/v1/vineyards/').then(r => r.data)
    },
    get(id: string): Promise<VineyardDto> {
      return client.fruitOrigin.get(`/api/v1/vineyards/${id}`).then(r => r.data)
    },
    create(data: { name: string; location?: string; hectares?: number }): Promise<VineyardDto> {
      return client.fruitOrigin.post('/api/v1/vineyards/', data).then(r => r.data)
    },
    update(id: string, data: Partial<{ name: string; location: string; hectares: number }>): Promise<VineyardDto> {
      return client.fruitOrigin.patch(`/api/v1/vineyards/${id}`, data).then(r => r.data)
    },
    delete(id: string): Promise<void> {
      return client.fruitOrigin.delete(`/api/v1/vineyards/${id}`).then(() => undefined)
    },
  }
}
```

```typescript
// harvest-lot.ts
import type { ApiClient } from './client'
import type { HarvestLotDto } from '../types/vineyard'

export function createHarvestLotApi(client: ApiClient) {
  return {
    list(vineyardId?: string): Promise<HarvestLotDto[]> {
      return client.fruitOrigin
        .get('/api/v1/harvest-lots/', { params: vineyardId ? { vineyard_id: vineyardId } : {} })
        .then(r => r.data)
    },
    get(id: string): Promise<HarvestLotDto> {
      return client.fruitOrigin.get(`/api/v1/harvest-lots/${id}`).then(r => r.data)
    },
    create(data: {
      vineyard_id: string
      vintage_year: number
      variety_name: string
      mass_kg: number
      harvest_date: string
      notes?: string
    }): Promise<HarvestLotDto> {
      return client.fruitOrigin.post('/api/v1/harvest-lots/', data).then(r => r.data)
    },
  }
}
```

- [ ] **Step 6: Create `src/api/index.ts`**

```typescript
export { ApiClient, AuthExpiredError } from './client'
export { createFermentationApi } from './fermentation'
export { createSampleApi } from './sample'
export { createProtocolApi } from './protocol'
export { createProtocolStepsApi } from './protocol-steps'
export { createExecutionApi } from './execution'
export { createStepCompletionApi } from './step-completion'
export { createAlertApi } from './alert'
export { createActionApi } from './action'
export { createAnalysisApi } from './analysis'
export { createRecommendationApi } from './recommendation'
export { createAdvisoryApi } from './advisory'
export { createWineryApi } from './winery'
export { createVineyardApi } from './vineyard'
export { createHarvestLotApi } from './harvest-lot'
```

- [ ] **Step 7: Run tests and type-check**

```bash
cd frontend/packages/shared && pnpm test && pnpm type-check
```

Expected: PASS — all tests pass, zero TypeScript errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/packages/shared/src/api/
git commit -m "feat(shared): add typed API function factories for all backend endpoints"
```

---

## Task 9: packages/shared — Auth hooks + root index

**Files to create:**
- `frontend/packages/shared/src/hooks/useAuth.ts`
- `frontend/packages/shared/src/hooks/useCurrentUser.ts`
- `frontend/packages/shared/src/hooks/useRole.ts`
- `frontend/packages/shared/src/hooks/usePolling.ts`
- `frontend/packages/shared/src/hooks/useStaleDataWarning.ts`
- `frontend/packages/shared/src/hooks/index.ts`
- `frontend/packages/shared/src/sync/sync-queue.ts`
- `frontend/packages/shared/src/sync/index.ts`
- `frontend/packages/shared/src/index.ts`
- `frontend/packages/shared/__tests__/useAuth.test.ts`

- [ ] **Step 1: Write failing hook tests**

```typescript
// frontend/packages/shared/__tests__/useAuth.test.ts
import { describe, it, expect, vi } from 'vitest'

vi.mock('../src/api/client', () => ({
  ApiClient: vi.fn(),
  AuthExpiredError: class AuthExpiredError extends Error {
    constructor() { super('expired') }
  },
}))

describe('useAuth module', () => {
  it('exports useAuth function', async () => {
    const mod = await import('../src/hooks/useAuth')
    expect(typeof mod.makeUseAuth).toBe('function')
  })
})

describe('useRole module', () => {
  it('exports useRole function', async () => {
    const mod = await import('../src/hooks/useRole')
    expect(typeof mod.useRole).toBe('function')
  })
})

describe('usePolling module', () => {
  it('exports usePolling function', async () => {
    const mod = await import('../src/hooks/usePolling')
    expect(typeof mod.usePolling).toBe('function')
  })
})
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd frontend/packages/shared && pnpm test
```

Expected: FAIL — `Cannot find module '../src/hooks/useAuth'`

- [ ] **Step 3: Create `src/hooks/useCurrentUser.ts`**

```typescript
import { useQuery } from '@tanstack/react-query'
import type { UserDto } from '../types/auth'
import type { ApiClient } from '../api/client'

export function makeUseCurrentUser(client: ApiClient) {
  return function useCurrentUser() {
    return useQuery<UserDto>({
      queryKey: ['currentUser'],
      queryFn: () => client.getCurrentUser(),
      staleTime: 5 * 60 * 1000,
    })
  }
}
```

- [ ] **Step 4: Create `src/hooks/useRole.ts`**

```typescript
import type { UserRole } from '../types/auth'

export function useRole(role: UserRole | undefined) {
  return {
    role,
    isAdmin: role === 'ADMIN',
    isWinemaker: role === 'WINEMAKER',
    hasRole: (r: UserRole) => role === r,
  }
}
```

- [ ] **Step 5: Create `src/hooks/usePolling.ts`**

```typescript
import { useQuery, type QueryKey } from '@tanstack/react-query'

interface UsePollingOptions {
  intervalMs?: number
  enabled?: boolean
}

export function usePolling<T>(
  queryKey: QueryKey,
  queryFn: () => Promise<T>,
  options: UsePollingOptions = {}
) {
  const { intervalMs = 30_000, enabled = true } = options

  return useQuery<T>({
    queryKey,
    queryFn,
    refetchInterval: enabled ? intervalMs : false,
    refetchIntervalInBackground: false,
    enabled,
  })
}
```

- [ ] **Step 6: Create `src/hooks/useStaleDataWarning.ts`**

```typescript
import { useQueryClient, type QueryKey } from '@tanstack/react-query'

const STALE_THRESHOLD_MS = 4 * 60 * 60 * 1000 // 4 hours

export function useStaleDataWarning(queryKey: QueryKey) {
  const queryClient = useQueryClient()
  const state = queryClient.getQueryState(queryKey as string[])

  if (!state?.dataUpdatedAt) {
    return { isStale: false, staleSinceMinutes: 0 }
  }

  const ageMins = (Date.now() - state.dataUpdatedAt) / 60_000
  const isStale = Date.now() - state.dataUpdatedAt > STALE_THRESHOLD_MS

  return { isStale, staleSinceMinutes: Math.round(ageMins) }
}
```

- [ ] **Step 7: Create `src/hooks/useAuth.ts`**

```typescript
import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { ApiClient } from '../api/client'

export function makeUseAuth(client: ApiClient) {
  return function useAuth() {
    const queryClient = useQueryClient()

    const login = useCallback(async (username: string, password: string) => {
      await client.login(username, password)
      await queryClient.invalidateQueries({ queryKey: ['currentUser'] })
    }, [queryClient])

    const logout = useCallback(async () => {
      await client.logout()
      queryClient.clear()
    }, [queryClient])

    return { login, logout }
  }
}
```

- [ ] **Step 8: Create `src/hooks/index.ts`**

```typescript
export { makeUseAuth } from './useAuth'
export { makeUseCurrentUser } from './useCurrentUser'
export { useRole } from './useRole'
export { usePolling } from './usePolling'
export { useStaleDataWarning } from './useStaleDataWarning'
```

- [ ] **Step 9: Create `src/sync/sync-queue.ts` and `src/sync/index.ts`**

```typescript
// sync-queue.ts — placeholder for offline sync (Iteration 3+)
export class SyncQueue {
  private queue: Array<() => Promise<void>> = []

  enqueue(task: () => Promise<void>): void {
    this.queue.push(task)
  }

  async flush(): Promise<void> {
    while (this.queue.length > 0) {
      const task = this.queue.shift()!
      await task()
    }
  }

  get size(): number {
    return this.queue.length
  }
}
```

```typescript
// sync/index.ts
export { SyncQueue } from './sync-queue'
```

- [ ] **Step 10: Create `src/index.ts`**

```typescript
export * from './types'
export * from './api'
export * from './hooks'
export * from './storage'
```

- [ ] **Step 11: Run all tests**

```bash
cd frontend/packages/shared && pnpm test
```

Expected: PASS — all tests pass.

- [ ] **Step 12: Commit**

```bash
git add frontend/packages/shared/src/hooks/ frontend/packages/shared/src/sync/ frontend/packages/shared/src/index.ts frontend/packages/shared/__tests__/useAuth.test.ts
git commit -m "feat(shared): add auth hooks, polling hook, stale data warning, and SyncQueue"
```

---

## Verification checklist

- [ ] `cd frontend/packages/shared && pnpm test` — all tests pass
- [ ] `cd frontend/packages/shared && pnpm type-check` — zero TypeScript errors
- [ ] `packages/shared` has no direct `process.env` or `document` references (confirm with grep — must be injectable via constructor)
- [ ] `ApiClient` accepts any `TokenStorage` implementation (web cookies or mobile SecureStore)

## Final commit

```bash
git add .
git commit -m "feat: complete frontend iteration 2 — packages/shared with ApiClient, API factories, and hooks"
```

---

## Handoff to Iteration 3

Iteration 3 (`2026-04-19-frontend-iteration-3-web.md`) scaffolds `apps/web` on top of this.
Prerequisites before starting Iteration 3:
- This branch merged
- Both `@wine/ui` and `@wine/shared` resolve as workspace dependencies
- `pnpm install` works from `frontend/`
