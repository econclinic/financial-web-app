"""Portfolio performance engine.

Computes performance analytics from stored snapshots and current positions:
- Range-based portfolio returns with max drawdown
- Per-asset contribution to portfolio PnL
- Best/worst asset performers by return

Dependency flow:
  API -> this service -> snapshot repo / transaction repo / market data service
"""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.portfolio import PortfolioTransaction
from app.repositories.portfolio_snapshot_repository import (
    get_all_snapshots,
    get_latest_snapshot,
    get_snapshots,
)
from app.repositories.portfolio_transaction_repository import (
    get_user_transactions,
)
from app.services.market_data_service import get_current_prices_map

logger = logging.getLogger(__name__)

RANGE_DAYS: dict[str, int | None] = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "1y": 365,
    "all": None,
}

_ASSET_TYPE_MAP: dict[str, str] = {
    "crypto": "crypto",
    "stock": "equity",
}


def _compute_max_drawdown(values: list[float]) -> float:
    """Compute max drawdown from a sequence of portfolio values.

    Returns a non-positive decimal (e.g. -0.082 for 8.2% drawdown).
    Returns 0.0 if fewer than 2 values or all values are non-positive.
    """
    if len(values) < 2:
        return 0.0

    peak = values[0]
    max_dd = 0.0

    for val in values[1:]:
        if val > peak:
            peak = val
        if peak > 0:
            dd = (val - peak) / peak
            if dd < max_dd:
                max_dd = dd

    return max_dd


def get_range_performance(
    db: Session,
    user_id: int,
    range_key: str,
) -> dict:
    """Compute portfolio performance summary for a given range."""
    days = RANGE_DAYS[range_key]

    if days is None:
        snapshots = get_all_snapshots(db, user_id)
    else:
        latest = get_latest_snapshot(db, user_id)
        if latest is None:
            return _empty_performance(range_key)
        end = latest.timestamp
        start = end - timedelta(days=days)
        snapshots = get_snapshots(db, user_id, start, end)

    if not snapshots:
        return _empty_performance(range_key)

    first = snapshots[0]
    last = snapshots[-1]
    starting_value = first.total_value
    ending_value = last.total_value
    absolute_return = ending_value - starting_value

    if starting_value > 0:
        total_return = absolute_return / starting_value
    else:
        total_return = 0.0

    values = [s.total_value for s in snapshots]
    max_dd = _compute_max_drawdown(values)

    return {
        "range": range_key,
        "start_timestamp": first.timestamp.isoformat(),
        "end_timestamp": last.timestamp.isoformat(),
        "starting_value": starting_value,
        "ending_value": ending_value,
        "absolute_return": absolute_return,
        "total_return": total_return,
        "total_return_pct": total_return * 100,
        "max_drawdown": max_dd,
        "max_drawdown_pct": max_dd * 100,
        "snapshot_count": len(snapshots),
    }


def _empty_performance(range_key: str) -> dict:
    return {
        "range": range_key,
        "start_timestamp": None,
        "end_timestamp": None,
        "starting_value": 0.0,
        "ending_value": 0.0,
        "absolute_return": 0.0,
        "total_return": 0.0,
        "total_return_pct": 0.0,
        "max_drawdown": 0.0,
        "max_drawdown_pct": 0.0,
        "snapshot_count": 0,
    }


