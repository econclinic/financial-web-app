from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.portfolio import PortfolioTransaction
from app.models.user import User
from app.repositories.portfolio_snapshot_repository import get_snapshots
from app.schemas.analytics import (
    PerformanceHistoryPoint,
    PerformanceHistoryResponse,
    PerformanceReturns,
    PerformanceSummaryResponse,
    PerformanceWindowReturn,
    PortfolioAnalyticsResponse,
    SnapshotHistoryPoint,
    SnapshotHistoryResponse,
    SnapshotResponse,
)
from app.schemas.portfolio import (
    PortfolioSummaryResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.services.analytics.portfolio_analytics import get_portfolio_analytics
from app.services.performance.portfolio_performance_service import (
    get_performance_history,
    get_performance_summary,
)
from app.services.portfolio import (
    create_transaction,
    get_portfolio_summary,
    get_transactions,
)
from app.services.portfolio_snapshot_service import create_snapshot

_WINDOW_KEY_TO_FIELD: dict[str, str] = {
    "7d": "seven_d",
    "30d": "thirty_d",
    "90d": "ninety_d",
    "1y": "one_y",
}

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


@router.get("/performance", response_model=PerformanceSummaryResponse)
async def portfolio_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PerformanceSummaryResponse:
    summary = get_performance_summary(db, current_user.id)
    if summary is None:
        return PerformanceSummaryResponse(
            current_value=0.0,
            as_of="",
            returns=PerformanceReturns(),
        )
    returns_data: dict[str, PerformanceWindowReturn | None] = {}
    for key, field_name in _WINDOW_KEY_TO_FIELD.items():
        raw = summary["returns"].get(key)
        returns_data[field_name] = (
            PerformanceWindowReturn(**raw) if raw is not None else None
        )
    return PerformanceSummaryResponse(
        current_value=summary["current_value"],
        as_of=summary["as_of"],
        returns=PerformanceReturns(**returns_data),
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
