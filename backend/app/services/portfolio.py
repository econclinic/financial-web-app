from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.portfolio import PortfolioTransaction
from app.schemas.portfolio import (
    PortfolioSummaryResponse,
    PositionResponse,
    TransactionCreate,
)
from app.services.market_data_service import get_current_prices_map


def create_transaction(
    db: Session, user_id: int, data: TransactionCreate
) -> PortfolioTransaction:
    symbol = data.symbol.upper()

    if data.transaction_type == "sell":
        owned = _get_owned_quantity(db, user_id, symbol)
        if data.quantity > owned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot sell {data.quantity} {symbol} — you only own {owned}",
            )

    txn = PortfolioTransaction(
        user_id=user_id,
        symbol=symbol,
        asset_type=data.asset_type.value,
        transaction_type=data.transaction_type.value,
        quantity=data.quantity,
        price=data.price,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def get_transactions(db: Session, user_id: int) -> list[PortfolioTransaction]:
    return (
        db.query(PortfolioTransaction)
        .filter(PortfolioTransaction.user_id == user_id)
        .order_by(PortfolioTransaction.timestamp.desc())
        .all()
    )


def get_portfolio_summary(db: Session, user_id: int) -> PortfolioSummaryResponse:
    transactions = (
        db.query(PortfolioTransaction)
        .filter(PortfolioTransaction.user_id == user_id)
        .all()
    )

    positions_map: dict[str, dict] = {}

    for txn in transactions:
        sym = txn.symbol
        if sym not in positions_map:
            positions_map[sym] = {
                "asset_type": txn.asset_type,
                "buy_quantity": 0.0,
                "buy_cost": 0.0,
                "sell_quantity": 0.0,
            }

        entry = positions_map[sym]
        if txn.transaction_type == "buy":
            entry["buy_quantity"] += txn.quantity
            entry["buy_cost"] += txn.quantity * txn.price
        else:
            entry["sell_quantity"] += txn.quantity

    symbols_in_portfolio = list(positions_map.keys())
    current_prices = get_current_prices_map(symbols_in_portfolio)
    positions: list[PositionResponse] = []
    total_value = 0.0
    total_invested = 0.0

    for sym, entry in positions_map.items():
        net_qty = round(entry["buy_quantity"] - entry["sell_quantity"], 8)
        if net_qty <= 0:
            continue

        avg_price = round(entry["buy_cost"] / entry["buy_quantity"], 2) if entry["buy_quantity"] > 0 else 0.0
        cur_price = current_prices.get(sym, avg_price)
        value = round(net_qty * cur_price, 2)
        invested = round(net_qty * avg_price, 2)
        pnl = round(value - invested, 2)

        positions.append(
            PositionResponse(
                symbol=sym,
                asset_type=entry["asset_type"],
                total_quantity=net_qty,
                average_buy_price=avg_price,
                current_price=cur_price,
                total_value=value,
                unrealized_pnl=pnl,
            )
        )

        total_value += value
        total_invested += invested

    total_pnl = round(total_value - total_invested, 2)
    pnl_pct = round((total_pnl / total_invested) * 100, 2) if total_invested > 0 else 0.0

    return PortfolioSummaryResponse(
        total_value=round(total_value, 2),
        total_invested=round(total_invested, 2),
        total_pnl=total_pnl,
        pnl_percentage=pnl_pct,
        positions=positions,
    )


def _get_owned_quantity(db: Session, user_id: int, symbol: str) -> float:
    transactions = (
        db.query(PortfolioTransaction)
        .filter(
            PortfolioTransaction.user_id == user_id,
            PortfolioTransaction.symbol == symbol,
        )
        .all()
    )

    total = 0.0
    for txn in transactions:
        if txn.transaction_type == "buy":
            total += txn.quantity
        else:
            total -= txn.quantity
    return round(total, 8)
