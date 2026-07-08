import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.database import init_db

@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("src.config.DB_NAME", db_path)
    monkeypatch.setattr("src.config.DATABASE_URL", "")
    monkeypatch.setattr("src.config.ACCESS_PASSWORD", "")
    monkeypatch.setattr("src.database.USE_POSTGRES", False)
    init_db(db_path)
    yield db_path


@pytest.fixture
def client():
    return TestClient(app)
