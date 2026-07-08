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
                CREATE TABLE IF NOT EXISTS urls (
                    id SERIAL PRIMARY KEY,
                    short_code TEXT UNIQUE NOT NULL,
                    original_url TEXT NOT NULL,
                    click_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP
                )
            """)
    else:
        with get_db(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    short_code TEXT UNIQUE NOT NULL,
                    original_url TEXT NOT NULL,
                    click_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_accessed DATETIME
                )
            """)
