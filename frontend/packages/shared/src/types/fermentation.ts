import type { FermentationStatus } from '@wine/ui/constants'

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
  days_fermenting: number
  current_density: number | null
  temperature_current: number | null
  density_drop_percent: number | null
  estimated_alcohol: number | null
}
