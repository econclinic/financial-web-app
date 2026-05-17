"""Portfolio analytics orchestrator.

Coordinates the analytics workflow:
1. Retrieve portfolio positions from the existing portfolio storage
2. Normalize positions into the analytics-layer format
3. Request current prices via market_data_service (single call)
4. Run calculation functions from metrics / allocation modules
5. Assemble and return the final analytics response

Dependency flow: API → this module → market_data_service → providers.
This module never imports provider modules directly.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.portfolio import PortfolioTransaction
from app.services.analytics.allocation import (
    asset_count,
    calculate_allocation,
    largest_position_weight,
)
from app.services.analytics.metrics import (
    PortfolioPosition,
    calculate_portfolio_value,
    calculate_return_pct,
    calculate_total_cost,
    calculate_total_pnl,
)
from app.services.market_data_service import get_current_prices_map

logger = logging.getLogger(__name__)

# Map DB asset_type values to the analytics-layer convention
_ASSET_TYPE_MAP: dict[str, str] = {
    "crypto": "crypto",
    "stock": "equity",
}


def _normalize_positions(
    transactions: list[PortfolioTransaction],
) -> list[PortfolioPosition]:
    """Aggregate transactions into normalized analytics positions.

    Only positions with a positive net quantity are returned.
    """
    agg: dict[str, dict] = {}
    for txn in transactions:
        sym = txn.symbol
        if sym not in agg:
            agg[sym] = {
                "asset_type": txn.asset_type,
                "buy_qty": 0.0,
                "buy_cost": 0.0,
                "sell_qty": 0.0,
            }
        entry = agg[sym]
        if txn.transaction_type == "buy":
            entry["buy_qty"] += txn.quantity
            entry["buy_cost"] += txn.quantity * txn.price
        else:
            entry["sell_qty"] += txn.quantity

    positions: list[PortfolioPosition] = []
    for sym, entry in agg.items():
        net_qty = round(entry["buy_qty"] - entry["sell_qty"], 8)
        if net_qty <= 0:
            continue
        avg_cost = (
            round(entry["buy_cost"] / entry["buy_qty"], 2)
            if entry["buy_qty"] > 0
            else 0.0
        )
        positions.append(
            PortfolioPosition(
                symbol=sym,
                asset_type=_ASSET_TYPE_MAP.get(
                    entry["asset_type"], entry["asset_type"]
                ),
                quantity=net_qty,
                avg_cost=avg_cost,
            )
        )
    return positions


def get_portfolio_analytics(db: Session, user_id: int) -> dict:
    """Compute a snapshot of portfolio analytics for the given user.

    Returns a dict matching the ``GET /api/portfolio/analytics`` schema.
    """
    transactions = (
        db.query(PortfolioTransaction)
        .filter(PortfolioTransaction.user_id == user_id)
        .all()
    )

    positions = _normalize_positions(transactions)

    if not positions:
        return {
            "total_value": 0.0,
            "total_cost": 0.0,
            "total_pnl": 0.0,
            "return_pct": 0.0,
            "allocation": [],
            "diversification": {
                "asset_count": 0,
                "largest_position_pct": 0.0,
            },
        }

    # Single call to market_data_service
    symbols = [p.symbol for p in positions]
    try:
        prices = get_current_prices_map(symbols)
    except Exception:
        logger.warning("market_data_service unavailable; using empty prices")
        prices = {}

    total_value = calculate_portfolio_value(positions, prices)
    total_cost = calculate_total_cost(positions)
    total_pnl = calculate_total_pnl(total_value, total_cost)
    return_pct = calculate_return_pct(total_pnl, total_cost)

    allocation = calculate_allocation(positions, prices)
    largest_weight = largest_position_weight(allocation)
    count = asset_count(positions)

    return {
        "total_value": total_value,
        "total_cost": total_cost,
        "total_pnl": total_pnl,
        "return_pct": return_pct,
        "allocation": allocation,
        "diversification": {
            "asset_count": count,
            "largest_position_pct": largest_weight,
        },
    }
