export interface VineyardDto {
  id: number
  winery_id: number
  code: string
  name: string
  notes: string | null
  is_deleted: boolean
  created_at: string
  updated_at: string
  blocks_count: number | null
}

export interface VineyardListDto {
  vineyards: VineyardDto[]
  total: number
}

export interface HarvestLotDto {
  id: number
  winery_id: number
  block_id: number
  code: string
  harvest_date: string
  weight_kg: number
  brix_at_harvest: number | null
  brix_method: string | null
  brix_measured_at: string | null
  grape_variety: string | null
  clone: string | null
  rootstock: string | null
  pick_method: string | null
  pick_start_time: string | null
  pick_end_time: string | null
  bins_count: number | null
  field_temp_c: number | null
  notes: string | null
  is_deleted: boolean
  created_at: string
  updated_at: string
  vineyard_name: string | null
  vineyard_code: string | null
  block_name: string | null
  used_in_fermentation: boolean | null
}

export interface HarvestLotListDto {
  total: number
  lots: HarvestLotDto[]
  page: number | null
  page_size: number | null
  total_pages: number | null
}
