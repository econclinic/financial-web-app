from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.watchlist import WatchlistItem


def get_user_watchlist(db: Session, user_id: int) -> list[WatchlistItem]:
    return (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user_id)
        .order_by(WatchlistItem.created_at.desc())
        .all()
    )


def add_symbol(db: Session, user_id: int, symbol: str) -> WatchlistItem:
    item = WatchlistItem(user_id=user_id, symbol=symbol.upper())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(item)
    return item


def remove_symbol(db: Session, user_id: int, symbol: str) -> bool:
    item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == user_id,
            WatchlistItem.symbol == symbol.upper(),
        )
        .first()
    )
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True
