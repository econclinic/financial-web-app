from fastapi import APIRouter, HTTPException, Query

from app.schemas.market_data import MarketDataHistoryResponse, MarketDataLatestResponse
from app.services.market_data import get_latest_quotes, get_price_history

router = APIRouter()


@router.get("/latest", response_model=MarketDataLatestResponse)
async def latest_market_data() -> MarketDataLatestResponse:
    quotes = get_latest_quotes()
    return MarketDataLatestResponse(data=quotes)


@router.get("/history", response_model=MarketDataHistoryResponse)
async def market_data_history(
    symbol: str = Query(..., description="Ticker symbol, e.g. BTC"),
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
) -> MarketDataHistoryResponse:
    history = get_price_history(symbol, days)
    if history is None:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    symbols_map = {"BTC": "Bitcoin", "ETH": "Ethereum", "AAPL": "Apple Inc."}
    return MarketDataHistoryResponse(
        symbol=symbol.upper(),
        name=symbols_map.get(symbol.upper(), symbol.upper()),
        history=history,
    )
