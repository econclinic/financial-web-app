from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.analytics import (
    AllocationResponse,
    PortfolioHistoryResponse,
    PortfolioOverviewResponse,
)
from app.services.portfolio_analytics import (
    build_time_series_history,
    calculate_allocation,
    calculate_portfolio_overview,
)

router = APIRouter()


@router.get("/portfolio/overview", response_model=PortfolioOverviewResponse)
async def portfolio_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioOverviewResponse:
    data = calculate_portfolio_overview(db, current_user.id)
    return PortfolioOverviewResponse(**data)


@router.get("/portfolio/allocation", response_model=AllocationResponse)
async def portfolio_allocation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AllocationResponse:
    data = calculate_allocation(db, current_user.id)
    return AllocationResponse(**data)


@router.get("/portfolio/history", response_model=PortfolioHistoryResponse)
async def portfolio_history(
    range: str = Query(
        default="1m",
        pattern="^(1m|3m|6m|1y|all)$",
        description="Time range: 1m, 3m, 6m, 1y, or all",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioHistoryResponse:
    data = build_time_series_history(db, current_user.id, range)
    return PortfolioHistoryResponse(range=range, data=data)
