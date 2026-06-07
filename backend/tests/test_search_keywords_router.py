from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_search_keywords_router.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
client = TestClient(app)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def with_test_db_override():
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    return previous_override


def restore_db_override(previous_override) -> None:
    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override


def test_create_keyword_trims_optional_fields() -> None:
    previous_override = with_test_db_override()
    try:
        response = client.post(
            "/api/search-keywords",
            json={"keyword": "  Nikon F3  ", "category": "  Camera  ", "brand": "  ", "model_group": "  F series  "},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["keyword"] == "Nikon F3"
        assert payload["category"] == "Camera"
        assert payload["brand"] is None
        assert payload["model_group"] == "F series"
    finally:
        restore_db_override(previous_override)


def test_create_keyword_returns_conflict_for_duplicate_keyword() -> None:
    previous_override = with_test_db_override()
    try:
        response1 = client.post("/api/search-keywords", json={"keyword": "Canon EOS"})
        assert response1.status_code == 200

        response2 = client.post("/api/search-keywords", json={"keyword": "Canon EOS"})
        assert response2.status_code == 409
        assert response2.json()["detail"] == "search keyword already exists"
    finally:
        restore_db_override(previous_override)


def test_update_keyword_returns_conflict_for_duplicate_keyword() -> None:
    previous_override = with_test_db_override()
    try:
        response1 = client.post("/api/search-keywords", json={"keyword": "Canon EOS"})
        response2 = client.post("/api/search-keywords", json={"keyword": "Nikon F3"})
        assert response1.status_code == 200
        assert response2.status_code == 200

        update = client.put(f"/api/search-keywords/{response2.json()['id']}", json={"keyword": "Canon EOS"})
        assert update.status_code == 409
        assert update.json()["detail"] == "search keyword already exists"
    finally:
        restore_db_override(previous_override)
