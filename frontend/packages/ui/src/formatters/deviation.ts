export function formatDeviationScore(score: number): string {
  const sign = score >= 0 ? '+' : '−'
  return `${sign}${Math.abs(score).toFixed(1)}σ`
}

export function formatDeviationSeverity(severity: string): string {
  return severity.charAt(0).toUpperCase() + severity.slice(1).toLowerCase()
}
