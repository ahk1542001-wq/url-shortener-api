import sqlite3

from src.database import get_db, init_db


def _create_managed_user(auth_client, username="manageduser", password="oldpass"):
    response = auth_client.post(
        "/api/admin/users", json={"username": username, "password": password}
    )
    assert response.status_code == 201
    users = auth_client.get("/api/admin/users").json()["users"]
    return next(user for user in users if user["username"] == username)


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


def test_admin_user_detail_returns_owned_data_summary(auth_client):
    managed_user = _create_managed_user(auth_client)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO profiles (user_id, username, bio, tree_views) VALUES (?, ?, ?, ?)",
            (managed_user["id"], "managed-profile", "Managed profile", 7),
        )
        profile_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO links (user_id, profile_id, short_code, original_url, click_count) VALUES (?, ?, ?, ?, ?)",
            (
                managed_user["id"],
                profile_id,
                "managed-link",
                "https://example.com",
                4,
            ),
        )

    response = auth_client.get(f"/api/admin/users/{managed_user['id']}")
    assert response.status_code == 200
    detail = response.json()["user"]
    assert detail["profile_count"] == 1
    assert detail["link_count"] == 1
    assert detail["total_clicks"] == 4
    assert detail["profiles"][0]["tree_views"] == 7


def test_admin_can_rename_reset_password_and_disable_user(auth_client, client):
    managed_user = _create_managed_user(auth_client)
    admin_authorization = auth_client.headers["Authorization"]

    login = client.post(
        "/api/login", json={"username": "manageduser", "password": "oldpass"}
    )
    assert login.status_code == 200
    old_token = login.json()["token"]

    update = auth_client.patch(
        f"/api/admin/users/{managed_user['id']}",
        json={
            "username": "renamed-user",
            "password": "newpass",
            "is_active": False,
        },
    )
    assert update.status_code == 200
    assert update.json()["user"]["username"] == "renamed-user"
    assert update.json()["user"]["is_active"] is False

    client.headers.update({"Authorization": f"Bearer {old_token}"})
    assert client.get("/api/profiles").status_code == 401

    client.headers.update({"Authorization": admin_authorization})
    enable = auth_client.patch(
        f"/api/admin/users/{managed_user['id']}", json={"is_active": True}
    )
    assert enable.status_code == 200

    client.headers.pop("Authorization", None)
    assert (
        client.post(
            "/api/login", json={"username": "manageduser", "password": "oldpass"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/login", json={"username": "renamed-user", "password": "newpass"}
        ).status_code
        == 200
    )


def test_admin_delete_user_removes_owned_data(auth_client):
    managed_user = _create_managed_user(auth_client)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO profiles (user_id, username) VALUES (?, ?)",
            (managed_user["id"], "delete-profile"),
        )
        profile_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO links (user_id, profile_id, short_code, original_url) VALUES (?, ?, ?, ?)",
            (
                managed_user["id"],
                profile_id,
                "delete-link",
                "https://example.com",
            ),
        )
        link_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO daily_stats (link_id, date, clicks) VALUES (?, ?, ?)",
            (link_id, "2026-07-16", 2),
        )

    response = auth_client.delete(f"/api/admin/users/{managed_user['id']}")
    assert response.status_code == 200

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE id = ?", (managed_user["id"],))
        assert cursor.fetchone()[0] == 0
        cursor.execute(
            "SELECT COUNT(*) FROM profiles WHERE user_id = ?", (managed_user["id"],)
        )
        assert cursor.fetchone()[0] == 0
        cursor.execute(
            "SELECT COUNT(*) FROM links WHERE user_id = ?", (managed_user["id"],)
        )
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT COUNT(*) FROM daily_stats WHERE link_id = ?", (link_id,))
        assert cursor.fetchone()[0] == 0


def test_admin_account_cannot_be_edited_or_deleted(auth_client):
    admin_user = next(
        user
        for user in auth_client.get("/api/admin/users").json()["users"]
        if user["is_admin"]
    )
    assert (
        auth_client.patch(
            f"/api/admin/users/{admin_user['id']}", json={"is_active": False}
        ).status_code
        == 400
    )
    assert auth_client.delete(f"/api/admin/users/{admin_user['id']}").status_code == 400


def test_users_schema_records_account_status_migration():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        assert "is_active" in {row[1] for row in cursor.fetchall()}
        cursor.execute("SELECT version FROM schema_versions WHERE version = 2")
        assert cursor.fetchone()[0] == 2


def test_init_db_upgrades_legacy_users_before_admin_upsert(tmp_path):
    database_path = tmp_path / "legacy-users.db"
    with sqlite3.connect(database_path) as conn:
        conn.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            ("admin", "legacy-hash"),
        )

    init_db(str(database_path))

    with sqlite3.connect(database_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        assert "is_active" in columns
        admin = conn.execute(
            "SELECT is_active FROM users WHERE username = ?", ("admin",)
        ).fetchone()
        assert admin == (1,)
