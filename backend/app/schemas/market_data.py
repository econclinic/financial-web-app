from datetime import datetime

from pydantic import BaseModel


class MarketQuote(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    updated_at: datetime


class MarketDataLatestResponse(BaseModel):
    data: list[MarketQuote]


class PricePoint(BaseModel):
    timestamp: datetime
    price: float


class MarketDataHistoryResponse(BaseModel):
    symbol: str
    name: str
    history: list[PricePoint]
