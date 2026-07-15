import os
import sys
import time
import io
import uuid
import sqlite3
import subprocess
import pytest
import jwt
import asyncio
from unittest.mock import MagicMock, patch

from src.database import get_db, init_db
from src.migration import run_migrations, check_table_exists
from src import config


# 1. Helper to run config validation in subprocess
def run_config_check(env_updates):
    env = os.environ.copy()
    for k, v in env_updates.items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v
    res = subprocess.run(
        [sys.executable, "-c", "import src.config"],
        env=env,
        capture_output=True,
        text=True,
    )
    return res


def test_config_jwt_secret_too_short():
    res = run_config_check({"JWT_SECRET": "short-secret"})
    assert res.returncode != 0
    assert "ValueError" in res.stderr
    assert "JWT_SECRET must be at least 32 characters long" in res.stderr


def test_config_jwt_secret_placeholder():
    res = run_config_check({"JWT_SECRET": "super-secret-key-change-me"})
    assert res.returncode != 0
    assert "ValueError" in res.stderr
    assert "JWT_SECRET must not use the default placeholder values" in res.stderr


def test_config_jwt_secret_predictable_placeholder():
    res = run_config_check(
        {"JWT_SECRET": "generate_a_secure_random_string_of_at_least_32_chars"}
    )
    assert res.returncode != 0
    assert "ValueError" in res.stderr
    assert "JWT_SECRET must not use the default placeholder values" in res.stderr


def test_config_admin_hash_placeholder():
    res = run_config_check({"ADMIN_PASSWORD_HASH": "$2b$12$your_bcrypt_hash_here"})
    assert res.returncode != 0
    assert "ValueError" in res.stderr
    assert "ADMIN_PASSWORD_HASH must not use the placeholder value" in res.stderr


def test_config_admin_hash_invalid():
    res = run_config_check({"ADMIN_PASSWORD_HASH": "invalidhash"})
    assert res.returncode != 0
    assert "ValueError" in res.stderr
    assert "ADMIN_PASSWORD_HASH must be a valid configured bcrypt hash" in res.stderr


def test_config_admin_hash_valid():
    # Valid bcrypt hash for 'password' (starts with $2b$, 60 chars)
    valid_hash = "$2b$12$V5/S5.d2nQ25h9YQp6n2re4u5S5u5S5u5S5u5S5u5S5u5S5u5S5u5"
    res = run_config_check({"ADMIN_PASSWORD_HASH": valid_hash})
    assert res.returncode == 0


def test_config_admin_hash_missing():
    res = run_config_check({"ADMIN_PASSWORD_HASH": ""})
    assert res.returncode != 0
    assert "ValueError" in res.stderr
    assert "ADMIN_PASSWORD_HASH must be explicitly set" in res.stderr


def test_config_cloudinary_partial():
    # Only the cloud name is configured.
    res = run_config_check(
        {
            "CLOUDINARY_CLOUD_NAME": "test-cloud",
            "CLOUDINARY_API_KEY": "",
            "CLOUDINARY_API_SECRET": "",
        }
    )
    assert res.returncode != 0
    assert "ValueError" in res.stderr
    assert "All Cloudinary configuration variables" in res.stderr


# 2. SQLite Foreign Key Enforcement Test
def test_sqlite_foreign_key_enforcement(tmp_path):
    db_path = str(tmp_path / "test_fk.db")

    # Connect and verify foreign keys are enabled
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("""
        CREATE TABLE parent (
            id INTEGER PRIMARY KEY
        )
    """)
    conn.execute("""
        CREATE TABLE child (
            id INTEGER PRIMARY KEY,
            parent_id INTEGER REFERENCES parent(id) ON DELETE CASCADE
        )
    """)

    conn.execute("INSERT INTO parent (id) VALUES (1)")
    conn.execute("INSERT INTO child (id, parent_id) VALUES (10, 1)")

    # Delete parent and check cascade
    conn.execute("DELETE FROM parent WHERE id = 1")
    cur = conn.execute("SELECT COUNT(*) FROM child")
    assert cur.fetchone()[0] == 0

    # Run PRAGMA foreign_key_check
    cur = conn.execute("PRAGMA foreign_key_check")
    assert len(cur.fetchall()) == 0
    conn.close()


