"""Portfolio snapshot creation service.

Orchestrates: portfolio → analytics → snapshot persistence.

Does NOT recompute analytics manually and does NOT call providers.
Uses the analytics layer exactly as the API does.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.portfolio_snapshot import PortfolioSnapshot
from app.repositories.portfolio_snapshot_repository import save_snapshot
from app.services.analytics.portfolio_analytics import get_portfolio_analytics

logger = logging.getLogger(__name__)


def create_snapshot(db: Session, user_id: int) -> PortfolioSnapshot:
    """Create and persist a portfolio snapshot for the given user.

    Steps:
    1. Run the existing analytics engine (which fetches positions and prices)
    2. Persist a snapshot record with the computed metrics
    """
    analytics = get_portfolio_analytics(db, user_id)

    snapshot = PortfolioSnapshot(
        user_id=user_id,
        total_value=analytics["total_value"],
        total_cost=analytics["total_cost"],
        total_pnl=analytics["total_pnl"],
        asset_count=analytics["diversification"]["asset_count"],
    )

    return save_snapshot(db, snapshot)
