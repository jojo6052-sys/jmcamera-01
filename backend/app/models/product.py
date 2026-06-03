from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    es_number: Mapped[str | None] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    normalized_title: Mapped[str | None] = mapped_column(String(512), index=True)
    brand: Mapped[str | None] = mapped_column(String(128), index=True)
    model: Mapped[str | None] = mapped_column(String(128), index=True)
    category: Mapped[str | None] = mapped_column(String(128), index=True)
    mount: Mapped[str | None] = mapped_column(String(128))
    condition_rank: Mapped[str | None] = mapped_column(String(32))
    purchase_price_jpy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    sale_price_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    sale_price_jpy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    gross_profit_jpy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    final_profit_jpy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    profit_margin: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    purchased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    listed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    days_to_sell: Mapped[int | None] = mapped_column(Integer)
    sales_channel: Mapped[str | None] = mapped_column(String(64))
    buyer_country: Mapped[str | None] = mapped_column(String(64))
    returned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    complaint: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    repair_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seller_id: Mapped[str | None] = mapped_column(String(128), index=True)
    source_platform: Mapped[str | None] = mapped_column(String(64))
    source_url: Mapped[str | None] = mapped_column(String(1024))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