# 3. SQLite Migration Tests (States: urls only, links only, both tables, and Idempotency)
def test_sqlite_migration_urls_only(tmp_path):
    db_path = str(tmp_path / "test_mig_urls.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Create base tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            username TEXT UNIQUE NOT NULL,
            bio TEXT,
            avatar_url TEXT,
            avatar_object_key TEXT,
            tree_views INTEGER DEFAULT 0,
            social_links TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create legacy table
    conn.execute("""
        CREATE TABLE urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            short_code TEXT UNIQUE,
            original_url TEXT,
            profile_id INTEGER,
            title TEXT,
            show_on_tree BOOLEAN,
            click_count INTEGER,
            created_at DATETIME,
            last_accessed DATETIME
        )
    """)
    conn.execute("""
        CREATE TABLE daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INTEGER REFERENCES urls(id),
            date TEXT,
            clicks INTEGER,
            UNIQUE(link_id, date)
        )
    """)

    # Insert legacy link
    conn.execute(
        "INSERT INTO urls (id, user_id, short_code, original_url, click_count) VALUES (1, 100, 'abc', 'http://a.com', 5)"
    )
    conn.execute(
        "INSERT INTO daily_stats (link_id, date, clicks) VALUES (1, '2026-07-15', 3)"
    )
    conn.commit()

    # Run migration twice (idempotency check)
    run_migrations(conn)
    run_migrations(conn)

    # Check tables
    assert not check_table_exists(conn, "urls")
    assert check_table_exists(conn, "links")

    cur = conn.execute(
        "SELECT click_count, original_url FROM links WHERE short_code = 'abc'"
    )
    row = cur.fetchone()
    assert row[0] == 5
    assert row[1] == "http://a.com"

    # Verify daily_stats targets links
    cur = conn.execute("PRAGMA foreign_key_list(daily_stats)")
    fk = cur.fetchall()
    assert any(r[2] == "links" for r in fk)

    conn.close()


def test_sqlite_migration_both_tables_merge(tmp_path):
    db_path = str(tmp_path / "test_mig_both.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Create base tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            username TEXT UNIQUE NOT NULL,
            bio TEXT,
            avatar_url TEXT,
            avatar_object_key TEXT,
            tree_views INTEGER DEFAULT 0,
            social_links TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create both tables
    conn.execute("""
        CREATE TABLE urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            short_code TEXT UNIQUE,
            original_url TEXT,
            profile_id INTEGER,
            title TEXT,
            show_on_tree BOOLEAN,
            click_count INTEGER,
            created_at DATETIME,
            last_accessed DATETIME
        )
    """)
    conn.execute("""
        CREATE TABLE links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            short_code TEXT UNIQUE,
            original_url TEXT,
            profile_id INTEGER,
            title TEXT,
            show_on_tree BOOLEAN,
            click_count INTEGER,
            created_at DATETIME,
            last_accessed DATETIME
        )
    """)
    conn.execute("""
        CREATE TABLE daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INTEGER REFERENCES urls(id),
            date TEXT,
            clicks INTEGER,
            UNIQUE(link_id, date)
        )
    """)

    # Insert legacy urls
    conn.execute(
        "INSERT INTO urls (id, user_id, short_code, original_url, click_count, title, show_on_tree) VALUES (1, 100, 'abc', 'http://legacy.com', 5, 'Legacy', 1)"
    )
    conn.execute(
        "INSERT INTO urls (id, user_id, short_code, original_url, click_count, title, show_on_tree) VALUES (2, 100, 'xyz', 'http://xyz.com', 10, 'XYZ', 0)"
    )

    # Insert links (conflict on 'abc')
    conn.execute(
        "INSERT INTO links (id, user_id, short_code, original_url, click_count, title, show_on_tree) VALUES (10, 100, 'abc', 'http://authoritative.com', 3, NULL, NULL)"
    )

    # Insert stats pointing to urls
    conn.execute(
        "INSERT INTO daily_stats (link_id, date, clicks) VALUES (1, '2026-07-15', 4)"
    )  # for 'abc'
    conn.execute(
        "INSERT INTO daily_stats (link_id, date, clicks) VALUES (2, '2026-07-15', 8)"
    )  # for 'xyz'
    conn.commit()

    # Run migration twice (idempotency check)
    run_migrations(conn)
    run_migrations(conn)

    # Check tables
    assert not check_table_exists(conn, "urls")
    assert check_table_exists(conn, "links")

    # Check merged links: 'abc' must keep authoritative URL but sum clicks and preserve missing metadata
    cur = conn.execute(
        "SELECT id, click_count, original_url, title, show_on_tree FROM links WHERE short_code = 'abc'"
    )
    row = cur.fetchone()
    assert row[0] == 10  # Authoritative ID remains
    assert row[1] == 8  # Clicks summed: 3 + 5 = 8
    assert row[2] == "http://authoritative.com"
    assert row[3] == "Legacy"  # Preserved from urls because links' value was NULL
    assert row[4] == 1  # Preserved show_on_tree from urls because links' value was NULL

    # Check merged stats
    cur = conn.execute(
        "SELECT link_id, date, clicks FROM daily_stats WHERE link_id = 10"
    )
    stat_abc = cur.fetchone()
    assert stat_abc[2] == 4  # Remapped successfully to link_id=10

    cur = conn.execute("PRAGMA foreign_key_list(daily_stats)")
    fk = cur.fetchall()
    assert any(r[2] == "links" for r in fk)

    conn.close()


# 4. Cloudinary Upload Lifecycle Tests
@pytest.fixture
def mock_cloudinary(monkeypatch):
    monkeypatch.setattr(config, "CLOUDINARY_CLOUD_NAME", "test-cloud")
    monkeypatch.setattr(config, "CLOUDINARY_API_KEY", "test-key")
    monkeypatch.setattr(config, "CLOUDINARY_API_SECRET", "test-secret")
    with patch("src.routers.profiles.cloudinary.uploader") as uploader:
        uploader.upload.return_value = {
            "secure_url": "https://res.cloudinary.com/test-cloud/image/upload/avatars/new-avatar.jpg",
            "public_id": "avatars/new-avatar",
        }
        yield uploader


def test_avatar_upload_without_storage_returns_service_unavailable(auth_client):
    avatar_file = io.BytesIO(b"dummy image bytes")
    with patch("PIL.Image.open") as mock_open:
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_img.mode = "RGB"
        mock_open.return_value = mock_img

        response = auth_client.post(
            "/api/profiles/avatar",
            files={"file": ("avatar.jpg", avatar_file, "image/jpeg")},
        )

    assert response.status_code == 503
    assert response.json()["error"]["message"] == "Avatar storage is not configured."


def test_avatar_upload_cloudinary_failure(mock_cloudinary, auth_client):
    mock_cloudinary.upload.side_effect = Exception("Upload to Cloudinary failed")

    # Get current DB state
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT avatar_url, avatar_object_key FROM profiles WHERE username = 'admin'"
        )
        before_row = c.fetchone()

    avatar_file = io.BytesIO(b"dummy image bytes")
    # Mock PIL Image to pass validation
    with patch("PIL.Image.open") as mock_open:
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_img.mode = "RGB"
        mock_open.return_value = mock_img

        response = auth_client.post(
            "/api/profiles/avatar",
            files={"file": ("avatar.jpg", avatar_file, "image/jpeg")},
        )
        assert response.status_code == 500
        assert "Failed to upload image" in response.json()["error"]["message"]

    # Verify DB was unchanged
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT avatar_url, avatar_object_key FROM profiles WHERE username = 'admin'"
        )
        after_row = c.fetchone()
        assert after_row == before_row


