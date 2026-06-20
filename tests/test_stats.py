def test_stats_valid_code_returns_analytics(client):
    client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "stat"},
    )
    r = client.get("/api/stats/stat")
    assert r.status_code == 200
    data = r.json()
    assert data["short_code"] == "stat"
    assert data["original_url"] == "https://example.com"
    assert data["click_count"] == 0


def test_stats_unknown_code_returns_404(client):
    r = client.get("/api/stats/unknown")
    assert r.status_code == 404
    assert "error" in r.json()


def test_stats_after_redirect_shows_clicks(client):
    client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "cnt"},
    )
    client.get("/cnt", follow_redirects=False)

    r = client.get("/api/stats/cnt")
    assert r.json()["click_count"] == 1


def test_stats_never_accessed_shows_never(client):
    client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "fresh"},
    )
    r = client.get("/api/stats/fresh")
    assert r.json()["last_accessed"] == "Never"
