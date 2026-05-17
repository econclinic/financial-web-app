"""Pure financial calculation functions.

All functions are stateless and free of side effects — no external
service calls, no I/O. This makes them trivial to unit test.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PortfolioPosition:
    """Normalized position used by the analytics layer."""

    symbol: str
    asset_type: str  # "crypto" | "equity"
    quantity: float
    avg_cost: float


def calculate_position_value(quantity: float, price: float) -> float:
    """Market value of a single position."""
    return round(quantity * price, 2)


def calculate_portfolio_value(
    positions: list[PortfolioPosition],
    prices: dict[str, float],
) -> float:
    """Total market value of all positions with available prices."""
    total = 0.0
    for pos in positions:
        price = prices.get(pos.symbol)
        if price is not None:
            total += pos.quantity * price
    return round(total, 2)


def calculate_total_cost(positions: list[PortfolioPosition]) -> float:
    """Total cost basis across all positions."""
    return round(sum(pos.quantity * pos.avg_cost for pos in positions), 2)


def calculate_total_pnl(total_value: float, total_cost: float) -> float:
    """Unrealized profit / loss."""
    return round(total_value - total_cost, 2)


def calculate_return_pct(total_pnl: float, total_cost: float) -> float:
    """Return percentage. Returns 0.0 when cost basis is zero."""
    if total_cost == 0:
        return 0.0
    return round((total_pnl / total_cost) * 100, 2)
