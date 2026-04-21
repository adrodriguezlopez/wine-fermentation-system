export interface VineyardDto {
  id: string
  winery_id: string
  name: string
  location: string | null
  hectares: number | null
  created_at: string
}

export interface HarvestLotDto {
  id: string
  vineyard_id: string
  vintage_year: number
  variety_name: string
  mass_kg: number
  harvest_date: string
  notes: string | null
}
