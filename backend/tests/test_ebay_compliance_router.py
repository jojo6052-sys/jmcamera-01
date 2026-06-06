import hashlib
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.competitor import CompetitorItem, CompetitorSeller
from app.routers.ebay_compliance import compute_challenge_response, extract_possible_usernames

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ebay_compliance_router.db"
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


def test_compute_challenge_response_matches_ebay_sha256_contract() -> None:
    challenge_code = "challenge-123"
    verification_token = "verification-token-abc"
    endpoint_url = "https://example.com/api/ebay/marketplace-account-deletion"

    expected = hashlib.sha256(f"{challenge_code}{verification_token}{endpoint_url}".encode("utf-8")).hexdigest()

    assert compute_challenge_response(
        challenge_code=challenge_code,
        verification_token=verification_token,
        endpoint_url=endpoint_url,
    ) == expected


def test_marketplace_account_deletion_challenge_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ebay_marketplace_deletion_verification_token", "verification-token-abc")
    monkeypatch.setattr(settings, "ebay_marketplace_deletion_endpoint_url", "https://example.com/api/ebay/marketplace-account-deletion")

    response = client.get("/api/ebay/marketplace-account-deletion?challenge_code=challenge-123")

    assert response.status_code == 200
    assert response.json() == {
        "challengeResponse": compute_challenge_response(
            challenge_code="challenge-123",
            verification_token="verification-token-abc",
            endpoint_url="https://example.com/api/ebay/marketplace-account-deletion",
        )
    }


def test_marketplace_account_deletion_challenge_requires_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ebay_marketplace_deletion_verification_token", "")
    monkeypatch.setattr(settings, "ebay_marketplace_deletion_endpoint_url", "")

    response = client.get("/api/ebay/marketplace-account-deletion?challenge_code=challenge-123")

    assert response.status_code == 503
    assert response.json()["detail"] == "eBay marketplace deletion verification is not configured"


def test_extract_possible_usernames_from_nested_notification_payload() -> None:
    payload = {
        "metadata": {"topic": "MARKETPLACE_ACCOUNT_DELETION"},
        "notification": {
            "data": {
                "username": "seller-a",
                "nested": [{"sellerUserName": "seller-b"}, {"ignored": "x"}],
            }
        },
    }

    assert extract_possible_usernames(payload) == {"seller-a", "seller-b"}


def test_marketplace_account_deletion_notification_deletes_matching_competitor_seller() -> None:
    previous_override = with_test_db_override()
    try:
        with TestingSessionLocal() as db:
            seller = CompetitorSeller(
                marketplace="ebay",
                seller_username="seller-to-delete",
                seller_url="https://www.ebay.com/str/seller-to-delete",
                fetch_status="ok",
            )
            db.add(seller)
            db.flush()
            db.add(
                CompetitorItem(
                    seller_id=seller.id,
                    marketplace="ebay",
                    external_item_id="1",
                    title="Nikon F3",
                    item_url="https://example.com/1",
                    item_status="sold",
                    source_url="https://example.com",
                    raw={},
                )
            )
            db.commit()

        response = client.post(
            "/api/ebay/marketplace-account-deletion",
            json={"notification": {"data": {"username": "seller-to-delete"}}},
        )

        assert response.status_code == 200
        assert response.json()["deleted_competitor_sellers"] == 1
        with TestingSessionLocal() as db:
            assert db.query(CompetitorSeller).count() == 0
            assert db.query(CompetitorItem).count() == 0
    finally:
        restore_db_override(previous_override)
