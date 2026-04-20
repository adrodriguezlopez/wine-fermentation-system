import { z } from 'zod'

export const FERMENTATION_STATUSES = ['ACTIVE', 'SLOW', 'STUCK', 'COMPLETED'] as const

export const FermentationStatusSchema = z.enum(FERMENTATION_STATUSES)

export type FermentationStatus = z.infer<typeof FermentationStatusSchema>

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
