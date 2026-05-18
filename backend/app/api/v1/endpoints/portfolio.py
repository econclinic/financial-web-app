from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.portfolio import PortfolioTransaction
from app.models.user import User
from app.repositories.portfolio_snapshot_repository import get_snapshots
from app.schemas.analytics import (
    AssetAllocationItem,
    AssetClassExposureItem,
    ContributionItem,
    ContributionResponse,
    PerformanceHistoryPoint,
    PerformanceHistoryResponse,
    PerformerItem,
    PerformersResponse,
    PortfolioAllocationResponse,
    PortfolioAnalyticsResponse,
    PortfolioExposureResponse,
    PortfolioPerformanceSummary,
    SnapshotHistoryPoint,
    SnapshotHistoryResponse,
    SnapshotResponse,
    TopPositionItem,
    TopPositionsResponse,
)
from app.schemas.portfolio import (
    PortfolioSummaryResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.services.allocation.portfolio_allocation_service import (
    get_portfolio_allocation,
    get_portfolio_exposure,
    get_top_positions,
)
from app.services.analytics.portfolio_analytics import get_portfolio_analytics
from app.services.analytics.portfolio_performance_engine import (
    get_contribution,
    get_performers,
    get_range_performance,
)
from app.services.performance.portfolio_performance_service import (
    get_performance_history,
)
from app.services.portfolio import (
    create_transaction,
    get_portfolio_summary,
    get_transactions,
)
from app.services.portfolio_snapshot_service import create_snapshot

router = APIRouter()


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def add_transaction(
    body: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioTransaction:
    return create_transaction(db, current_user.id, body)


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PortfolioTransaction]:
    return get_transactions(db, current_user.id)


@router.get("/summary", response_model=PortfolioSummaryResponse)
async def portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioSummaryResponse:
    return get_portfolio_summary(db, current_user.id)


@router.get("/analytics", response_model=PortfolioAnalyticsResponse)
async def portfolio_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioAnalyticsResponse:
    data = get_portfolio_analytics(db, current_user.id)
    return PortfolioAnalyticsResponse(**data)


_RANGE_TO_DAYS: dict[str, int] = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "1y": 365,
}


@router.post("/snapshot", response_model=SnapshotResponse, status_code=201)
async def take_snapshot(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SnapshotResponse:
    snap = create_snapshot(db, current_user.id)
    return SnapshotResponse(
        timestamp=snap.timestamp.isoformat(),
        total_value=snap.total_value,
        total_cost=snap.total_cost,
        total_pnl=snap.total_pnl,
        asset_count=snap.asset_count,
    )


@router.get("/history", response_model=SnapshotHistoryResponse)
async def portfolio_history_snapshots(
    range: str = Query(
        default="30d",
        pattern="^(7d|30d|90d|1y)$",
        description="Time range: 7d, 30d, 90d, or 1y",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SnapshotHistoryResponse:
    days = _RANGE_TO_DAYS[range]
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    snapshots = get_snapshots(db, current_user.id, start, end)
    points = [
        SnapshotHistoryPoint(
            timestamp=s.timestamp.isoformat(),
            value=s.total_value,
        )
        for s in snapshots
    ]
    return SnapshotHistoryResponse(range=range, points=points)


@router.get("/performance", response_model=PortfolioPerformanceSummary)
async def portfolio_performance(
    range: str = Query(
        default="30d",
        pattern="^(7d|30d|90d|1y|all)$",
        description="Time range: 7d, 30d, 90d, 1y, or all",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioPerformanceSummary:
    data = get_range_performance(db, current_user.id, range)
    return PortfolioPerformanceSummary(
        range=data["range"],
        start_timestamp=data["start_timestamp"],
        end_timestamp=data["end_timestamp"],
        starting_value=round(data["starting_value"], 2),
        ending_value=round(data["ending_value"], 2),
        absolute_return=round(data["absolute_return"], 2),
        total_return=round(data["total_return"], 4),
        total_return_pct=round(data["total_return_pct"], 2),
        max_drawdown=round(data["max_drawdown"], 4),
        max_drawdown_pct=round(data["max_drawdown_pct"], 2),
        snapshot_count=data["snapshot_count"],
    )


@router.get("/performance/history", response_model=PerformanceHistoryResponse)
async def portfolio_performance_history(
    range: str = Query(
        default="30d",
        pattern="^(7d|30d|90d|1y)$",
        description="Time range: 7d, 30d, 90d, or 1y",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PerformanceHistoryResponse:
    items = get_performance_history(db, current_user.id, range)
    points = [PerformanceHistoryPoint(**item) for item in items]
    return PerformanceHistoryResponse(range=range, points=points)


@router.get("/allocation", response_model=PortfolioAllocationResponse)
async def portfolio_allocation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioAllocationResponse:
    data = get_portfolio_allocation(db, current_user.id)
    assets = [
        AssetAllocationItem(
            symbol=a["symbol"],
            quantity=a["quantity"],
            price=a["price"],
            value=a["value"],
            weight=a["weight"],
        )
        for a in data["assets"]
    ]
    return PortfolioAllocationResponse(total_value=data["total_value"], assets=assets)


@router.get("/exposure", response_model=PortfolioExposureResponse)
async def portfolio_exposure(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioExposureResponse:
    data = get_portfolio_exposure(db, current_user.id)
    exposures = [
        AssetClassExposureItem(
            asset_class=e["asset_class"],
            value=e["value"],
            weight=e["weight"],
        )
        for e in data["exposures"]
    ]
    return PortfolioExposureResponse(
        total_value=data["total_value"], exposures=exposures
    )


@router.get("/top-positions", response_model=TopPositionsResponse)
async def portfolio_top_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TopPositionsResponse:
    items = get_top_positions(db, current_user.id)
    positions = [
        TopPositionItem(
            symbol=p["symbol"],
            value=p["value"],
            weight=p["weight"],
        )
        for p in items
    ]
    return TopPositionsResponse(positions=positions)


@router.get("/contribution", response_model=ContributionResponse)
async def portfolio_contribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ContributionResponse:
    data = get_contribution(db, current_user.id)
    assets = [
        ContributionItem(
            symbol=a["symbol"],
            asset_type=a["asset_type"],
            value=a["value"],
            cost_basis=a["cost_basis"],
            pnl=a["pnl"],
            contribution=a["contribution"],
            contribution_weight=a["contribution_weight"],
        )
        for a in data["assets"]
    ]
    return ContributionResponse(
        total_contribution=round(data["total_contribution"], 2),
        assets=assets,
    )


@router.get("/performers", response_model=PerformersResponse)
async def portfolio_performers(
    limit: int = Query(default=5, ge=1, le=50, description="Number of performers"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PerformersResponse:
    data = get_performers(db, current_user.id, limit)

    def _to_item(p: dict) -> PerformerItem:
        return PerformerItem(
            symbol=p["symbol"],
            asset_type=p["asset_type"],
            value=p["value"],
            cost_basis=p["cost_basis"],
            pnl=p["pnl"],
            return_val=p["return"],
            return_pct=p["return_pct"],
        )

    return PerformersResponse(
        best=[_to_item(p) for p in data["best"]],
        worst=[_to_item(p) for p in data["worst"]],
    )
