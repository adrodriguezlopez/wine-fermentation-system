export interface WineryDto {
  id: number
  code: string
  name: string
  location: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface WineryListDto {
  items: WineryDto[]
  total: number
  limit: number
  offset: number
}
