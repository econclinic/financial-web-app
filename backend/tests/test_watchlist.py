from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app

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

def test_get_watchlist_empty():
    _reset_db()
    token = _register("wl1@test.com")
    resp = client.get("/api/watchlist", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_add_symbol():
    _reset_db()
    token = _register("wl2@test.com")
    resp = client.post("/api/watchlist", json={"symbol": "btc"}, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["symbol"] == "BTC"
    assert data["user_id"] is not None

    listing = client.get("/api/watchlist", headers=_auth(token))
    assert len(listing.json()) == 1
    assert listing.json()[0]["symbol"] == "BTC"


def test_duplicate_symbol_returns_409():
    _reset_db()
    token = _register("wl3@test.com")
    client.post("/api/watchlist", json={"symbol": "ETH"}, headers=_auth(token))
    resp = client.post("/api/watchlist", json={"symbol": "eth"}, headers=_auth(token))
    assert resp.status_code == 409
    assert "already in your watchlist" in resp.json()["detail"]


def test_delete_symbol():
    _reset_db()
    token = _register("wl4@test.com")
    client.post("/api/watchlist", json={"symbol": "BTC"}, headers=_auth(token))

    resp = client.delete("/api/watchlist/BTC", headers=_auth(token))
    assert resp.status_code == 200
    assert "removed" in resp.json()["detail"]

    listing = client.get("/api/watchlist", headers=_auth(token))
    assert listing.json() == []


def test_delete_missing_symbol_returns_404():
    _reset_db()
    token = _register("wl5@test.com")
    resp = client.delete("/api/watchlist/DOGE", headers=_auth(token))
    assert resp.status_code == 404


def test_unauthenticated_requests_rejected():
    resp_get = client.get("/api/watchlist")
    resp_post = client.post("/api/watchlist", json={"symbol": "BTC"})
    resp_del = client.delete("/api/watchlist/BTC")
    assert resp_get.status_code == 403
    assert resp_post.status_code == 403
    assert resp_del.status_code == 403


def test_user_isolation():
    _reset_db()
    token_a = _register("user_a@test.com")
    token_b = _register("user_b@test.com")

    client.post("/api/watchlist", json={"symbol": "BTC"}, headers=_auth(token_a))
    client.post("/api/watchlist", json={"symbol": "ETH"}, headers=_auth(token_b))

    list_a = client.get("/api/watchlist", headers=_auth(token_a)).json()
    list_b = client.get("/api/watchlist", headers=_auth(token_b)).json()

    assert len(list_a) == 1
    assert list_a[0]["symbol"] == "BTC"
    assert len(list_b) == 1
    assert list_b[0]["symbol"] == "ETH"

    # user B cannot delete user A's symbol
    resp = client.delete("/api/watchlist/BTC", headers=_auth(token_b))
    assert resp.status_code == 404

    # user A's watchlist unchanged
    list_a_after = client.get("/api/watchlist", headers=_auth(token_a)).json()
    assert len(list_a_after) == 1
