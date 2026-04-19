export type RecommendationCategory = 'IMMEDIATE_ACTION' | 'MONITORING' | 'PREVENTIVE' | 'INFORMATIONAL'

export const RECOMMENDATION_CATEGORY_LABEL: Record<RecommendationCategory, string> = {
  IMMEDIATE_ACTION: 'Immediate Action',
  MONITORING: 'Monitor Closely',
  PREVENTIVE: 'Preventive',
  INFORMATIONAL: 'Info',
}

export const RECOMMENDATION_CATEGORY_COLOR: Record<RecommendationCategory, string> = {
  IMMEDIATE_ACTION: '#DC2626',
  MONITORING: '#D97706',
  PREVENTIVE: '#2563EB',
  INFORMATIONAL: '#6B7280',
}
