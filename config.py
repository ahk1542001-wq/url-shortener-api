import os

from dotenv import load_dotenv

load_dotenv()

DB_NAME: str = os.getenv("DB_NAME", "shortener.db")
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "5000"))
RATE_LIMIT: str = os.getenv("RATE_LIMIT", "30/minute")
