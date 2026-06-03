export type Candidate = {
  id: number
  auction_id: string
  title: string
  url: string
  current_price_jpy: number | null
  buyout_price_jpy: number | null
  bid_count: number
  end_time: string | null
  seller_id: string | null
  seller_rating: number | null
  description: string | null
  image_urls: string[]
  search_keyword: string | null
  status: string
  latest_total_score: number | null
  latest_rank: string | null
}

export type RecommendationScore = {
  id: number
  candidate_id: number
  similarity_score: number | null
  expected_sale_price_usd: number | null
  expected_sale_price_jpy: number | null
  expected_profit_jpy: number | null
  expected_profit_margin: number | null
  recommended_max_bid_jpy: number | null
  seller_risk_score: number | null
  description_risk_score: number | null
  image_risk_score: number | null
  total_score: number | null
  rank: string | null
  reason: string | null
  caution: string | null
  created_at: string
  updated_at: string
}

export type FeedbackRequest = {
  user_decision: 'purchase' | 'skip' | 'review'
  notes?: string
}
