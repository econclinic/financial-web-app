"""Data access layer for portfolio snapshots.

Handles only database operations — no analytics computation.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.portfolio_snapshot import PortfolioSnapshot


def save_snapshot(db: Session, snapshot: PortfolioSnapshot) -> PortfolioSnapshot:
    """Persist a snapshot and return the refreshed instance."""
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_snapshots(
    db: Session,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
) -> list[PortfolioSnapshot]:
    """Return snapshots within a time window, ordered by timestamp ascending."""
    return (
        db.query(PortfolioSnapshot)
        .filter(
            PortfolioSnapshot.user_id == user_id,
            PortfolioSnapshot.timestamp >= start_time,
            PortfolioSnapshot.timestamp <= end_time,
        )
        .order_by(PortfolioSnapshot.timestamp.asc())
        .all()
    )


def get_recent_snapshots(
    db: Session,
    user_id: int,
    limit: int = 30,
) -> list[PortfolioSnapshot]:
    """Return the most recent snapshots, ordered by timestamp ascending."""
    rows = (
        db.query(PortfolioSnapshot)
        .filter(PortfolioSnapshot.user_id == user_id)
        .order_by(PortfolioSnapshot.timestamp.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()
    return rows
