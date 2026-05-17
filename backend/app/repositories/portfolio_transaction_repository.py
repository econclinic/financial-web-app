"""Data access layer for portfolio transactions.

Handles only database operations — no analytics computation.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.portfolio import PortfolioTransaction


def get_user_transactions(
    db: Session,
    user_id: int,
) -> list[PortfolioTransaction]:
    """Return all transactions for a user."""
    return (
        db.query(PortfolioTransaction)
        .filter(PortfolioTransaction.user_id == user_id)
        .all()
    )
