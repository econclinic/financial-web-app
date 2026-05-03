from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.models.user import User
from app.services.market_data_service import get_live_prices

router = APIRouter()


@router.get("/prices")
async def get_market_prices(
    symbols: str = Query(
        default="BTC,ETH",
        description="Comma-separated list of symbols, e.g. BTC,ETH",
    ),
    current_user: User = Depends(get_current_user),
) -> dict[str, dict]:
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return get_live_prices(symbol_list)
