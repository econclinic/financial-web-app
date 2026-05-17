"""Allocation and diversification calculations.

All functions are pure — no service calls, no I/O.
"""

from __future__ import annotations

from app.services.analytics.metrics import PortfolioPosition


def calculate_allocation(
    positions: list[PortfolioPosition],
    prices: dict[str, float],
) -> list[dict[str, object]]:
    """Per-symbol allocation weights based on current market value.

    Returns a list sorted by weight descending.  Weights sum to 1.0
    (or the list is empty when total value is zero).
    """
    values: list[tuple[str, float]] = []
    total = 0.0
    for pos in positions:
        price = prices.get(pos.symbol)
        if price is not None:
            val = pos.quantity * price
            values.append((pos.symbol, val))
            total += val

    if total == 0:
        return []

    allocation = [
        {"symbol": sym, "weight": val / total}
        for sym, val in values
    ]
    allocation.sort(key=lambda a: a["weight"], reverse=True)
    return allocation


def largest_position_weight(
    allocation: list[dict[str, object]],
) -> float:
    """Weight of the largest position.  Returns 0.0 for empty portfolios."""
    if not allocation:
        return 0.0
    return float(allocation[0]["weight"])


def asset_count(positions: list[PortfolioPosition]) -> int:
    """Number of distinct positions."""
    return len(positions)
