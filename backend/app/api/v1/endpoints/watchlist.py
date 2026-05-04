from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.watchlist import WatchlistAdd, WatchlistResponse
from app.services.watchlist import add_symbol, get_user_watchlist, remove_symbol

router = APIRouter()


@router.get("", response_model=list[WatchlistResponse])
async def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WatchlistResponse]:
    return get_user_watchlist(db, current_user.id)


@router.post("", response_model=WatchlistResponse, status_code=201)
async def add_to_watchlist(
    body: WatchlistAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistResponse:
    try:
        return add_symbol(db, current_user.id, body.symbol)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Symbol {body.symbol.upper()} is already in your watchlist",
        )


@router.delete("/{symbol}", status_code=200)
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    removed = remove_symbol(db, current_user.id, symbol)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol {symbol.upper()} not found in your watchlist",
        )
    return {"detail": f"{symbol.upper()} removed from watchlist"}
