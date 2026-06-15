from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utc_now


class RecommendationScore(Base):
    __tablename__ = "recommendation_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("yahoo_auction_candidates.id", ondelete="CASCADE"), index=True)
    similarity_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    expected_sale_price_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    expected_sale_price_jpy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    expected_profit_jpy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    expected_profit_margin: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    recommended_max_bid_jpy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    seller_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    description_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    image_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    total_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), index=True)
    rank: Mapped[str | None] = mapped_column(String(8), index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    caution: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
