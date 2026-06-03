from datetime import datetime

from pydantic import BaseModel, Field


class YahooSearchRequest(BaseModel):
    keyword: str
    limit: int = 20
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    exclude_words: list[str] = Field(default_factory=list)


class CandidateRead(BaseModel):
    id: int
    auction_id: str
    title: str
    url: str
    current_price_jpy: float | None = None
    buyout_price_jpy: float | None = None
    bid_count: int
    end_time: datetime | None = None
    seller_id: str | None = None
    seller_rating: float | None = None
    description: str | None = None
    image_urls: list[str]
    search_keyword: str | None = None
    status: str
    latest_total_score: float | None = None
    latest_rank: str | None = None

    class Config:
        from_attributes = True
