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
