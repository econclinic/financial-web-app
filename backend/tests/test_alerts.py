from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.services.alerts import evaluate_alerts

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


def test_get_alerts_empty():
    _reset_db()
    token = _register("alert1@test.com")
    resp = client.get("/api/alerts", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_alert():
    _reset_db()
    token = _register("alert2@test.com")
    resp = client.post(
        "/api/alerts",
        json={"symbol": "btc", "target_price": 100000, "direction": "above"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["symbol"] == "BTC"
    assert data["target_price"] == 100000
    assert data["direction"] == "above"
    assert data["is_triggered"] is False
    assert data["triggered_at"] is None


def test_duplicate_active_alert_returns_409():
    _reset_db()
    token = _register("alert3@test.com")
    payload = {"symbol": "ETH", "target_price": 5000, "direction": "above"}
    client.post("/api/alerts", json=payload, headers=_auth(token))
    resp = client.post("/api/alerts", json=payload, headers=_auth(token))
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


def test_delete_alert():
    _reset_db()
    token = _register("alert4@test.com")
    create_resp = client.post(
        "/api/alerts",
        json={"symbol": "BTC", "target_price": 50000, "direction": "below"},
        headers=_auth(token),
    )
    alert_id = create_resp.json()["id"]

    resp = client.delete(f"/api/alerts/{alert_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert "deleted" in resp.json()["detail"]

    listing = client.get("/api/alerts", headers=_auth(token))
    assert listing.json() == []


def test_delete_nonexistent_alert_returns_404():
    _reset_db()
    token = _register("alert5@test.com")
    resp = client.delete("/api/alerts/9999", headers=_auth(token))
    assert resp.status_code == 404


def test_unauthenticated_requests_rejected():
    resp_get = client.get("/api/alerts")
    resp_post = client.post(
        "/api/alerts",
        json={"symbol": "BTC", "target_price": 100000, "direction": "above"},
    )
    resp_del = client.delete("/api/alerts/1")
    assert resp_get.status_code == 403
    assert resp_post.status_code == 403
    assert resp_del.status_code == 403


def test_user_isolation():
    _reset_db()
    token_a = _register("user_a_alert@test.com")
    token_b = _register("user_b_alert@test.com")

    resp_a = client.post(
        "/api/alerts",
        json={"symbol": "BTC", "target_price": 100000, "direction": "above"},
        headers=_auth(token_a),
    )
    client.post(
        "/api/alerts",
        json={"symbol": "ETH", "target_price": 1000, "direction": "below"},
        headers=_auth(token_b),
    )

    list_a = client.get("/api/alerts", headers=_auth(token_a)).json()
    list_b = client.get("/api/alerts", headers=_auth(token_b)).json()

    assert len(list_a) == 1
    assert list_a[0]["symbol"] == "BTC"
    assert len(list_b) == 1
    assert list_b[0]["symbol"] == "ETH"

    # user B cannot delete user A's alert
    alert_a_id = resp_a.json()["id"]
    resp = client.delete(f"/api/alerts/{alert_a_id}", headers=_auth(token_b))
    assert resp.status_code == 404


def test_trigger_logic_above():
    """Alert with direction=above triggers when price >= target."""
    _reset_db()
    token = _register("trigger1@test.com")
    client.post(
        "/api/alerts",
        json={"symbol": "BTC", "target_price": 70000, "direction": "above"},
        headers=_auth(token),
    )

    db = SessionLocal()
    try:
        triggered = evaluate_alerts(db, {"BTC": 75000.0})
        assert triggered == 1
    finally:
        db.close()

    alerts = client.get("/api/alerts", headers=_auth(token)).json()
    assert alerts[0]["is_triggered"] is True
    assert alerts[0]["triggered_at"] is not None


def test_trigger_logic_below():
    """Alert with direction=below triggers when price <= target."""
    _reset_db()
    token = _register("trigger2@test.com")
    client.post(
        "/api/alerts",
        json={"symbol": "ETH", "target_price": 3000, "direction": "below"},
        headers=_auth(token),
    )

    db = SessionLocal()
    try:
        triggered = evaluate_alerts(db, {"ETH": 2500.0})
        assert triggered == 1
    finally:
        db.close()

    alerts = client.get("/api/alerts", headers=_auth(token)).json()
    assert alerts[0]["is_triggered"] is True


def test_trigger_does_not_fire_when_condition_not_met():
    """Alert stays active when price doesn't meet threshold."""
    _reset_db()
    token = _register("trigger3@test.com")
    client.post(
        "/api/alerts",
        json={"symbol": "BTC", "target_price": 100000, "direction": "above"},
        headers=_auth(token),
    )

    db = SessionLocal()
    try:
        triggered = evaluate_alerts(db, {"BTC": 80000.0})
        assert triggered == 0
    finally:
        db.close()

    alerts = client.get("/api/alerts", headers=_auth(token)).json()
    assert alerts[0]["is_triggered"] is False


def test_triggered_alert_does_not_fire_again():
    """Once triggered, alert should not fire again."""
    _reset_db()
    token = _register("trigger4@test.com")
    client.post(
        "/api/alerts",
        json={"symbol": "BTC", "target_price": 70000, "direction": "above"},
        headers=_auth(token),
    )

    db = SessionLocal()
    try:
        evaluate_alerts(db, {"BTC": 75000.0})
        triggered_again = evaluate_alerts(db, {"BTC": 80000.0})
        assert triggered_again == 0
    finally:
        db.close()
