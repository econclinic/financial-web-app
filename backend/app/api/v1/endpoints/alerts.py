from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.alert import AlertCreate, AlertResponse
from app.services.alerts import create_alert, delete_alert, get_user_alerts

router = APIRouter()


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AlertResponse]:
    return get_user_alerts(db, current_user.id)


@router.post("", response_model=AlertResponse, status_code=201)
async def add_alert(
    body: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertResponse:
    try:
        return create_alert(
            db,
            current_user.id,
            body.symbol,
            body.target_price,
            body.direction,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An active alert for {body.symbol.upper()} "
                f"{body.direction} ${body.target_price} already exists"
            ),
        )


@router.delete("/{alert_id}", status_code=200)
async def remove_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    removed = delete_alert(db, current_user.id, alert_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    return {"detail": "Alert deleted"}