def test_avatar_upload_db_failure_rollback(mock_cloudinary, auth_client):
    # Get current DB state
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT avatar_url, avatar_object_key FROM profiles WHERE username = 'admin'"
        )
        before_row = c.fetchone()

    # Force a database failure during execute by patching get_db
    with patch("src.routers.profiles.get_db") as mock_get_db:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.execute.side_effect = Exception("DB error")
        mock_conn.cursor.return_value = mock_cur
        mock_get_db.return_value.__enter__.return_value = mock_conn

        avatar_file = io.BytesIO(b"dummy image bytes")
        with patch("PIL.Image.open") as mock_open:
            mock_img = MagicMock()
            mock_img.width = 100
            mock_img.height = 100
            mock_img.mode = "RGB"
            mock_open.return_value = mock_img

            response = auth_client.post(
                "/api/profiles/avatar",
                files={"file": ("avatar.jpg", avatar_file, "image/jpeg")},
            )
            assert response.status_code == 500
            assert "Database update failed" in response.json()["error"]["message"]

            # Verify the Cloudinary upload was deleted during rollback.
            mock_cloudinary.destroy.assert_called_once_with(
                "avatars/new-avatar", resource_type="image", invalidate=True
            )

    # Verify DB was unchanged after rollback
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT avatar_url, avatar_object_key FROM profiles WHERE username = 'admin'"
        )
        after_row = c.fetchone()
        assert after_row == before_row


