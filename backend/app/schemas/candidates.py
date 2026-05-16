from datetime import datetime
from pydantic import BaseModel


class YahooSearchRequest(BaseModel):
    keyword: str
    limit: int = 20


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

    class Config:
        from_attributes = True
