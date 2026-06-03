from collections.abc import Generator
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.competitor import CompetitorItem, CompetitorSeller
from app.services.ebay_research import CompetitorItemPayload, EbayFetchBlockedError, _fetch_html, _parse_ebay_items, extract_ebay_seller_username


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
