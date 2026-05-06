"""Portfolio analytics service.

Computes performance insights, allocation breakdowns, and historical
value timeseries from existing portfolio transactions and market data.

Heavy operations are cached in-memory for 5 minutes per user.
"""

import time
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.portfolio import PortfolioTransaction
from app.services.market_data import get_latest_quotes, get_price_history
from app.services.market_data_service import get_current_prices_map

CACHE_TTL = 300  # 5 minutes

_overview_cache: dict[int, tuple[float, dict]] = {}


def _cache_get(user_id: int) -> dict | None:
    entry = _overview_cache.get(user_id)
    if entry and time.time() - entry[0] < CACHE_TTL:
        return entry[1]
    return None


def _cache_set(user_id: int, data: dict) -> None:
    _overview_cache[user_id] = (time.time(), data)


@dataclass
class _Position:
    symbol: str
    asset_type: str
    buy_qty: float = 0.0
    buy_cost: float = 0.0
    sell_qty: float = 0.0
    transactions: list = field(default_factory=list)

    @property
    def net_qty(self) -> float:
        return round(self.buy_qty - self.sell_qty, 8)

    @property
    def avg_price(self) -> float:
        return round(self.buy_cost / self.buy_qty, 2) if self.buy_qty > 0 else 0.0

    @property
    def cost_basis(self) -> float:
        return round(self.net_qty * self.avg_price, 2)


def _build_positions(db: Session, user_id: int) -> dict[str, _Position]:
    txns = (
        db.query(PortfolioTransaction)
        .filter(PortfolioTransaction.user_id == user_id)
        .order_by(PortfolioTransaction.timestamp.asc())
        .all()
    )
    positions: dict[str, _Position] = {}
    for txn in txns:
        sym = txn.symbol
        if sym not in positions:
            positions[sym] = _Position(symbol=sym, asset_type=txn.asset_type)
        pos = positions[sym]
        pos.transactions.append(txn)
        if txn.transaction_type == "buy":
            pos.buy_qty += txn.quantity
            pos.buy_cost += txn.quantity * txn.price
        else:
            pos.sell_qty += txn.quantity
    return positions


def calculate_portfolio_overview(db: Session, user_id: int) -> dict:
    cached = _cache_get(user_id)
    if cached:
        return cached

    positions = _build_positions(db, user_id)
    active = {s: p for s, p in positions.items() if p.net_qty > 0}

    if not active:
        result = {
            "total_value": 0.0,
            "total_cost_basis": 0.0,
            "total_pnl": 0.0,
            "today_change_value": 0.0,
            "today_change_percent": 0.0,
            "top_gainers": [],
            "top_losers": [],
            "allocation_by_asset_type": {},
            "allocation_by_symbol": {},
        }
        _cache_set(user_id, result)
        return result

    symbols = list(active.keys())
    prices = get_current_prices_map(symbols)
    quotes_list = get_latest_quotes()
    quotes = {q.symbol: q for q in quotes_list}

    total_value = 0.0
    total_cost = 0.0
    today_change_value = 0.0
    asset_type_values: dict[str, float] = {}
    symbol_values: dict[str, float] = {}
    symbol_pnl: list[dict] = []

    for sym, pos in active.items():
        cur_price = prices.get(sym, pos.avg_price)
        value = round(pos.net_qty * cur_price, 2)
        cost = pos.cost_basis
        pnl = round(value - cost, 2)
        pnl_pct = round((pnl / cost) * 100, 2) if cost > 0 else 0.0

        total_value += value
        total_cost += cost

        quote = quotes.get(sym)
        if quote:
            change_pct_24h = quote.change_percent
            sym_today_change = round(value * (change_pct_24h / 100), 2)
            today_change_value += sym_today_change
        else:
            change_pct_24h = 0.0

        at = pos.asset_type
        asset_type_values[at] = asset_type_values.get(at, 0.0) + value
        symbol_values[sym] = value

        symbol_pnl.append({
            "symbol": sym,
            "pnl": pnl,
            "pnl_percent": pnl_pct,
            "current_price": cur_price,
            "value": value,
        })

    total_pnl = round(total_value - total_cost, 2)
    today_pct = round((today_change_value / (total_value - today_change_value)) * 100, 2) if total_value - today_change_value > 0 else 0.0

    alloc_asset = {k: round((v / total_value) * 100, 2) for k, v in asset_type_values.items()} if total_value > 0 else {}
    alloc_symbol = {k: round((v / total_value) * 100, 2) for k, v in symbol_values.items()} if total_value > 0 else {}

    sorted_pnl = sorted(symbol_pnl, key=lambda x: x["pnl_percent"], reverse=True)
    top_gainers = [s for s in sorted_pnl if s["pnl_percent"] >= 0][:5]
    top_losers = [s for s in reversed(sorted_pnl) if s["pnl_percent"] < 0][:5]

    result = {
        "total_value": round(total_value, 2),
        "total_cost_basis": round(total_cost, 2),
        "total_pnl": total_pnl,
        "today_change_value": round(today_change_value, 2),
        "today_change_percent": today_pct,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "allocation_by_asset_type": alloc_asset,
        "allocation_by_symbol": alloc_symbol,
    }
    _cache_set(user_id, result)
    return result


def calculate_allocation(db: Session, user_id: int) -> dict:
    overview = calculate_portfolio_overview(db, user_id)
    return {
        "allocation_by_asset_type": overview["allocation_by_asset_type"],
        "allocation_by_symbol": overview["allocation_by_symbol"],
    }


_RANGE_TO_DAYS = {
    "1m": 30,
    "3m": 90,
    "6m": 180,
    "1y": 365,
    "all": 365,
}


def build_time_series_history(
    db: Session, user_id: int, range_key: str = "1m"
) -> list[dict]:
    positions = _build_positions(db, user_id)
    active = {s: p for s, p in positions.items() if p.net_qty > 0}
    if not active:
        return []

    days = _RANGE_TO_DAYS.get(range_key, 30)

    symbol_histories: dict[str, list] = {}
    for sym in active:
        history = get_price_history(sym, days)
        if history:
            symbol_histories[sym] = history

    if not symbol_histories:
        return []

    max_len = max(len(h) for h in symbol_histories.values())
    timeseries: list[dict] = []

    for i in range(max_len):
        total = 0.0
        ts = None
        for sym, history in symbol_histories.items():
            if i < len(history):
                point = history[i]
                ts = point.timestamp.isoformat()
                total += round(active[sym].net_qty * point.price, 2)
        if ts:
            timeseries.append({"timestamp": ts, "value": round(total, 2)})

    return timeseries
