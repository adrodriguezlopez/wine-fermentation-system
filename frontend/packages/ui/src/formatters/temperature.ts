// Consistent spacing: no space between value and °C to match SAMPLE_TYPE_UNIT convention
export function formatCelsius(value: number): string {
  return `${value.toFixed(1)}°C`
}