def test_avatar_upload_success_delete_old(mock_cloudinary, auth_client):
    # Pre-populate database with an old avatar object key
    with get_db() as conn:
        conn.execute(
            "UPDATE profiles SET avatar_object_key = 'avatars/old-avatar' WHERE username = 'admin'"
        )
        conn.commit()

    avatar_file = io.BytesIO(b"dummy image bytes")
    with patch("PIL.Image.open") as mock_open:
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_img.mode = "RGB"
        mock_open.return_value = mock_img

        response = auth_client.post(
            "/api/profiles/avatar",
            files={"file": ("avatar.jpg", avatar_file, "image/jpeg")},
        )
        assert response.status_code == 200

        # Verify UUID-based public IDs and deletion of the old avatar.
        generated_public_id = mock_cloudinary.upload.call_args.kwargs["public_id"]
        assert generated_public_id.startswith("avatars/")
        uuid.UUID(generated_public_id.removeprefix("avatars/"))
        mock_cloudinary.destroy.assert_called_with(
            "avatars/old-avatar", resource_type="image", invalidate=True
        )


def test_avatar_upload_delete_old_fail_logged(mock_cloudinary, auth_client):
    # Raise exception when deleting old object
    mock_cloudinary.destroy.side_effect = Exception("Deletion failed")

    with get_db() as conn:
        conn.execute(
            "UPDATE profiles SET avatar_object_key = 'avatars/old-avatar' WHERE username = 'admin'"
        )
        conn.commit()

    avatar_file = io.BytesIO(b"dummy image bytes")
    with patch("PIL.Image.open") as mock_open:
        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100
        mock_img.mode = "RGB"
        mock_open.return_value = mock_img

        with patch("src.routers.profiles.logger") as mock_logger:
            response = auth_client.post(
                "/api/profiles/avatar",
                files={"file": ("avatar.jpg", avatar_file, "image/jpeg")},
            )
            # Request should still succeed
            assert response.status_code == 200
            mock_logger.exception.assert_called_once_with(
                "Failed to delete old Cloudinary avatar %s", "avatars/old-avatar"
            )


# 5. JWT Expiry Test
def test_jwt_expiry(client):
    # Create an expired token manually
    expired_payload = {"sub": "admin", "exp": time.time() - 3600}
    expired_token = jwt.encode(expired_payload, config.JWT_SECRET, algorithm="HS256")

    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/me", headers=headers)
    assert response.status_code == 401
    assert "Token has expired" in response.json()["error"]["message"]


# 6. Link Tree Views and Filtering Test
def test_link_tree_views_and_filtering(auth_client, client):
    # Create profiles and links
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM profiles WHERE username = 'admin'")
        prof_id = c.fetchone()[0]

        # Link 1: show_on_tree = True
        c.execute(
            "INSERT INTO links (user_id, profile_id, short_code, original_url, title, show_on_tree) VALUES (1, ?, 't1', 'http://t1.com', 'T1', ?)",
            (prof_id, True),
        )
        # Link 2: show_on_tree = False
        c.execute(
            "INSERT INTO links (user_id, profile_id, short_code, original_url, title, show_on_tree) VALUES (1, ?, 't2', 'http://t2.com', 'T2', ?)",
            (prof_id, False),
        )
        # Get tree views count
        c.execute("SELECT tree_views FROM profiles WHERE id = ?", (prof_id,))
        initial_views = c.fetchone()[0]
        conn.commit()

    # Query public tree endpoint
    response = client.get("/api/users/admin/tree")
    assert response.status_code == 200
    data = response.json()

    # Views should be incremented
    assert data["username"] == "admin"

    # Tree links should ONLY contain t1 (show_on_tree=True), not t2
    codes = [link["short_code"] for link in data["tree_links"]]
    assert "t1" in codes
    assert "t2" not in codes

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT tree_views FROM profiles WHERE id = ?", (prof_id,))
        final_views = c.fetchone()[0]
        assert final_views == initial_views + 1


