def test_redirect_valid_code_returns_302(client):
    r = client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "redir"},
    )
    assert r.status_code == 201

    r = client.get("/redir", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com"


def test_redirect_unknown_code_returns_404(client):
    r = client.get("/nonexistent", follow_redirects=False)
    assert r.status_code == 404
    assert "error" in r.json()


def test_redirect_increments_click_count(client):
    client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "clicks"},
    )
    client.get("/clicks", follow_redirects=False)
    client.get("/clicks", follow_redirects=False)

    r = client.get("/api/stats/clicks")
    assert r.json()["click_count"] == 2


def test_redirect_returns_correct_location(client):
    client.post(
        "/api/shorten",
        json={"url": "https://example.com/path?q=1", "custom_code": "loc"},
    )
    r = client.get("/loc", follow_redirects=False)
    assert r.headers["location"] == "https://example.com/path?q=1"
