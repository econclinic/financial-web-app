from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AssetType(str, Enum):
    crypto = "crypto"
    stock = "stock"


class TransactionType(str, Enum):
    buy = "buy"
    sell = "sell"


class TransactionCreate(BaseModel):
    symbol: str
    asset_type: AssetType
    transaction_type: TransactionType
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    symbol: str
    asset_type: AssetType
    transaction_type: TransactionType
    quantity: float
    price: float
    timestamp: datetime

    model_config = {"from_attributes": True}


class PositionResponse(BaseModel):
    symbol: str
    asset_type: AssetType
    total_quantity: float
    average_buy_price: float
    current_price: float
    total_value: float
    unrealized_pnl: float


class PortfolioSummaryResponse(BaseModel):
    total_value: float
    total_invested: float
    total_pnl: float
    positions: list[PositionResponse]
