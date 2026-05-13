from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, UniqueConstraint

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "symbol",
            "direction",
            "target_price",
            "is_triggered",
            name="uq_active_alert",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String, nullable=False)
    target_price = Column(Float, nullable=False)
    direction = Column(String, nullable=False)  # price_above, price_below, daily_change_above, daily_change_below
    is_triggered = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    triggered_at = Column(DateTime(timezone=True), nullable=True)