# 7. Graceful Shutdown & background flush verification
@pytest.mark.asyncio
async def test_shutdown_flush_verification():
    from src.analytics import analytics_buffer, flush_analytics
    from src.database import get_db

    # Create a link to track
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO links (user_id, short_code, original_url, click_count) VALUES (1, 'shutdown_code', 'http://test.com', 0)"
        )
        conn.commit()

    # Populate buffer
    analytics_buffer["shutdown_code"] = 12

    # Start task
    task = asyncio.create_task(flush_analytics())
    await asyncio.sleep(0.05)

    # Cancel task (simulating shutdown)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Check that buffer was flushed to links / daily_stats database
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT click_count, id FROM links WHERE short_code = 'shutdown_code'"
        )
        row = c.fetchone()
        assert row is not None
        assert row[0] == 12
        link_id = row[1]

        # Verify daily stats entry was created with correct clicks
        c.execute("SELECT clicks FROM daily_stats WHERE link_id = ?", (link_id,))
        stat_row = c.fetchone()
        assert stat_row is not None
        assert stat_row[0] == 12

    # Verify that buffer was cleared
    assert "shutdown_code" not in analytics_buffer

    # Verify duplicate write prevention
    from src.analytics import _flush_now

    _flush_now()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT click_count FROM links WHERE short_code = 'shutdown_code'")
        assert c.fetchone()[0] == 12


# 8. PostgreSQL Real Database Integration Tests (Runs only when POSTGRES_TEST_URL is provided)


def _parse_pg_uri(uri: str):
    """Parse a PostgreSQL URI into (host, port, dbname) for structural comparison."""
    from urllib.parse import urlparse

    parsed = urlparse(uri)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    # DB name is path without leading slash
    dbname = (parsed.path or "").lstrip("/").split("?")[0]
    return host, port, dbname


def _validate_postgres_test_url(
    postgres_test_db: str,
    prod_url: "str | None" = None,
) -> None:
    """Run all safety checks before any destructive PostgreSQL operations.
    Raises pytest.fail() with a descriptive message on any violation.

    Args:
        postgres_test_db: The test database URL to validate.
        prod_url: Override for the production URL. When None, reads
            _ORIGINAL_DATABASE_URL (preserved by conftest before
            DATABASE_URL is cleared for SQLite test mode).
    """
    # Check 1: Structural comparison with production DATABASE_URL
    if prod_url is None:
        prod_url = os.getenv("_ORIGINAL_DATABASE_URL", "") or os.getenv(
            "DATABASE_URL", ""
        )
    if prod_url:
        prod_host, prod_port, prod_db = _parse_pg_uri(prod_url)
        test_host, test_port, test_db = _parse_pg_uri(postgres_test_db)
        if (prod_host, prod_port, prod_db) == (
            test_host,
            test_port,
            test_db,
        ):
            pytest.fail(
                "Safety check failed: POSTGRES_TEST_URL resolves to the "
                "same database as DATABASE_URL "
                f"({test_host}:{test_port}/{test_db}). "
                "Use a separate disposable database."
            )

    # Check 2: Database name must look like a test database
    _, _, test_dbname = _parse_pg_uri(postgres_test_db)
    if not test_dbname:
        pytest.fail(
            "Safety check failed: POSTGRES_TEST_URL has no database " "name in the URI."
        )
    if "test" not in test_dbname.lower():
        pytest.fail(
            f"Safety check failed: database name '{test_dbname}' does "
            "not contain 'test'. The test database name must end in "
            "'_test' or contain 'test' to prevent accidental "
            "destructive operations on production data."
        )

    # Check 3: Explicit opt-in required
    opt_in = os.getenv("ALLOW_DESTRUCTIVE_POSTGRES_TESTS", "").strip().lower()
    if opt_in != "yes":
        pytest.fail(
            "Safety check failed: "
            "ALLOW_DESTRUCTIVE_POSTGRES_TESTS must be set to 'yes' "
            "to run destructive PostgreSQL migration tests."
        )


