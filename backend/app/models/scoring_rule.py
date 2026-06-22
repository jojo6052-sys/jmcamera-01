from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utc_now


class ScoringRule(Base):
    __tablename__ = "scoring_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    match_type: Mapped[str] = mapped_column(String(32), nullable=False, default="keyword")
    pattern: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    score_adjustment: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    max_bid_adjustment_pct: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="info")
    reason: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
