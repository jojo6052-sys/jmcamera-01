from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utc_now


class YahooAuctionCandidate(Base):
    __tablename__ = "yahoo_auction_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    auction_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    normalized_title: Mapped[str | None] = mapped_column(String(512), index=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    current_price_jpy: Mapped[float | None] = mapped_column(Numeric(12, 2))
    buyout_price_jpy: Mapped[float | None] = mapped_column(Numeric(12, 2))
    bid_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    seller_id: Mapped[str | None] = mapped_column(String(128), index=True)
    seller_rating: Mapped[float | None] = mapped_column(Numeric(5, 2))
    description: Mapped[str | None] = mapped_column(Text)
    image_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    search_keyword: Mapped[str | None] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32), default="new", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
