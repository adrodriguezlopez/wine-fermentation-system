import { z } from 'zod'

export const FERMENTATION_STATUSES = ['ACTIVE', 'LAG', 'SLOW', 'STUCK', 'DECLINE', 'COMPLETED'] as const

export const FermentationStatusSchema = z.enum(FERMENTATION_STATUSES)

export type FermentationStatus = z.infer<typeof FermentationStatusSchema>

export const FERMENTATION_STATUS_LABEL: Record<FermentationStatus, string> = {
  ACTIVE: 'Active',
  LAG: 'Lag',
  SLOW: 'Slow',
  STUCK: 'Stuck',
  DECLINE: 'Decline',
  COMPLETED: 'Completed',
}

export const FERMENTATION_STATUS_COLOR: Record<FermentationStatus, string> = {
  ACTIVE: '#16A34A',
  LAG: '#2563EB',
  SLOW: '#D97706',
  STUCK: '#DC2626',
  DECLINE: '#9333EA',
  COMPLETED: '#6B7280',
}
