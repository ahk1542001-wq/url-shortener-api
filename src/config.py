import os
import re

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
DB_NAME: str = os.getenv("DB_NAME", "shortener.db")
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "5000"))
RATE_LIMIT: str = os.getenv("RATE_LIMIT", "30/minute")
JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-me")
ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")

R2_ENDPOINT: str = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET: str = os.getenv("R2_BUCKET", "")
R2_PUBLIC_BASE_URL: str = os.getenv("R2_PUBLIC_BASE_URL", "")

# Validation checks on startup
if not JWT_SECRET:
    raise ValueError("JWT_SECRET must be explicitly set.")
if JWT_SECRET.lower() in (
    "super-secret-key-change-me",
    "super_secret_key_change_me",
    "generate_a_secure_random_string_of_at_least_32_chars",
):
    raise ValueError("JWT_SECRET must not use the default placeholder values.")
if len(JWT_SECRET) < 32:
    raise ValueError("JWT_SECRET must be at least 32 characters long.")

if not ADMIN_PASSWORD_HASH or ADMIN_PASSWORD_HASH.strip() == "":
    raise ValueError("ADMIN_PASSWORD_HASH must be explicitly set.")
if ADMIN_PASSWORD_HASH.strip() == "$2b$12$your_bcrypt_hash_here":
    raise ValueError(
        "ADMIN_PASSWORD_HASH must not use the placeholder value from .env.example."
    )
if not re.match(r"^\$2[ayb]\$[0-9]{2}\$[./A-Za-z0-9]{53}$", ADMIN_PASSWORD_HASH):
    raise ValueError("ADMIN_PASSWORD_HASH must be a valid configured bcrypt hash.")

# Validate R2 variables together
r2_vars = [
    R2_ENDPOINT,
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
    R2_BUCKET,
    R2_PUBLIC_BASE_URL,
]
any_r2 = any(r2_vars)
all_r2 = all(r2_vars)
if any_r2 and not all_r2:
    raise ValueError(
        "All R2 configuration variables (R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, R2_PUBLIC_BASE_URL) must be set together."
    )
