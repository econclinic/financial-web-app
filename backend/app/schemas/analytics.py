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


class AllocationEntry(BaseModel):
    symbol: str
    weight: float


class DiversificationInfo(BaseModel):
    asset_count: int
    largest_position_pct: float


class PortfolioAnalyticsResponse(BaseModel):
    total_value: float
    total_cost: float
    total_pnl: float
    return_pct: float
    allocation: list[AllocationEntry]
    diversification: DiversificationInfo


class SnapshotResponse(BaseModel):
    timestamp: str
    total_value: float
    total_cost: float
    total_pnl: float
    asset_count: int

    model_config = {"from_attributes": True}


class SnapshotHistoryPoint(BaseModel):
    timestamp: str
    value: float


class SnapshotHistoryResponse(BaseModel):
    range: str
    points: list[SnapshotHistoryPoint]


class PerformanceWindowReturn(BaseModel):
    absolute: float
    percent: float


class PerformanceReturns(BaseModel):
    seven_d: PerformanceWindowReturn | None = None
    thirty_d: PerformanceWindowReturn | None = None
    ninety_d: PerformanceWindowReturn | None = None
    one_y: PerformanceWindowReturn | None = None


class PerformanceSummaryResponse(BaseModel):
    current_value: float
    as_of: str
    returns: PerformanceReturns


class PerformanceHistoryPoint(BaseModel):
    timestamp: str
    total_value: float
    total_cost: float
    total_pnl: float


class PerformanceHistoryResponse(BaseModel):
    range: str
    points: list[PerformanceHistoryPoint]
