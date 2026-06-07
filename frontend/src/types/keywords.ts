export type SearchKeyword = {
  id: number
  keyword: string
  category: string | null
  brand: string | null
  model_group: string | null
  priority: number
  active: boolean
  created_at: string
  updated_at: string
}

export type SearchKeywordCreate = {
  keyword: string
  category?: string | null
  brand?: string | null
  model_group?: string | null
  priority?: number
  active?: boolean
}
