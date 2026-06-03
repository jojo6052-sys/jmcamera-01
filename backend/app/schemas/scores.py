from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecommendationScoreRead(BaseModel):
    id: int
    candidate_id: int
    similarity_score: float | None = None
    expected_sale_price_usd: float | None = None
    expected_sale_price_jpy: float | None = None
    expected_profit_jpy: float | None = None
    expected_profit_margin: float | None = None
    recommended_max_bid_jpy: float | None = None
    seller_risk_score: float | None = None
    description_risk_score: float | None = None
    image_risk_score: float | None = None
    total_score: float | None = None
    rank: str | None = None
    reason: str | None = None
    caution: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
