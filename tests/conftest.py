import os
import pytest

# Preserve the original DATABASE_URL for PostgreSQL safety checks before clearing
os.environ["_ORIGINAL_DATABASE_URL"] = os.environ.get("DATABASE_URL", "")
# Ensure tests run against sqlite by clearing DATABASE_URL before importing the app
os.environ["DATABASE_URL"] = ""
os.environ["JWT_SECRET"] = "test-secret-32-chars-long-security-key"
os.environ["ADMIN_PASSWORD_HASH"] = (
    "$2b$12$V5/S5.d2nQ25h9YQp6n2re4u5S5u5S5u5S5u5S5u5S5u5S5u5S5u5"  # Valid dummy hash for tests
)

from fastapi.testclient import TestClient
from src.main import app
from src.database import init_db


@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")

    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash("testpass")

    monkeypatch.setattr("src.config.DB_NAME", db_path)
    monkeypatch.setattr("src.config.DATABASE_URL", "")
    monkeypatch.setattr(
        "src.config.JWT_SECRET", "test-secret-32-chars-long-security-key"
    )
    monkeypatch.setattr("src.config.ADMIN_PASSWORD_HASH", hashed)
    monkeypatch.setattr("src.database.USE_POSTGRES", False)
    init_db(db_path)

    yield db_path


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_client(client):
    # Login to get token using the admin user created during init_db
    r = client.post("/api/login", json={"username": "admin", "password": "testpass"})
    token = r.json().get("token")
    if not token:
        raise ValueError(f"Failed to get token: {r.json()}")

    # Return client with auth header and active profile header
    client.headers.update(
        {"Authorization": f"Bearer {token}", "X-Active-Profile": "admin"}
    )
    return client
