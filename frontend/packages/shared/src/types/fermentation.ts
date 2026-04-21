import type { FermentationStatus } from '@wine/ui/constants'

export interface FermentationDto {
  id: string
  winery_id: string
  vintage_year: number
  yeast_strain: string
  vessel_code: string
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
  pages: number
}

export interface FermentationStatisticsDto {
  days_fermenting: number
  current_density: number | null
  temperature_current: number | null
  density_drop_percent: number | null
  estimated_alcohol: number | null
}
