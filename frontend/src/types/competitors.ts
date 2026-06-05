export type CompetitorSeller = {
  id: number
  marketplace: string
  seller_username: string
  seller_url: string
  fetch_status: string
  last_error: string | null
  active_count: number
  sold_count: number
  avg_active_price: number | null
  avg_sold_price: number | null
  last_analyzed_at: string | null
  created_at: string
  updated_at: string
}

export type CompetitorItem = {
  id: number
  seller_id: number
  marketplace: string
  external_item_id: string
  title: string
  normalized_title: string | null
  item_url: string
  image_url: string | null
  price: number | null
  currency: string | null
  item_status: 'active' | 'sold' | string
  source_url: string
  first_seen_at: string
  last_seen_at: string
}

export type CompetitorAnalyzeResponse = {
  seller: CompetitorSeller
  items: CompetitorItem[]
}


export type CompetitorTopTerm = {
  term: string
  count: number
}

export type CompetitorKeywordSuggestion = {
  keyword: string
  count: number
}

export type CompetitorInsights = {
  seller_id: number
  seller_username: string
  active_count: number
  sold_count: number
  sell_through_rate: number | null
  avg_active_price: number | null
  avg_sold_price: number | null
  sold_active_price_gap: number | null
  top_sold_terms: CompetitorTopTerm[]
  suggested_keywords: CompetitorKeywordSuggestion[]
}
