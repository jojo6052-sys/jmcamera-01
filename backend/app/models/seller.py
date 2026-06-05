from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Seller(Base):
    __tablename__ = "sellers"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    seller_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    seller_name: Mapped[str | None] = mapped_column(String(255))
    rating: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    total_purchases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_purchases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_purchases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_profit_jpy: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    return_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    repair_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    description_mismatch_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_whitelisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
