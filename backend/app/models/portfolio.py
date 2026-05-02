from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy import Enum as SAEnum

from app.core.database import Base


class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    asset_type = Column(SAEnum("crypto", "stock", name="asset_type_enum"), nullable=False)
    transaction_type = Column(
        SAEnum("buy", "sell", name="transaction_type_enum"), nullable=False
    )
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
