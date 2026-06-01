from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    user_decision: str = Field(min_length=1, max_length=32)
    purchased: bool = False
    actual_purchase_price_jpy: float | None = None
    actual_condition: str | None = None
    inspection_result: str | None = None
    sold: bool = False
    actual_sale_price_jpy: float | None = None
    actual_profit_jpy: float | None = None
    returned: bool = False
    complaint: bool = False
    repair_required: bool = False
    ai_prediction_was_correct: bool | None = None
    notes: str | None = None


class FeedbackRead(BaseModel):
    id: int
    candidate_id: int
    user_decision: str
    purchased: bool
    actual_purchase_price_jpy: float | None = None
    actual_condition: str | None = None
    inspection_result: str | None = None
    sold: bool
    actual_sale_price_jpy: float | None = None
    actual_profit_jpy: float | None = None
    returned: bool
    complaint: bool
    repair_required: bool
    ai_prediction_was_correct: bool | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
