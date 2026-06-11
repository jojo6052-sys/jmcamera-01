from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utc_now


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("yahoo_auction_candidates.id", ondelete="CASCADE"), index=True)
    user_decision: Mapped[str] = mapped_column(String(32), nullable=False)
    purchased: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    actual_purchase_price_jpy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    actual_condition: Mapped[str | None] = mapped_column(String(64))
    inspection_result: Mapped[str | None] = mapped_column(Text)
    sold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    actual_sale_price_jpy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    actual_profit_jpy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    returned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    complaint: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    repair_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_prediction_was_correct: Mapped[bool | None] = mapped_column(Boolean)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
