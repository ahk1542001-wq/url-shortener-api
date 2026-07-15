def test_admin_users_list_unauthorized(client):
    r = client.get("/api/admin/users")
    assert r.status_code == 401


def test_admin_users_list_authorized(auth_client):
    r = auth_client.get("/api/admin/users")
    assert r.status_code == 200
    assert "users" in r.json()


def test_create_user_unauthorized(client):
    r = client.post(
        "/api/admin/users", json={"username": "newuser", "password": "password"}
    )
    assert r.status_code == 401


def test_create_user_authorized(auth_client):
    r = auth_client.post(
        "/api/admin/users", json={"username": "newuser", "password": "password"}
    )
    assert r.status_code == 201
    assert r.json()["username"] == "newuser"


def test_admin_access_denied_for_normal_user(auth_client, client):
    # Create a normal user token
    auth_client.post(
        "/api/admin/users", json={"username": "normal_test", "password": "password"}
    )

    r = client.post(
        "/api/login", json={"username": "normal_test", "password": "password"}
    )
    token = r.json()["token"]

    client.headers.update({"Authorization": f"Bearer {token}"})

    r2 = client.get("/api/admin/users")
    assert r2.status_code == 403
