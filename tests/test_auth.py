def test_login_success(client):
    r = client.post("/api/login", json={"username": "admin", "password": "testpass"})
    assert r.status_code == 200
    assert "token" in r.json()


def test_login_failure(client):
    r = client.post(
        "/api/login", json={"username": "admin", "password": "wrongpassword"}
    )
    assert r.status_code == 401
    assert "error" in r.json()


def test_unauthorized_access(client):
    r = client.get("/api/links")
    assert r.status_code == 401


def test_authorized_access(auth_client):
    r = auth_client.get("/api/links")
    assert r.status_code == 200
