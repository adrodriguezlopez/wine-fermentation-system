export function formatDensity(value: number): string {
  return `${value.toFixed(4)} g/cm³`
}

export function formatDensityShort(value: number): string {
  return value.toFixed(3)
}
