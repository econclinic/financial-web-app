"""Portfolio performance service.

Computes performance metrics from persisted portfolio snapshots.
Does NOT call market_data_service, providers, or analytics engine.

Dependency flow: API -> this service -> snapshot repository -> snapshot table.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.repositories.portfolio_snapshot_repository import (
    get_closest_snapshot_at_or_before,
    get_latest_snapshot,
    get_snapshots,
)

RETURN_WINDOWS: dict[str, int] = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "1y": 365,
}


def _compute_return(
    current_value: float,
    prior_value: float,
) -> dict[str, float]:
    """Compute absolute and percentage return between two values."""
    absolute = round(current_value - prior_value, 2)
    percent = round(absolute / prior_value, 4) if prior_value != 0 else 0.0
    return {"absolute": absolute, "percent": percent}


def get_performance_summary(
    db: Session,
    user_id: int,
) -> dict | None:
    """Return a performance summary with return metrics for each window.

    Returns None if the user has no snapshots at all.
    """
    latest = get_latest_snapshot(db, user_id)
    if latest is None:
        return None

    now = latest.timestamp
    returns: dict[str, dict[str, float] | None] = {}

    for window_key, days in RETURN_WINDOWS.items():
        target = now - timedelta(days=days)
        prior = get_closest_snapshot_at_or_before(db, user_id, target)
        if prior is None or prior.id == latest.id:
            returns[window_key] = None
        else:
            returns[window_key] = _compute_return(latest.total_value, prior.total_value)

    return {
        "current_value": latest.total_value,
        "as_of": latest.timestamp.isoformat(),
        "returns": returns,
    }


def get_performance_history(
    db: Session,
    user_id: int,
    range_key: str,
) -> list[dict]:
    """Return snapshot timeseries for the requested range.

    Each item contains timestamp, total_value, total_cost, and total_pnl.
    Results are in chronological ascending order.
    """
    days = RETURN_WINDOWS[range_key]
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    snapshots = get_snapshots(db, user_id, start, end)
    return [
        {
            "timestamp": s.timestamp.isoformat(),
            "total_value": s.total_value,
            "total_cost": s.total_cost,
            "total_pnl": s.total_pnl,
        }
        for s in snapshots
    ]
