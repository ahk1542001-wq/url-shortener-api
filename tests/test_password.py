def test_shorten_without_password_when_set(client, monkeypatch):
    monkeypatch.setattr("config.ACCESS_PASSWORD", "secret123")
    r = client.post("/api/shorten", json={"url": "https://example.com"})
    assert r.status_code == 401
    assert "password" in r.json()["error"]["message"].lower()


def test_shorten_with_wrong_password(client, monkeypatch):
    monkeypatch.setattr("config.ACCESS_PASSWORD", "secret123")
    r = client.post(
        "/api/shorten",
        json={"url": "https://example.com"},
        headers={"X-Access-Password": "wrong"},
    )
    assert r.status_code == 401


def test_shorten_with_correct_password(client, monkeypatch):
    monkeypatch.setattr("config.ACCESS_PASSWORD", "secret123")
    r = client.post(
        "/api/shorten",
        json={"url": "https://example.com"},
        headers={"X-Access-Password": "secret123"},
    )
    assert r.status_code == 201


def test_delete_without_password_when_set(client, monkeypatch):
    monkeypatch.setattr("config.ACCESS_PASSWORD", "secret123")
    r = client.delete("/api/links/somecode")
    assert r.status_code == 401


def test_get_links_protected(client, monkeypatch):
    monkeypatch.setattr("config.ACCESS_PASSWORD", "secret123")
    r = client.get("/api/links")
    assert r.status_code == 401


def test_redirect_not_protected(client, monkeypatch):
    monkeypatch.setattr("config.ACCESS_PASSWORD", "secret123")
    r = client.get("/nonexistent", follow_redirects=False)
    assert r.status_code == 404


def test_no_password_allows_access(client, monkeypatch):
    monkeypatch.setattr("config.ACCESS_PASSWORD", "")
    r = client.post("/api/shorten", json={"url": "https://example.com"})
    assert r.status_code == 201
