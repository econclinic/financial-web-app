from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from app.core.database import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_user_symbol"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
