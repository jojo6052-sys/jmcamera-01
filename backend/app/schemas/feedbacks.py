from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class FeedbackBatchCreate(BaseModel):
    candidate_ids: list[int] = Field(min_length=1, max_length=50)
    user_decision: Literal['purchase', 'skip', 'review']
    notes: str | None = None

    @model_validator(mode='after')
    def validate_unique_candidate_ids(self):
        if len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise ValueError('candidate_ids must be unique')
        return self


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

    model_config = ConfigDict(from_attributes=True)
