from pydantic import BaseModel


class SymbolPnl(BaseModel):
    symbol: str
    pnl: float
    pnl_percent: float
    current_price: float
    value: float


class PortfolioOverviewResponse(BaseModel):
    total_value: float
    total_cost_basis: float
    total_pnl: float
    today_change_value: float
    today_change_percent: float
    top_gainers: list[SymbolPnl]
    top_losers: list[SymbolPnl]
    allocation_by_asset_type: dict[str, float]
    allocation_by_symbol: dict[str, float]


class AllocationResponse(BaseModel):
    allocation_by_asset_type: dict[str, float]
    allocation_by_symbol: dict[str, float]


class HistoryPoint(BaseModel):
    timestamp: str
    value: float


class PortfolioHistoryResponse(BaseModel):
    range: str
    data: list[HistoryPoint]
