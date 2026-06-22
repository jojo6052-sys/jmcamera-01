from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MatchType = Literal['keyword', 'description', 'seller_id']
RiskLevel = Literal['info', 'positive', 'warning', 'critical']


class ScoringRuleBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    match_type: MatchType = 'keyword'
    pattern: str = Field(min_length=1, max_length=255)
    score_adjustment: float = Field(default=0, ge=-50, le=50)
    max_bid_adjustment_pct: float = Field(default=0, ge=-50, le=50)
    risk_level: RiskLevel = 'info'
    reason: str | None = None
    enabled: bool = True


class ScoringRuleCreate(ScoringRuleBase):
    pass


class ScoringRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    match_type: MatchType | None = None
    pattern: str | None = Field(default=None, min_length=1, max_length=255)
    score_adjustment: float | None = Field(default=None, ge=-50, le=50)
    max_bid_adjustment_pct: float | None = Field(default=None, ge=-50, le=50)
    risk_level: RiskLevel | None = None
    reason: str | None = None
    enabled: bool | None = None


class ScoringRuleRead(ScoringRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
