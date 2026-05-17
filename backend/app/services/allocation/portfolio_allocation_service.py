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
        net_qty = round(entry["buy_qty"] - entry["sell_qty"], 8)
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
    transactions = (
        db.query(PortfolioTransaction)
        .filter(PortfolioTransaction.user_id == user_id)
        .all()
    )
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
        value = round(pos["quantity"] * price, 2)
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

    total_value = round(total_value, 2)

    for asset in assets:
        asset["weight"] = (
            round(asset["value"] / total_value, 4) if total_value > 0 else None
        )

    assets.sort(key=lambda a: a["value"], reverse=True)

    return {"total_value": total_value, "assets": assets}


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
        value = round(value, 2)
        weight = round(value / total_value, 4) if total_value > 0 else None
        exposures.append(
            {"asset_class": cls, "value": value, "weight": weight}
        )

    exposures.sort(key=lambda e: e["value"], reverse=True)

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