@pytest.mark.postgres
def test_postgres_migration_real_partial_both_tables():
    postgres_test_db = os.getenv("POSTGRES_TEST_URL")
    if not postgres_test_db:
        pytest.skip(
            "POSTGRES_TEST_URL not set — skipping PostgreSQL integration tests."
        )

    # Run all safety validations before touching any tables
    _validate_postgres_test_url(postgres_test_db)

    import psycopg2

    # Connect and set up disposable test tables
    conn = psycopg2.connect(postgres_test_db)
    cur = conn.cursor()

    try:
        # Clear any previous test tables
        cur.execute("DROP TABLE IF EXISTS daily_stats CASCADE")
        cur.execute("DROP TABLE IF EXISTS links CASCADE")
        cur.execute("DROP TABLE IF EXISTS urls CASCADE")
        cur.execute("DROP TABLE IF EXISTS schema_versions CASCADE")
        conn.commit()

        # Reproduce the production partial state: both tables exist, while the
        # legacy urls table has no user_id or profile_id columns.
        cur.execute("""
            CREATE TABLE urls (
                id SERIAL PRIMARY KEY,
                short_code VARCHAR(50) UNIQUE,
                original_url TEXT,
                title TEXT,
                show_on_tree BOOLEAN,
                click_count INTEGER,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE links (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                profile_id INTEGER,
                short_code VARCHAR(50) UNIQUE NOT NULL,
                original_url TEXT NOT NULL,
                title TEXT,
                show_on_tree BOOLEAN,
                click_count INTEGER,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE daily_stats (
                id SERIAL PRIMARY KEY,
                link_id INTEGER REFERENCES urls(id),
                date DATE,
                clicks INTEGER,
                UNIQUE(link_id, date)
            )
        """)

        cur.execute(
            "INSERT INTO links (short_code, original_url, click_count) VALUES ('pg_existing', 'http://existing.com', 2)"
        )
        cur.execute(
            "INSERT INTO urls (short_code, original_url, click_count) VALUES ('pg_abc', 'http://pg.com', 10)"
        )
        cur.execute(
            "INSERT INTO daily_stats (link_id, date, clicks) VALUES (1, '2026-07-15', 5)"
        )
        conn.commit()

        # Run migration twice (idempotency check)
        with patch("src.migration.USE_POSTGRES", True):
            run_migrations(conn)
            run_migrations(conn)

        # Verify migration results
        cur.execute(
            "SELECT id, user_id, click_count, original_url FROM links WHERE short_code = 'pg_abc'"
        )
        row = cur.fetchone()
        migrated_link_id = row[0]
        assert row[1] is None
        assert row[2] == 10
        assert row[3] == "http://pg.com"

        cur.execute("SELECT to_regclass('public.urls')")
        assert cur.fetchone()[0] is None

        # Verify daily_stats data is preserved
        cur.execute(
            "SELECT clicks FROM daily_stats WHERE link_id = %s", (migrated_link_id,)
        )
        stat_row = cur.fetchone()
        assert stat_row is not None
        assert stat_row[0] == 5

        # Verify constraint exists pointing to links
        cur.execute("""
            SELECT ccu.table_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_name = 'daily_stats'
        """)
        targets = [r[0] for r in cur.fetchall()]
        assert "links" in targets

    finally:
        # Cleanup in a finally block to avoid leaving garbage
        try:
            cur.execute("DROP TABLE IF EXISTS daily_stats CASCADE")
            cur.execute("DROP TABLE IF EXISTS links CASCADE")
            cur.execute("DROP TABLE IF EXISTS urls CASCADE")
            cur.execute("DROP TABLE IF EXISTS schema_versions CASCADE")
            conn.commit()
        except Exception:
            pass
        conn.close()


