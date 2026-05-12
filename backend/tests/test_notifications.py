from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.services.alerts import evaluate_alerts
from app.services.notifications import create_notification

client = TestClient(app)

# ── helpers ──────────────────────────────────────────────────────────


def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _register(email: str, password: str = "Test1234!") -> str:
    client.post("/api/auth/register", json={"email": email, "password": password})
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── tests ────────────────────────────────────────────────────────────


def test_get_notifications_empty():
    _reset_db()
    token = _register("notif1@test.com")
    resp = client.get("/api/notifications", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_list_notifications():
    _reset_db()
    token = _register("notif2@test.com")
    db = SessionLocal()
    try:
        create_notification(db, 1, "info", "Title A", "Message A")
        create_notification(db, 1, "info", "Title B", "Message B")
    finally:
        db.close()

    resp = client.get("/api/notifications", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["title"] == "Title B"
    assert data[1]["title"] == "Title A"


def test_notifications_pagination():
    _reset_db()
    token = _register("notif3@test.com")
    db = SessionLocal()
    try:
        for i in range(5):
            create_notification(db, 1, "info", f"Title {i}", f"Msg {i}")
    finally:
        db.close()

    resp = client.get("/api/notifications?limit=2&offset=0", headers=_auth(token))
    assert len(resp.json()) == 2

    resp2 = client.get("/api/notifications?limit=2&offset=2", headers=_auth(token))
    assert len(resp2.json()) == 2

    resp3 = client.get("/api/notifications?limit=2&offset=4", headers=_auth(token))
    assert len(resp3.json()) == 1


def test_mark_notification_as_read():
    _reset_db()
    token = _register("notif4@test.com")
    db = SessionLocal()
    try:
        n = create_notification(db, 1, "info", "Title", "Msg")
        nid = n.id
    finally:
        db.close()

    resp = client.post(f"/api/notifications/{nid}/read", headers=_auth(token))
    assert resp.status_code == 200
    assert "read" in resp.json()["detail"]

    listing = client.get("/api/notifications", headers=_auth(token)).json()
    assert listing[0]["is_read"] is True


def test_mark_nonexistent_notification_returns_404():
    _reset_db()
    token = _register("notif5@test.com")
    resp = client.post("/api/notifications/9999/read", headers=_auth(token))
    assert resp.status_code == 404


def test_mark_all_as_read():
    _reset_db()
    token = _register("notif6@test.com")
    db = SessionLocal()
    try:
        create_notification(db, 1, "info", "T1", "M1")
        create_notification(db, 1, "info", "T2", "M2")
        create_notification(db, 1, "info", "T3", "M3")
    finally:
        db.close()

    resp = client.post("/api/notifications/read-all", headers=_auth(token))
    assert resp.status_code == 200
    assert "3" in resp.json()["detail"]

    listing = client.get("/api/notifications", headers=_auth(token)).json()
    assert all(n["is_read"] for n in listing)


def test_unread_count():
    _reset_db()
    token = _register("notif7@test.com")
    db = SessionLocal()
    try:
        create_notification(db, 1, "info", "T1", "M1")
        create_notification(db, 1, "info", "T2", "M2")
    finally:
        db.close()

    resp = client.get("/api/notifications/unread-count", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 2

    db = SessionLocal()
    try:
        from app.services.notifications import mark_all_notifications_as_read
        mark_all_notifications_as_read(db, 1)
    finally:
        db.close()

    resp2 = client.get("/api/notifications/unread-count", headers=_auth(token))
    assert resp2.json()["unread_count"] == 0


def test_user_isolation():
    _reset_db()
    token_a = _register("notif_a@test.com")
    token_b = _register("notif_b@test.com")

    db = SessionLocal()
    try:
        create_notification(db, 1, "info", "User A notif", "For A")
        create_notification(db, 2, "info", "User B notif", "For B")
    finally:
        db.close()

    list_a = client.get("/api/notifications", headers=_auth(token_a)).json()
    list_b = client.get("/api/notifications", headers=_auth(token_b)).json()

    assert len(list_a) == 1
    assert list_a[0]["title"] == "User A notif"
    assert len(list_b) == 1
    assert list_b[0]["title"] == "User B notif"

    # user B cannot mark user A's notification as read
    notif_a_id = list_a[0]["id"]
    resp = client.post(f"/api/notifications/{notif_a_id}/read", headers=_auth(token_b))
    assert resp.status_code == 404


def test_unauthenticated_requests_rejected():
    resp_get = client.get("/api/notifications")
    resp_count = client.get("/api/notifications/unread-count")
    resp_read = client.post("/api/notifications/1/read")
    resp_read_all = client.post("/api/notifications/read-all")
    assert resp_get.status_code == 403
    assert resp_count.status_code == 403
    assert resp_read.status_code == 403
    assert resp_read_all.status_code == 403


def test_alert_trigger_creates_notification():
    _reset_db()
    token = _register("trigger_notif@test.com")
    client.post(
        "/api/alerts",
        json={"symbol": "BTC", "target_price": 70000, "direction": "price_above"},
        headers=_auth(token),
    )

    db = SessionLocal()
    try:
        triggered = evaluate_alerts(db, {"BTC": 75000.0})
        assert triggered == 1
    finally:
        db.close()

    notifs = client.get("/api/notifications", headers=_auth(token)).json()
    assert len(notifs) == 1
    assert notifs[0]["type"] == "price_alert_triggered"
    assert notifs[0]["title"] == "Alert Triggered"
    assert "BTC" in notifs[0]["message"]
    assert "crossed above" in notifs[0]["message"]
    assert notifs[0]["related_alert_id"] is not None


def test_alert_trigger_below_creates_notification():
    _reset_db()
    token = _register("trigger_below@test.com")
    client.post(
        "/api/alerts",
        json={"symbol": "ETH", "target_price": 3000, "direction": "price_below"},
        headers=_auth(token),
    )

    db = SessionLocal()
    try:
        evaluate_alerts(db, {"ETH": 2500.0})
    finally:
        db.close()

    notifs = client.get("/api/notifications", headers=_auth(token)).json()
    assert len(notifs) == 1
    assert "dropped below" in notifs[0]["message"]


def test_no_duplicate_notification_on_repeated_trigger():
    _reset_db()
    token = _register("dup_notif@test.com")
    client.post(
        "/api/alerts",
        json={"symbol": "BTC", "target_price": 70000, "direction": "price_above"},
        headers=_auth(token),
    )

    db = SessionLocal()
    try:
        evaluate_alerts(db, {"BTC": 75000.0})
        evaluate_alerts(db, {"BTC": 80000.0})
    finally:
        db.close()

    notifs = client.get("/api/notifications", headers=_auth(token)).json()
    assert len(notifs) == 1
