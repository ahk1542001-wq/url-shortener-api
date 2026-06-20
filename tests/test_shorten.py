def test_shorten_valid_url_returns_201(client):
    r = client.post("/api/shorten", json={"url": "https://example.com"})
    assert r.status_code == 201
    data = r.json()
    assert "short_code" in data
    assert data["original_url"] == "https://example.com"


def test_shorten_with_custom_code_returns_201(client):
    r = client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "my-link"},
    )
    assert r.status_code == 201
    assert r.json()["short_code"] == "my-link"


def test_shorten_missing_scheme_returns_422(client):
    r = client.post("/api/shorten", json={"url": "not-a-url"})
    assert r.status_code == 422
    assert "error" in r.json()


def test_shorten_empty_url_returns_422(client):
    r = client.post("/api/shorten", json={"url": ""})
    assert r.status_code == 422


def test_shorten_reserved_code_returns_422(client):
    r = client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "api"},
    )
    assert r.status_code == 422
    assert "reserved" in r.json()["error"]["message"].lower()


def test_shorten_duplicate_code_returns_409(client):
    client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "taken"},
    )
    r = client.post(
        "/api/shorten",
        json={"url": "https://other.com", "custom_code": "taken"},
    )
    assert r.status_code == 409


def test_shorten_code_too_short_returns_422(client):
    r = client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "ab"},
    )
    assert r.status_code == 422
    assert "3-20" in r.json()["error"]["message"]


def test_shorten_code_too_long_returns_422(client):
    r = client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "a" * 21},
    )
    assert r.status_code == 422
    assert "3-20" in r.json()["error"]["message"]


def test_shorten_code_special_chars_returns_422(client):
    r = client.post(
        "/api/shorten",
        json={"url": "https://example.com", "custom_code": "my code!"},
    )
    assert r.status_code == 422
    assert "letters, numbers" in r.json()["error"]["message"]


def test_shorten_url_too_long_returns_422(client):
    r = client.post(
        "/api/shorten",
        json={"url": "https://example.com/" + "x" * 2100},
    )
    assert r.status_code == 422
    assert "2048" in r.json()["error"]["message"]


def test_shorten_returns_structured_error_format(client):
    r = client.post("/api/shorten", json={"url": "bad"})
    body = r.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
