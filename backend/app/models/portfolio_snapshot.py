from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer

from app.core.database import Base


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    total_value = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    total_pnl = Column(Float, nullable=False)
    asset_count = Column(Integer, nullable=False)
