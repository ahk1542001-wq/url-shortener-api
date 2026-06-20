import pytest
from fastapi.testclient import TestClient

from app import app
from database import init_db


@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("config.DB_NAME", db_path)
    init_db(db_path)
    yield db_path


@pytest.fixture
def client():
    return TestClient(app)
