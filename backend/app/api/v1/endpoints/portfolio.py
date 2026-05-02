from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.portfolio import PortfolioTransaction
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioSummaryResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.services.portfolio import (
    create_transaction,
    get_portfolio_summary,
    get_transactions,
)

router = APIRouter()


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def add_transaction(
    body: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioTransaction:
    return create_transaction(db, current_user.id, body)


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PortfolioTransaction]:
    return get_transactions(db, current_user.id)


@router.get("/summary", response_model=PortfolioSummaryResponse)
async def portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioSummaryResponse:
    return get_portfolio_summary(db, current_user.id)
