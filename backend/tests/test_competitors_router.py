import csv
import io
from collections.abc import Generator
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.competitor import CompetitorItem, CompetitorSeller
from app.services.ebay_research import (
    CompetitorItemPayload,
    EbayFetchBlockedError,
    _fetch_html,
    _parse_browse_api_items,
    _parse_ebay_items,
    extract_ebay_seller_username,
    fetch_active_items_with_browse_api,
    fetch_competitor_items,
    get_ebay_application_token,
)


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_competitors_router.db"
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


def test_extract_ebay_seller_username_from_common_urls() -> None:
    assert extract_ebay_seller_username("https://www.ebay.com/str/jmcamera") == "jmcamera"
    assert extract_ebay_seller_username("https://www.ebay.com/usr/camera-pro") == "camera-pro"
    assert extract_ebay_seller_username("https://www.ebay.com/sch/i.html?_ssn=top-seller") == "top-seller"


def test_get_ebay_application_token_uses_client_credentials(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"access_token": "token-123"}

    def fake_post(url, headers, data, timeout):
        captured.update({"url": url, "headers": headers, "data": data, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr(settings, "ebay_client_id", "client-id")
    monkeypatch.setattr(settings, "ebay_client_secret", "client-secret")
    monkeypatch.setattr("app.services.ebay_research.requests.post", fake_post)

    assert get_ebay_application_token() == "token-123"
    assert captured["url"] == "https://api.ebay.com/identity/v1/oauth2/token"
    assert captured["headers"]["Authorization"].startswith("Basic ")
    assert captured["data"] == {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}


def test_parse_browse_api_items_maps_active_item_payload() -> None:
    rows = _parse_browse_api_items(
        {
            "itemSummaries": [
                {
                    "itemId": "v1|123|0",
                    "title": "Canon EOS 5D",
                    "itemWebUrl": "https://www.ebay.com/itm/123",
                    "image": {"imageUrl": "https://i.ebayimg.com/images/canon.jpg"},
                    "price": {"value": "499.99", "currency": "USD"},
                }
            ]
        },
        source_url="https://api.ebay.com/buy/browse/v1/item_summary/search",
        limit=10,
    )

    assert len(rows) == 1
    assert rows[0].external_item_id == "v1|123|0"
    assert rows[0].title == "Canon EOS 5D"
    assert rows[0].item_status == "active"
    assert rows[0].price == Decimal("499.99")
    assert rows[0].currency == "USD"
    assert rows[0].image_url == "https://i.ebayimg.com/images/canon.jpg"


def test_fetch_active_items_with_browse_api_filters_by_seller(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        url = "https://api.ebay.com/buy/browse/v1/item_summary/search?filter=sellers%3A%7Bcamera-pro%7D"

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "itemSummaries": [
                    {
                        "itemId": "v1|456|0",
                        "title": "Nikon F3",
                        "itemHref": "https://api.ebay.com/buy/browse/v1/item/v1|456|0",
                        "price": {"value": "299.00", "currency": "USD"},
                    }
                ]
            }

    def fake_get(url, headers, params, timeout):
        captured.update({"url": url, "headers": headers, "params": params, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr(settings, "ebay_marketplace_id", "EBAY_US")
    monkeypatch.setattr("app.services.ebay_research.get_ebay_application_token", lambda: "token-123")
    monkeypatch.setattr("app.services.ebay_research.requests.get", fake_get)

    rows = fetch_active_items_with_browse_api("camera-pro", limit=25)

    assert captured["url"] == "https://api.ebay.com/buy/browse/v1/item_summary/search"
    assert captured["headers"]["Authorization"] == "Bearer token-123"
    assert captured["headers"]["X-EBAY-C-MARKETPLACE-ID"] == "EBAY_US"
    assert captured["params"] == {"filter": "sellers:{camera-pro}", "limit": 25}
    assert rows[0].external_item_id == "v1|456|0"


def test_fetch_competitor_items_uses_browse_api_for_active_when_credentials_exist(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ebay_client_id", "client-id")
    monkeypatch.setattr(settings, "ebay_client_secret", "client-secret")
    monkeypatch.setattr(
        "app.services.ebay_research.fetch_active_items_with_browse_api",
        lambda seller_username, limit: [
            CompetitorItemPayload(
                external_item_id="api-active-1",
                title="API Active Item",
                normalized_title="api active item",
                item_url="https://www.ebay.com/itm/api-active-1",
                image_url=None,
                price=Decimal("100.00"),
                currency="USD",
                item_status="active",
                source_url="https://api.ebay.com/buy/browse/v1/item_summary/search",
                raw={},
            )
        ],
    )
    monkeypatch.setattr("app.services.ebay_research._fetch_html", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("HTML fallback should not run for active-only API fetch")))

    seller_username, rows = fetch_competitor_items("https://www.ebay.com/str/camera-pro", include_active=True, include_sold=False, limit=10)

    assert seller_username == "camera-pro"
    assert len(rows) == 1
    assert rows[0].external_item_id == "api-active-1"


def test_fetch_html_converts_ebay_403_to_blocked_error(monkeypatch) -> None:
    class FakeResponse:
        status_code = 403
        text = "Forbidden"

        def raise_for_status(self):  # pragma: no cover - must not be called for 403 mapping
            raise AssertionError("raise_for_status should not be called for mapped 403")

    monkeypatch.setattr("app.services.ebay_research.requests.get", lambda *args, **kwargs: FakeResponse())

    try:
        _fetch_html("https://www.ebay.com/sch/i.html?_ssn=blocked")
    except EbayFetchBlockedError as exc:
        assert "HTTP 403 Forbidden" in str(exc)
        assert "official eBay API" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected EbayFetchBlockedError")


def test_parse_ebay_items_reads_title_price_link_and_image() -> None:
    html = """
    <ul>
      <li class="s-item">
        <a class="s-item__link" href="https://www.ebay.com/itm/Nikon-F3/123456789012"><span class="s-item__title">Nikon F3 Body</span></a>
        <span class="s-item__price">US $299.99</span>
        <div class="s-item__image-wrapper"><img src="https://i.ebayimg.com/images/nikon.jpg" /></div>
      </li>
    </ul>
    """

    rows = _parse_ebay_items(html, source_url="https://www.ebay.com/sch/i.html?_ssn=seller", item_status="sold", limit=10)

    assert len(rows) == 1
    assert rows[0].external_item_id == "123456789012"
    assert rows[0].title == "Nikon F3 Body"
    assert rows[0].price == Decimal("299.99")
    assert rows[0].currency == "USD"
    assert rows[0].item_status == "sold"
    assert rows[0].image_url == "https://i.ebayimg.com/images/nikon.jpg"


def test_analyze_competitor_upserts_seller_items_and_summary(monkeypatch) -> None:
    def fake_fetch(*args, **kwargs):
        return "camera-pro", [
            CompetitorItemPayload(
                external_item_id="active-1",
                title="Canon EOS 5D Mark II",
                normalized_title="canon eos 5d mark ii",
                item_url="https://www.ebay.com/itm/active-1",
                image_url="https://example.com/active.jpg",
                price=Decimal("399.00"),
                currency="USD",
                item_status="active",
                source_url="https://www.ebay.com/sch/i.html?_ssn=camera-pro",
                raw={"price_text": "US $399.00"},
            ),
            CompetitorItemPayload(
                external_item_id="sold-1",
                title="Nikon F3 Body",
                normalized_title="nikon f3 body",
                item_url="https://www.ebay.com/itm/sold-1",
                image_url="https://example.com/sold.jpg",
                price=Decimal("250.00"),
                currency="USD",
                item_status="sold",
                source_url="https://www.ebay.com/sch/i.html?_ssn=camera-pro&LH_Sold=1&LH_Complete=1",
                raw={"price_text": "US $250.00"},
            ),
        ]

    monkeypatch.setattr("app.routers.competitors.fetch_competitor_items", fake_fetch)
    previous_override = with_test_db_override()
    try:
        response = client.post("/api/competitors/analyze", json={"seller_url": "https://www.ebay.com/str/camera-pro", "limit": 20})
        assert response.status_code == 200
        payload = response.json()

        assert payload["seller"]["seller_username"] == "camera-pro"
        assert payload["seller"]["active_count"] == 1
        assert payload["seller"]["sold_count"] == 1
        assert payload["seller"]["avg_active_price"] == 399.0
        assert payload["seller"]["avg_sold_price"] == 250.0
        assert {row["item_status"] for row in payload["items"]} == {"active", "sold"}

        with TestingSessionLocal() as db:
            assert db.query(CompetitorSeller).count() == 1
            assert db.query(CompetitorItem).count() == 2
    finally:
        restore_db_override(previous_override)


def test_analyze_competitor_records_blocked_status_without_raw_httperror(monkeypatch) -> None:
    def fake_fetch(*args, **kwargs):
        raise EbayFetchBlockedError("eBay blocked this server-side request with HTTP 403 Forbidden.")

    monkeypatch.setattr("app.routers.competitors.fetch_competitor_items", fake_fetch)
    previous_override = with_test_db_override()
    try:
        response = client.post("/api/competitors/analyze", json={"seller_url": "https://www.ebay.com/str/blocked-seller"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["seller"]["seller_username"] == "blocked-seller"
        assert payload["seller"]["fetch_status"] == "blocked"
        assert "HTTP 403 Forbidden" in payload["seller"]["last_error"]
        assert "HTTPError" not in payload["seller"]["last_error"]
        assert payload["items"] == []
    finally:
        restore_db_override(previous_override)


def test_import_competitor_html_saves_sold_items_from_uploaded_file() -> None:
    previous_override = with_test_db_override()
    try:
        html = """
        <ul>
          <li class="s-item">
            <a class="s-item__link" href="https://www.ebay.com/itm/Nikon-F3/123456789012"><span class="s-item__title">Nikon F3 Body</span></a>
            <span class="s-item__price">US $299.99</span>
            <div class="s-item__image-wrapper"><img src="https://i.ebayimg.com/images/nikon.jpg" /></div>
          </li>
        </ul>
        """
        response = client.post(
            "/api/competitors/import-html",
            data={"seller_url": "https://www.ebay.com/str/upload-seller", "item_status": "sold"},
            files={"file": ("sold.html", html, "text/html")},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["seller"]["seller_username"] == "upload-seller"
        assert payload["seller"]["fetch_status"] == "imported"
        assert payload["seller"]["sold_count"] == 1
        assert payload["items"][0]["title"] == "Nikon F3 Body"
        assert payload["items"][0]["item_status"] == "sold"

        with TestingSessionLocal() as db:
            seller = db.query(CompetitorSeller).filter(CompetitorSeller.seller_username == "upload-seller").one()
            item = db.query(CompetitorItem).filter(CompetitorItem.seller_id == seller.id).one()
            assert item.external_item_id == "123456789012"
            assert item.price == Decimal("299.99")
    finally:
        restore_db_override(previous_override)


def test_competitor_items_can_be_filtered_by_status_and_keyword() -> None:
    previous_override = with_test_db_override()
    try:
        with TestingSessionLocal() as db:
            seller = CompetitorSeller(marketplace="ebay", seller_username="filter-seller", seller_url="https://www.ebay.com/str/filter-seller", fetch_status="ok")
            db.add(seller)
            db.flush()
            db.add_all([
                CompetitorItem(seller_id=seller.id, marketplace="ebay", external_item_id="1", title="Nikon F3", item_url="https://example.com/1", item_status="sold", source_url="https://example.com", raw={}),
                CompetitorItem(seller_id=seller.id, marketplace="ebay", external_item_id="2", title="Canon AE-1", item_url="https://example.com/2", item_status="active", source_url="https://example.com", raw={}),
            ])
            db.commit()
            seller_id = seller.id

        response = client.get(f"/api/competitors/{seller_id}/items?item_status=sold&keyword=Nikon")
        assert response.status_code == 200
        rows = response.json()
        assert len(rows) == 1
        assert rows[0]["title"] == "Nikon F3"
    finally:
        restore_db_override(previous_override)


def test_export_competitor_items_csv_applies_status_and_keyword_filters() -> None:
    previous_override = with_test_db_override()
    try:
        with TestingSessionLocal() as db:
            seller = CompetitorSeller(marketplace="ebay", seller_username="csv-seller", seller_url="https://www.ebay.com/str/csv-seller", fetch_status="ok")
            db.add(seller)
            db.flush()
            db.add_all([
                CompetitorItem(seller_id=seller.id, marketplace="ebay", external_item_id="sold-1", title="Nikon F3 Body", item_url="https://example.com/sold-1", item_status="sold", price=Decimal("299.99"), currency="USD", source_url="https://example.com/sold", raw={}),
                CompetitorItem(seller_id=seller.id, marketplace="ebay", external_item_id="active-1", title="Nikon F3 Active", item_url="https://example.com/active-1", item_status="active", price=Decimal("399.99"), currency="USD", source_url="https://example.com/active", raw={}),
                CompetitorItem(seller_id=seller.id, marketplace="ebay", external_item_id="sold-2", title="Canon AE-1", item_url="https://example.com/sold-2", item_status="sold", price=Decimal("199.99"), currency="USD", source_url="https://example.com/sold", raw={}),
            ])
            db.commit()
            seller_id = seller.id

        response = client.get(f"/api/competitors/{seller_id}/export.csv?item_status=sold&keyword=Nikon")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert "competitor-csv-seller-items.csv" in response.headers["content-disposition"]
        rows = list(csv.DictReader(io.StringIO(response.text)))
        assert len(rows) == 1
        assert rows[0]["seller_username"] == "csv-seller"
        assert rows[0]["external_item_id"] == "sold-1"
        assert rows[0]["title"] == "Nikon F3 Body"
        assert rows[0]["price"] == "299.99"
    finally:
        restore_db_override(previous_override)
