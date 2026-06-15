from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utc_now


class CompetitorSeller(Base):
    __tablename__ = "competitor_sellers"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace: Mapped[str] = mapped_column(String(32), default="ebay", nullable=False, index=True)
    seller_username: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    seller_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    fetch_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    active_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sold_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_active_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    avg_sold_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    last_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    items: Mapped[list["CompetitorItem"]] = relationship(
        back_populates="seller",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("marketplace", "seller_username", name="uq_competitor_seller_marketplace_username"),)


class CompetitorItem(Base):
    __tablename__ = "competitor_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("competitor_sellers.id", ondelete="CASCADE"), nullable=False, index=True)
    marketplace: Mapped[str] = mapped_column(String(32), default="ebay", nullable=False, index=True)
    external_item_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    normalized_title: Mapped[str | None] = mapped_column(String(512), index=True)
    item_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1024))
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(8))
    item_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    raw: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    seller: Mapped[CompetitorSeller] = relationship(back_populates="items")

    __table_args__ = (UniqueConstraint("seller_id", "external_item_id", "item_status", name="uq_competitor_item_seller_external_status"),)
