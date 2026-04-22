import type { SampleTypeKey } from '@wine/ui/constants'

export interface SampleDto {
  id: number
  fermentation_id: number
  sample_type: SampleTypeKey
  value: number
  units: string
  recorded_at: string
  created_at: string
  updated_at: string
}
