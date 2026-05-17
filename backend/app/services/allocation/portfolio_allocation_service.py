"""Portfolio allocation and exposure analytics service.

Read-only analytics layer that computes portfolio composition from
current positions and market prices.

Dependency flow: API -> this service -> portfolio repo + market data service.
Does NOT modify snapshots, performance, or caching logic.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.portfolio import PortfolioTransaction
from app.repositories.portfolio_transaction_repository import (
    get_user_transactions,
)
from app.services.market_data_service import get_current_prices_map

logger = logging.getLogger(__name__)

_ASSET_TYPE_MAP: dict[str, str] = {
    "crypto": "crypto",
    "stock": "equity",
}


def _build_positions(
    transactions: list[PortfolioTransaction],
) -> list[dict]:
    """Aggregate transactions into position dicts with net quantity."""
    agg: dict[str, dict] = {}
    for txn in transactions:
        sym = txn.symbol
        if sym not in agg:
            agg[sym] = {
                "symbol": sym,
                "asset_type": _ASSET_TYPE_MAP.get(txn.asset_type, txn.asset_type),
                "buy_qty": 0.0,
                "sell_qty": 0.0,
            }
        entry = agg[sym]
        if txn.transaction_type == "buy":
            entry["buy_qty"] += txn.quantity
        else:
            entry["sell_qty"] += txn.quantity

    positions: list[dict] = []
    for entry in agg.values():
        net_qty = entry["buy_qty"] - entry["sell_qty"]
        if net_qty <= 0:
            continue
        positions.append(
            {
                "symbol": entry["symbol"],
                "asset_type": entry["asset_type"],
                "quantity": net_qty,
            }
        )
    return positions


def get_portfolio_allocation(
    db: Session,
    user_id: int,
) -> dict:
    """Compute per-asset allocation with current market prices."""
    transactions = get_user_transactions(db, user_id)
    positions = _build_positions(transactions)

    if not positions:
        return {"total_value": 0.0, "assets": []}

    symbols = [p["symbol"] for p in positions]
    try:
        prices = get_current_prices_map(symbols)
    except Exception:
        logger.warning("market_data_service unavailable; using empty prices")
        prices = {}

    assets: list[dict] = []
    total_value = 0.0
    for pos in positions:
        price = prices.get(pos["symbol"], 0.0)
        value = pos["quantity"] * price
        total_value += value
        assets.append(
            {
                "symbol": pos["symbol"],
                "quantity": pos["quantity"],
                "price": price,
                "value": value,
                "asset_type": pos["asset_type"],
            }
        )

    for asset in assets:
        asset["weight"] = asset["value"] / total_value if total_value > 0 else None

    assets.sort(key=lambda a: (-a["value"], a["symbol"]))

    return {
        "total_value": round(total_value, 2),
        "assets": [
            {
                "symbol": a["symbol"],
                "quantity": round(a["quantity"], 8),
                "price": a["price"],
                "value": round(a["value"], 2),
                "weight": round(a["weight"], 4) if a["weight"] is not None else None,
                "asset_type": a["asset_type"],
            }
            for a in assets
        ],
    }


def get_portfolio_exposure(
    db: Session,
    user_id: int,
) -> dict:
    """Compute exposure aggregated by asset class."""
    alloc = get_portfolio_allocation(db, user_id)
    total_value = alloc["total_value"]

    if not alloc["assets"]:
        return {"total_value": 0.0, "exposures": []}

    class_values: dict[str, float] = {}
    for asset in alloc["assets"]:
        cls = asset["asset_type"]
        class_values[cls] = class_values.get(cls, 0.0) + asset["value"]

    exposures: list[dict] = []
    for cls, value in class_values.items():
        weight = value / total_value if total_value > 0 else None
        exposures.append(
            {
                "asset_class": cls,
                "value": round(value, 2),
                "weight": round(weight, 4) if weight is not None else None,
            }
        )

    exposures.sort(key=lambda e: (-e["value"], e["asset_class"]))

    return {"total_value": total_value, "exposures": exposures}


def get_top_positions(
    db: Session,
    user_id: int,
    limit: int = 5,
) -> list[dict]:
    """Return the largest portfolio positions by value."""
    alloc = get_portfolio_allocation(db, user_id)

    if not alloc["assets"]:
        return []

    return [
        {
            "symbol": a["symbol"],
            "value": a["value"],
            "weight": a["weight"],
        }
        for a in alloc["assets"][:limit]
    ]