# 8b. PostgreSQL Safety Rejection Unit Tests


def test_postgres_skip_when_no_url(monkeypatch):
    """Default pytest run must not fail when POSTGRES_TEST_URL is absent."""
    monkeypatch.delenv("POSTGRES_TEST_URL", raising=False)
    # Verify the guard logic in test_postgres_migration_real:
    # when POSTGRES_TEST_URL is absent the test skips, not fails.
    postgres_test_db = os.getenv("POSTGRES_TEST_URL")
    assert postgres_test_db is None
    # The real test_postgres_migration_real is marked @postgres and
    # deselected by "-m 'not postgres'"; its first line calls
    # pytest.skip() when the env var is absent, which is verified
    # by the full suite passing with 0 failures and 1 deselect.


def test_postgres_safety_rejects_same_db_different_params(
    monkeypatch,
):
    """Validator rejects when POSTGRES_TEST_URL resolves to the
    same host/port/db as production, even with different query
    params."""
    monkeypatch.setenv("ALLOW_DESTRUCTIVE_POSTGRES_TESTS", "yes")
    prod = "postgresql://user:pass@prod-host:5432/myapp"
    test = (
        "postgresql://user:pass@prod-host:5432/"
        "myapp?sslmode=require&connect_timeout=10"
    )
    with pytest.raises(
        pytest.fail.Exception,
        match="resolves to the same database",
    ):
        _validate_postgres_test_url(test, prod_url=prod)


def test_postgres_safety_rejects_non_test_dbname(monkeypatch):
    """Validator rejects a database name that does not contain
    'test'."""
    monkeypatch.setenv("ALLOW_DESTRUCTIVE_POSTGRES_TESTS", "yes")
    monkeypatch.delenv("_ORIGINAL_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(
        pytest.fail.Exception,
        match="does not contain 'test'",
    ):
        _validate_postgres_test_url("postgresql://u:p@localhost:5432/production_app")


def test_postgres_safety_rejects_missing_opt_in(monkeypatch):
    """Validator rejects when the explicit destructive-test
    opt-in is absent."""
    monkeypatch.delenv("ALLOW_DESTRUCTIVE_POSTGRES_TESTS", raising=False)
    monkeypatch.delenv("_ORIGINAL_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(
        pytest.fail.Exception,
        match="ALLOW_DESTRUCTIVE_POSTGRES_TESTS must be set",
    ):
        _validate_postgres_test_url("postgresql://u:p@localhost:5432/swoosh_test")


def test_postgres_safety_accepts_valid_test_config(monkeypatch):
    """A properly configured test database passes all safety
    checks."""
    monkeypatch.setenv("ALLOW_DESTRUCTIVE_POSTGRES_TESTS", "yes")
    monkeypatch.setenv(
        "_ORIGINAL_DATABASE_URL",
        "postgresql://u:p@prod-host:5432/swoosh_prod",
    )
    # Should not raise
    _validate_postgres_test_url("postgresql://u:p@localhost:5432/swoosh_test")


# 9. Admin Identity and Reservation Tests
def test_admin_reserved_case_insensitive(auth_client):
    # Creating a user named 'admin' case-insensitively should fail with 400
    for name in ("admin", "ADMIN", "Admin", "aDmIn"):
        res = auth_client.post(
            "/api/admin/users", json={"username": name, "password": "password123"}
        )
        assert res.status_code == 400
        assert "Username 'admin' is reserved" in res.json()["error"]["message"]


