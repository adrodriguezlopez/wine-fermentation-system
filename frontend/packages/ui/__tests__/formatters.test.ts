import { describe, it, expect } from 'vitest'
import { formatDensity, formatDensityShort } from '../src/formatters/density'
import { formatBrix } from '../src/formatters/brix'
import { formatCelsius } from '../src/formatters/temperature'
import { formatKg, formatDays, formatPercent } from '../src/formatters/units'
import { formatDeviationScore } from '../src/formatters/deviation'

describe('formatDensity', () => {
  it('formats to 4 decimal places with unit', () => {
    expect(formatDensity(1.0823)).toBe('1.0823 g/cm³')
  })
})

describe('formatDensityShort', () => {
  it('formats to 3 decimal places without unit', () => {
    expect(formatDensityShort(1.0823)).toBe('1.082')
  })
})

describe('formatBrix', () => {
  it('formats with °Bx unit', () => {
    expect(formatBrix(22.4)).toBe('22.4 °Bx')
  })
})

describe('formatCelsius', () => {
  it('formats with °C unit', () => {
    expect(formatCelsius(18.5)).toBe('18.5 °C')
  })
})

describe('formatKg', () => {
  it('formats with thousands separator', () => {
    expect(formatKg(5000)).toBe('5,000 kg')
  })
})

describe('formatDays', () => {
  it('formats day count', () => {
    expect(formatDays(14)).toBe('14 days')
    expect(formatDays(1)).toBe('1 day')
  })
})

describe('formatPercent', () => {
  it('converts fraction to percentage', () => {
    expect(formatPercent(0.87)).toBe('87%')
  })
})

describe('formatDeviationScore', () => {
  it('formats positive deviation with plus sign', () => {
    expect(formatDeviationScore(2.3)).toBe('+2.3σ')
  })
  it('formats negative deviation with minus sign', () => {
    expect(formatDeviationScore(-1.1)).toBe('−1.1σ')
  })
})
