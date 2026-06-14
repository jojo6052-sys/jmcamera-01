from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.product import Product
from app.models.search_keyword import SearchKeyword

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase_status.db"
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


def test_phase_status_reports_db_counts_and_configuration(monkeypatch) -> None:
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "ebay_client_id", "client-id")
    monkeypatch.setattr(settings, "ebay_client_secret", "client-secret")
    monkeypatch.setattr(settings, "ebay_marketplace_deletion_verification_token", "token")
    monkeypatch.setattr(settings, "ebay_marketplace_deletion_endpoint_url", "https://example.com/api/ebay/marketplace-account-deletion")
    try:
        with TestingSessionLocal() as db:
            db.add(Product(title="Canon EOS 5D", category="Camera", sale_price_jpy=100000, final_profit_jpy=25000))
            db.add(SearchKeyword(keyword="canon eos 5d", category="Competitor Research"))
            db.commit()

        response = client.get("/api/phase/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["phase"] == "MVP Phase 1"
        assert payload["status"] == "ready"
        assert payload["core_ready"] is True
        assert payload["database"] == "ok"
        metrics = {item["label"]: item["count"] for item in payload["metrics"]}
        assert metrics["products"] == 1
        assert metrics["search_keywords"] == 1
        assert metrics["competitor_sellers"] == 0
        assert payload["ready_checks"]["database_connected"] is True
        assert payload["ready_checks"]["analytics_ready"] is True
        assert payload["configuration"]["ebay_api_credentials_configured"] is True
        assert payload["configuration"]["ebay_compliance_configured"] is True
        assert payload["pending_configuration"] == []
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override


def test_phase_status_keeps_local_mvp_ready_when_external_configuration_is_pending(monkeypatch) -> None:
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "ebay_client_id", "")
    monkeypatch.setattr(settings, "ebay_client_secret", "")
    monkeypatch.setattr(settings, "ebay_marketplace_deletion_verification_token", "")
    monkeypatch.setattr(settings, "ebay_marketplace_deletion_endpoint_url", "")
    try:
        response = client.get("/api/phase/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ready_with_configuration_pending"
        assert payload["core_ready"] is True
        assert payload["ready_checks"]["ebay_compliance_endpoint_ready"] is False
        assert payload["configuration"]["ebay_api_credentials_configured"] is False
        assert payload["configuration"]["ebay_compliance_configured"] is False
        assert payload["pending_configuration"] == ["ebay_api_credentials", "ebay_compliance_endpoint"]
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override
