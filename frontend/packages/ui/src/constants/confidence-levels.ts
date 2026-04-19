export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW'

export const CONFIDENCE_LABEL: Record<ConfidenceLevel, string> = {
  HIGH: 'High',
  MEDIUM: 'Medium',
  LOW: 'Low',
}

export const CONFIDENCE_COLOR: Record<ConfidenceLevel, string> = {
  HIGH: '#16A34A',
  MEDIUM: '#D97706',
  LOW: '#DC2626',
}
