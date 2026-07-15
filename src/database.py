import sqlite3
from contextlib import contextmanager

from src import config

USE_POSTGRES = bool(config.DATABASE_URL)


def _connect(db_path: str = None):
    if USE_POSTGRES:
        import psycopg2

        return psycopg2.connect(config.DATABASE_URL)
    conn = sqlite3.connect(db_path or config.DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _placeholder() -> str:
    return "%s" if USE_POSTGRES else "?"


@contextmanager
def get_db(db_path: str = None):
    conn = _connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = None):
    if USE_POSTGRES:
        with get_db(db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    username TEXT UNIQUE NOT NULL,
                    bio TEXT,
                    avatar_url TEXT,
                    avatar_object_key TEXT,
                    tree_views INTEGER DEFAULT 0,
                    social_links TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    profile_id INTEGER REFERENCES profiles(id),
                    short_code TEXT UNIQUE NOT NULL,
                    original_url TEXT NOT NULL,
                    title TEXT,
                    show_on_tree BOOLEAN DEFAULT FALSE,
                    click_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id SERIAL PRIMARY KEY,
                    link_id INTEGER REFERENCES links(id) ON DELETE CASCADE,
                    date DATE NOT NULL,
                    clicks INTEGER DEFAULT 0,
                    UNIQUE(link_id, date)
                )
            """)

            # Upgrade existing schemas before queries reference newly added columns.
            from src.migration import run_migrations

            run_migrations(conn)

            # Create/upsert admin user and profile
            admin_pwd_hash = config.ADMIN_PASSWORD_HASH or "dummy"
            cur.execute(
                """
                INSERT INTO users (username, hashed_password)
                VALUES (%s, %s)
                ON CONFLICT (username) DO UPDATE
                SET hashed_password = EXCLUDED.hashed_password,
                    is_active = TRUE
            """,
                ("admin", admin_pwd_hash),
            )

            cur.execute("SELECT id FROM users WHERE LOWER(username) = 'admin'")
            admin_uid = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO profiles (user_id, username, bio)
                VALUES (%s, 'admin', 'Admin Profile')
                ON CONFLICT (username) DO NOTHING
            """,
                (admin_uid,),
            )

    else:
        with get_db(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    profile_id INTEGER REFERENCES profiles(id),
                    short_code TEXT UNIQUE NOT NULL,
                    original_url TEXT NOT NULL,
                    title TEXT,
                    show_on_tree BOOLEAN DEFAULT 0,
                    click_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_accessed DATETIME
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    link_id INTEGER REFERENCES links(id) ON DELETE CASCADE,
                    date TEXT NOT NULL,
                    clicks INTEGER DEFAULT 0,
                    UNIQUE(link_id, date)
                )
            """)

            # Upgrade existing schemas before queries reference newly added columns.
            from src.migration import run_migrations

            run_migrations(conn)

            # Create/upsert admin user
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE LOWER(username) = 'admin'")
            row = c.fetchone()
            admin_pwd_hash = config.ADMIN_PASSWORD_HASH or "dummy"
            if row:
                admin_uid = row[0]
                c.execute(
                    "UPDATE users SET hashed_password = ?, is_active = 1 WHERE id = ?",
                    (admin_pwd_hash, admin_uid),
                )
            else:
                c.execute(
                    "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
                    ("admin", admin_pwd_hash),
                )
                admin_uid = c.lastrowid

            # Ensure admin profile exists
            c.execute("SELECT id FROM profiles WHERE LOWER(username) = 'admin'")
            if not c.fetchone():
                c.execute(
                    "INSERT INTO profiles (user_id, username, bio) VALUES (?, ?, ?)",
                    (admin_uid, "admin", "Admin Profile"),
                )
