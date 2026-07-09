def test_stats_valid_code_returns_analytics(auth_client):
    auth_client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "stat"},
    )
    r = auth_client.get("/api/stats/stat")
    assert r.status_code == 200
    data = r.json()
    assert data["short_code"] == "stat"
    assert data["original_url"] == "https://example.com"
    assert data["click_count"] == 0


def test_stats_unknown_code_returns_404(auth_client):
    r = auth_client.get("/api/stats/unknown")
    assert r.status_code == 404
    assert "error" in r.json()


def test_stats_after_redirect_shows_clicks(auth_client):
    auth_client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "cnt"},
    )
    auth_client.get("/cnt", follow_redirects=False)
    
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

    r = auth_client.get("/api/stats/cnt")
    assert r.json()["click_count"] == 1


def test_stats_never_accessed_shows_never(auth_client):
    auth_client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "fresh"},
    )
    r = auth_client.get("/api/stats/fresh")
    assert r.json()["last_accessed"] == "Never"
