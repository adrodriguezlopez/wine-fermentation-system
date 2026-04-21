import type { SampleTypeKey } from '@wine/ui/constants'

export interface SampleDto {
  id: string
  fermentation_id: string
  sample_type: SampleTypeKey
  value: number
  recorded_at: string
  notes: string | null
  created_at: string
}
