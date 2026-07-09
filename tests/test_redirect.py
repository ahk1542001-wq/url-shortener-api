def test_redirect_valid_code_returns_302(auth_client):
    r = auth_client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "redir"},
    )
    assert r.status_code == 201

    r = auth_client.get("/redir", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com"


def test_redirect_unknown_code_returns_404(auth_client):
    r = auth_client.get("/nonexistent", follow_redirects=False)
    assert r.status_code == 404
    assert "error" in r.json()


def test_redirect_increments_click_count(auth_client):
    auth_client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "clicks"},
    )
    auth_client.get("/clicks", follow_redirects=False)
    auth_client.get("/clicks", follow_redirects=False)
    
    from src.main import analytics_buffer
    from src.database import get_db
    from datetime import datetime, timezone
    to_flush = dict(analytics_buffer)
    analytics_buffer.clear()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with get_db() as conn:
        for code, count in to_flush.items():
            conn.execute("UPDATE urls SET click_count = click_count + ?, last_accessed = ? WHERE short_code = ?", (count, today, code))
        conn.commit()

    r = auth_client.get("/api/stats/clicks")
    assert r.json()["click_count"] == 2


def test_redirect_returns_correct_location(auth_client):
    auth_client.post(
        "/api/shorten",
        json={"url": "https://example.com/path?q=1", "custom_code": "loc"},
    )
    r = auth_client.get("/loc", follow_redirects=False)
    assert r.headers["location"] == "https://example.com/path?q=1"
