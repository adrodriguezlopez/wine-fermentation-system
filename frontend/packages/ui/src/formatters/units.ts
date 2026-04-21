export function formatKg(value: number): string {
  return `${value.toLocaleString('en-US')} kg`
}

export function formatDays(value: number): string {
  return `${value} ${value === 1 ? 'day' : 'days'}`
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}