def _build_positions_with_cost(
    transactions: list[PortfolioTransaction],
) -> list[dict]:
    """Aggregate transactions into positions with quantity and cost basis."""
    agg: dict[str, dict] = {}
    for txn in transactions:
        sym = txn.symbol
        if sym not in agg:
            agg[sym] = {
                "symbol": sym,
                "asset_type": _ASSET_TYPE_MAP.get(txn.asset_type, txn.asset_type),
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

    positions: list[dict] = []
    for entry in agg.values():
        net_qty = entry["buy_qty"] - entry["sell_qty"]
        if net_qty <= 0:
            continue
        avg_cost = (
            entry["buy_cost"] / entry["buy_qty"] if entry["buy_qty"] > 0 else 0.0
        )
        cost_basis = net_qty * avg_cost
        positions.append(
            {
                "symbol": entry["symbol"],
                "asset_type": entry["asset_type"],
                "quantity": net_qty,
                "avg_cost": avg_cost,
                "cost_basis": cost_basis,
            }
        )
    return positions


def get_contribution(
    db: Session,
    user_id: int,
) -> dict:
    """Compute per-asset PnL contribution to the portfolio."""
    transactions = get_user_transactions(db, user_id)
    positions = _build_positions_with_cost(transactions)

    if not positions:
        return {"total_contribution": 0.0, "assets": []}

    symbols = [p["symbol"] for p in positions]
    try:
        prices = get_current_prices_map(symbols)
    except Exception:
        logger.warning("market_data_service unavailable; using empty prices")
        prices = {}

    assets: list[dict] = []
    total_contribution = 0.0

    for pos in positions:
        price = prices.get(pos["symbol"], 0.0)
        value = pos["quantity"] * price
        pnl = value - pos["cost_basis"]
        total_contribution += pnl
        assets.append(
            {
                "symbol": pos["symbol"],
                "asset_type": pos["asset_type"],
                "value": value,
                "cost_basis": pos["cost_basis"],
                "pnl": pnl,
                "contribution": pnl,
            }
        )

    for asset in assets:
        asset["contribution_weight"] = (
            asset["contribution"] / total_contribution
            if total_contribution != 0
            else 0.0
        )

    assets.sort(key=lambda a: (-a["contribution"], a["symbol"]))

    return {
        "total_contribution": total_contribution,
        "assets": [
            {
                "symbol": a["symbol"],
                "asset_type": a["asset_type"],
                "value": round(a["value"], 2),
                "cost_basis": round(a["cost_basis"], 2),
                "pnl": round(a["pnl"], 2),
                "contribution": round(a["contribution"], 2),
                "contribution_weight": round(a["contribution_weight"], 4),
            }
            for a in assets
        ],
    }


def get_performers(
    db: Session,
    user_id: int,
    limit: int = 5,
) -> dict:
    """Identify best and worst performers by return relative to cost basis."""
    transactions = get_user_transactions(db, user_id)
    positions = _build_positions_with_cost(transactions)

    if not positions:
        return {"best": [], "worst": []}

    symbols = [p["symbol"] for p in positions]
    try:
        prices = get_current_prices_map(symbols)
    except Exception:
        logger.warning("market_data_service unavailable; using empty prices")
        prices = {}

    items: list[dict] = []
    for pos in positions:
        price = prices.get(pos["symbol"], 0.0)
        value = pos["quantity"] * price
        pnl = value - pos["cost_basis"]
        ret = pnl / pos["cost_basis"] if pos["cost_basis"] > 0 else 0.0
        items.append(
            {
                "symbol": pos["symbol"],
                "asset_type": pos["asset_type"],
                "value": value,
                "cost_basis": pos["cost_basis"],
                "pnl": pnl,
                "return": ret,
                "return_pct": ret * 100,
            }
        )

    best = sorted(items, key=lambda x: (-x["return"], x["symbol"]))[:limit]
    worst = sorted(items, key=lambda x: (x["return"], x["symbol"]))[:limit]

    def _round_item(item: dict) -> dict:
        return {
            "symbol": item["symbol"],
            "asset_type": item["asset_type"],
            "value": round(item["value"], 2),
            "cost_basis": round(item["cost_basis"], 2),
            "pnl": round(item["pnl"], 2),
            "return": round(item["return"], 4),
            "return_pct": round(item["return_pct"], 2),
        }

    return {
        "best": [_round_item(i) for i in best],
        "worst": [_round_item(i) for i in worst],
    }
