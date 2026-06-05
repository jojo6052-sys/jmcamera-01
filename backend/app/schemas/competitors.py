from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class CompetitorAnalyzeRequest(BaseModel):
    seller_url: HttpUrl
    include_active: bool = True
    include_sold: bool = True
    limit: int = Field(default=50, ge=1, le=100)

    @model_validator(mode="after")
    def validate_status_selection(self):
        if not self.include_active and not self.include_sold:
            raise ValueError("at least one of include_active or include_sold must be true")
        return self


class CompetitorKeywordCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    keyword: str
    category: str | None = "Competitor Research"
    brand: str | None = None
    model_group: str | None = None
    priority: int = Field(default=80, ge=1, le=999)
    active: bool = True


class CompetitorKeywordBulkCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    keywords: list[str] | None = None
    category: str | None = "Competitor Research"
    brand: str | None = None
    model_group: str | None = None
    priority: int = Field(default=80, ge=1, le=999)
    active: bool = True


class CompetitorItemRead(BaseModel):
    id: int
    seller_id: int
    marketplace: str
    external_item_id: str
    title: str
    normalized_title: str | None = None
    item_url: str
    image_url: str | None = None
    price: float | None = None
    currency: str | None = None
    item_status: str
    source_url: str
    first_seen_at: datetime
    last_seen_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompetitorSellerRead(BaseModel):
    id: int
    marketplace: str
    seller_username: str
    seller_url: str
    fetch_status: str
    last_error: str | None = None
    active_count: int
    sold_count: int
    avg_active_price: float | None = None
    avg_sold_price: float | None = None
    last_analyzed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompetitorAnalyzeResponse(BaseModel):
    seller: CompetitorSellerRead
    items: list[CompetitorItemRead]


class CompetitorKeywordSuggestion(BaseModel):
    keyword: str
    count: int


class CompetitorTopTerm(BaseModel):
    term: str
    count: int


class CompetitorInsights(BaseModel):
    seller_id: int
    seller_username: str
    active_count: int
    sold_count: int
    sell_through_rate: float | None = None
    avg_active_price: float | None = None
    avg_sold_price: float | None = None
    sold_active_price_gap: float | None = None
    top_sold_terms: list[CompetitorTopTerm]
    suggested_keywords: list[CompetitorKeywordSuggestion]
