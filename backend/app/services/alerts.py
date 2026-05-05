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


def evaluate_alerts(db: Session, prices: dict[str, float]) -> int:
    """Check all active alerts against current prices.

    Returns the number of newly triggered alerts.
    """
    active = db.query(Alert).filter(Alert.is_triggered.is_(False)).all()
    triggered_count = 0
    new_notifications: list[Notification] = []

    for alert in active:
        price = prices.get(alert.symbol)
        if price is None:
            continue

        should_trigger = (
            (alert.direction == "above" and price >= alert.target_price)
            or (alert.direction == "below" and price <= alert.target_price)
        )

        if should_trigger:
            alert.is_triggered = True
            alert.triggered_at = datetime.now(timezone.utc)
            triggered_count += 1

            verb = "crossed above" if alert.direction == "above" else "dropped below"
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
                        message=f"{alert.symbol} {verb} {alert.target_price:g}",
                        related_alert_id=alert.id,
                    )
                )

    if triggered_count > 0:
        for n in new_notifications:
            db.add(n)
        db.commit()

    return triggered_count