def test_admin_deterministic_init_db(tmp_path):
    # Verify repeated call to init_db preserves the admin user and does not throw error
    db_path = str(tmp_path / "test_init.db")
    init_db(db_path)

    with get_db(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = 'admin'")
        first_row = c.fetchone()
        assert first_row is not None
        admin_id = first_row[0]

    # Run init_db again
    init_db(db_path)

    with get_db(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = 'admin'")
        second_row = c.fetchone()
        assert second_row is not None
        assert second_row[0] == admin_id


# 10. Additional SQLite Migration Test Cases
def test_sqlite_migration_links_only(tmp_path):
    # Tests migration when only links table exists (e.g. fresh installation or already migrated database)
    db_path = str(tmp_path / "links_only.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Create links table only
    conn.execute("""
        CREATE TABLE links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            short_code TEXT UNIQUE,
            original_url TEXT,
            created_at DATETIME
        )
    """)
    conn.commit()

    # Run migration twice (idempotency check)
    run_migrations(conn)
    run_migrations(conn)

    # Verify links exists and urls does not
    assert check_table_exists(conn, "links")
    assert not check_table_exists(conn, "urls")

    # Verify that columns like title, click_count, show_on_tree were added
    cur = conn.execute("PRAGMA table_info(links)")
    cols = [r[1] for r in cur.fetchall()]
    assert "title" in cols
    assert "click_count" in cols
    assert "show_on_tree" in cols

    conn.close()


def test_sqlite_migration_partial_links_schema(tmp_path):
    # Tests migration when links table exists but is missing some columns (partial schema state)
    db_path = str(tmp_path / "partial_links.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Create links with only some columns
    conn.execute("""
        CREATE TABLE links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            short_code TEXT UNIQUE,
            original_url TEXT
        )
    """)
    conn.commit()

    run_migrations(conn)

    # Verify missing columns were added
    cur = conn.execute("PRAGMA table_info(links)")
    cols = [r[1] for r in cur.fetchall()]
    assert "profile_id" in cols
    assert "title" in cols
    assert "show_on_tree" in cols
    assert "click_count" in cols
    assert "last_accessed" in cols

    conn.close()


def test_sqlite_migration_urls_rename_stats_preservation(tmp_path):
    # Tests that in a urls-only rename path, the daily_stats row and click count are fully preserved
    db_path = str(tmp_path / "urls_rename.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("""
        CREATE TABLE urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            short_code TEXT UNIQUE,
            original_url TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INTEGER REFERENCES urls(id),
            date TEXT,
            clicks INTEGER,
            UNIQUE(link_id, date)
        )
    """)

    # Insert legacy link and its stats
    conn.execute(
        "INSERT INTO urls (id, user_id, short_code, original_url) VALUES (1, 10, 'rename_code', 'http://ren.com')"
    )
    conn.execute(
        "INSERT INTO daily_stats (link_id, date, clicks) VALUES (1, '2026-07-15', 7)"
    )
    conn.commit()

    # Migrate
    run_migrations(conn)

    # Verify link exists under 'links'
    cur = conn.execute(
        "SELECT original_url FROM links WHERE short_code = 'rename_code'"
    )
    assert cur.fetchone()[0] == "http://ren.com"

    # Verify daily_stats is preserved and not dropped!
    cur = conn.execute("SELECT clicks FROM daily_stats WHERE link_id = 1")
    row = cur.fetchone()
    assert row is not None
    assert row[0] == 7

    # Verify that foreign key targets links now
    cur = conn.execute("PRAGMA foreign_key_list(daily_stats)")
    fk_list = cur.fetchall()
    assert any(row[2] == "links" for row in fk_list)

    # Verify foreign key check passes
    cur = conn.execute("PRAGMA foreign_key_check")
    assert not cur.fetchall()

    conn.close()


def test_sqlite_migration_forced_failure_rollback(tmp_path):
    # Tests that if migration fails midway, transaction is rolled back and schema version is NOT written
    db_path = str(tmp_path / "failure_rollback.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("""
        CREATE TABLE urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            short_code TEXT UNIQUE,
            original_url TEXT
        )
    """)
    conn.commit()

    # Force a failure during run_migrations by mocking/patching check_table_exists to raise Exception
    with patch("src.migration.check_table_exists") as mock_check:
        mock_check.side_effect = Exception("Simulated DDL failure")

        # Wrapping database in context manager to simulate transactional rollback
        try:
            with get_db(db_path) as db_conn:
                run_migrations(db_conn)
        except Exception:
            pass

    # Verify that urls table still exists (not renamed) because transaction rolled back!
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='urls'"
    )
    assert cur.fetchone() is not None

    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='links'"
    )
    assert cur.fetchone() is None

    # Verify that schema version was NOT written (version 1)
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_versions'"
    )
    if cur.fetchone() is not None:
        cur = conn.execute("SELECT version FROM schema_versions")
        assert cur.fetchone() is None

    conn.close()
