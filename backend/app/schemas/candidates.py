from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class YahooSearchRequest(BaseModel):
    keyword: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=50)
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    exclude_words: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_price_range(self):
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise ValueError('min_price must be less than or equal to max_price')
        return self


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

    model_config = ConfigDict(from_attributes=True)
