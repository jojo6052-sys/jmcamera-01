from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SearchKeyword(Base):
    __tablename__ = "search_keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(128))
    brand: Mapped[str | None] = mapped_column(String(128))
    model_group: Mapped[str | None] = mapped_column(String(128))
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
