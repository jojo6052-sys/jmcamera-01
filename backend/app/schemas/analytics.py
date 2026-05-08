from pydantic import BaseModel


class BestSellerItem(BaseModel):
    title: str
    sales_count: int
    total_sales_jpy: float
    total_profit_jpy: float
    avg_profit_margin: float
    avg_days_to_sell: float


class CategoryAnalyticsItem(BaseModel):
    category: str
    total_sales_jpy: float
    total_profit_jpy: float
    avg_profit_margin: float
    avg_days_to_sell: float
