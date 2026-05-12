from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.notification import Notification


def get_user_alerts(db: Session, user_id: int) -> list[Alert]:
    return (
        db.query(Alert)
        .filter(Alert.user_id == user_id)
        .order_by(Alert.created_at.desc())
        .all()
    )


def create_alert(
    db: Session,
    user_id: int,
    symbol: str,
    target_price: float,
    direction: str,
) -> Alert:
    alert = Alert(
        user_id=user_id,
        symbol=symbol.upper(),
        target_price=target_price,
        direction=direction,
        is_triggered=False,
    )
    db.add(alert)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(alert)
    return alert


def delete_alert(db: Session, user_id: int, alert_id: int) -> bool:
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id, Alert.user_id == user_id)
        .first()
    )
    if not alert:
        return False
    db.delete(alert)
    db.commit()
    return True


def _check_condition(
    direction: str, price: float, change_24h: float, target: float
) -> bool:
    if direction == "price_above" or direction == "above":
        return price >= target
    if direction == "price_below" or direction == "below":
        return price <= target
    if direction == "daily_change_above":
        return change_24h >= target
    if direction == "daily_change_below":
        return change_24h <= target
    return False


def _notification_message(direction: str, symbol: str, target: float) -> str:
    if direction in ("price_above", "above"):
        return f"{symbol} crossed above {target:g}"
    if direction in ("price_below", "below"):
        return f"{symbol} dropped below {target:g}"
    if direction == "daily_change_above":
        return f"{symbol} daily change rose above {target:g}%"
    if direction == "daily_change_below":
        return f"{symbol} daily change dropped below {target:g}%"
    return f"{symbol} alert triggered at {target:g}"


def evaluate_alerts(
    db: Session,
    prices: dict[str, float],
    changes: dict[str, float] | None = None,
) -> int:
    """Check all active alerts against current prices and 24h changes.

    Returns the number of newly triggered alerts.
    """
    if changes is None:
        changes = {}

    active = db.query(Alert).filter(Alert.is_triggered.is_(False)).all()
    triggered_count = 0
    new_notifications: list[Notification] = []

    for alert in active:
        price = prices.get(alert.symbol)
        if price is None:
            continue

        change_24h = changes.get(alert.symbol, 0.0)

        should_trigger = _check_condition(
            alert.direction, price, change_24h, alert.target_price
        )

        if should_trigger:
            alert.is_triggered = True
            alert.triggered_at = datetime.now(timezone.utc)
            triggered_count += 1

            existing = (
                db.query(Notification)
                .filter(
                    Notification.related_alert_id == alert.id,
                    Notification.type == "price_alert_triggered",
                )
                .first()
            )
            if existing is None:
                new_notifications.append(
                    Notification(
                        user_id=alert.user_id,
                        type="price_alert_triggered",
                        title="Alert Triggered",
                        message=_notification_message(
                            alert.direction, alert.symbol, alert.target_price
                        ),
                        related_alert_id=alert.id,
                    )
                )

    if triggered_count > 0:
        for n in new_notifications:
            db.add(n)
        db.commit()

    return triggered_count
