import sqlite3
from contextlib import contextmanager

from src import config

USE_POSTGRES = bool(config.DATABASE_URL)


def _connect(db_path: str = None):
    if USE_POSTGRES:
        import psycopg2

        return psycopg2.connect(config.DATABASE_URL)
    return sqlite3.connect(db_path or config.DB_NAME)


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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    username TEXT UNIQUE NOT NULL,
                    bio TEXT,
                    tree_views INTEGER DEFAULT 0,
                    social_links TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS urls (
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
                    link_id INTEGER REFERENCES urls(id),
                    date DATE NOT NULL,
                    clicks INTEGER DEFAULT 0,
                    UNIQUE(link_id, date)
                )
            """)
    else:
        with get_db(db_path) as conn:
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
                    tree_views INTEGER DEFAULT 0,
                    social_links TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS urls (
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
                    link_id INTEGER REFERENCES urls(id),
                    date TEXT NOT NULL,
                    clicks INTEGER DEFAULT 0,
                    UNIQUE(link_id, date)
                )
            """)
