import type { FermentationStatus } from '@wine/ui/constants'
import type { SampleDto } from './sample'

export interface FermentationDto {
  id: number
  winery_id: number
  vintage_year: number
  yeast_strain: string
  vessel_code: string | null
  input_mass_kg: number
  initial_sugar_brix: number
  initial_density: number | null
  start_date: string
  status: FermentationStatus
  notes: string | null
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  // removed: pages — backend does not serialize this field
}

export interface FermentationStatisticsDto {
  fermentation_id: number
  status: string
  start_date: string
  duration_days: number | null
  total_samples: number
  samples_by_type: Record<string, number>
  initial_sugar: number | null
  latest_sugar: number | null
  sugar_drop: number | null
  avg_temperature: number | null
  avg_samples_per_day: number | null
}

export interface TimelineResponse {
  fermentation: FermentationDto
  samples: SampleDto[]
  sample_count: number
  first_sample_date: string | null
  last_sample_date: string | null
}
