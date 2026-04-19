export type FermentationStatus = 'ACTIVE' | 'SLOW' | 'STUCK' | 'COMPLETED'

export const FERMENTATION_STATUS_LABEL: Record<FermentationStatus, string> = {
  ACTIVE: 'Active',
  SLOW: 'Slow',
  STUCK: 'Stuck',
  COMPLETED: 'Completed',
}

export const FERMENTATION_STATUS_COLOR: Record<FermentationStatus, string> = {
  ACTIVE: '#16A34A',
  SLOW: '#D97706',
  STUCK: '#DC2626',
  COMPLETED: '#6B7280',
}
