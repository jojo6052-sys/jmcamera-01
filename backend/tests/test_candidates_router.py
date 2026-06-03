import csv
import io
from collections.abc import Generator
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.feedback import Feedback
from app.models.recommendation_score import RecommendationScore
from app.models.yahoo_candidate import YahooAuctionCandidate


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_candidates_router.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _create_candidate(db: Session, *, auction_id: str = "a-1") -> YahooAuctionCandidate:
    candidate = YahooAuctionCandidate(
        auction_id=auction_id,
        title="Canon EOS 5D",
        normalized_title="canon eos 5d",
        url=f"https://example.com/{auction_id}",
        current_price_jpy=12000,
        buyout_price_jpy=17000,
        bid_count=2,
        seller_id="seller-a",
        seller_rating=95,
        description="good",
        image_urls=["https://example.com/a.jpg"],
        search_keyword="canon",
        status="new",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def test_score_endpoint_updates_existing_score_instead_of_inserting_new_row() -> None:
    with TestingSessionLocal() as db:
        candidate = _create_candidate(db)

    response1 = client.post(f"/api/candidates/{candidate.id}/score")
    assert response1.status_code == 200
    first_score_id = response1.json()["id"]

    response2 = client.post(f"/api/candidates/{candidate.id}/score")
    assert response2.status_code == 200
    assert response2.json()["id"] == first_score_id

    with TestingSessionLocal() as db:
        rows = db.query(RecommendationScore).filter(RecommendationScore.candidate_id == candidate.id).all()
        assert len(rows) == 1


def test_list_candidates_rank_filter_returns_unique_candidates() -> None:
    with TestingSessionLocal() as db:
        candidate = _create_candidate(db, auction_id="a-2")
        db.add(
            RecommendationScore(
                candidate_id=candidate.id,
                similarity_score=Decimal("70.0"),
                expected_sale_price_usd=Decimal("200.0"),
                expected_sale_price_jpy=Decimal("30000.0"),
                expected_profit_jpy=Decimal("10000.0"),
                expected_profit_margin=Decimal("33.0"),
                recommended_max_bid_jpy=Decimal("16000.0"),
                seller_risk_score=Decimal("10.0"),
                description_risk_score=Decimal("10.0"),
                image_risk_score=Decimal("10.0"),
                total_score=Decimal("88.0"),
                rank="A",
                reason="r1",
                caution="c1",
            )
        )
        db.add(
            RecommendationScore(
                candidate_id=candidate.id,
                similarity_score=Decimal("75.0"),
                expected_sale_price_usd=Decimal("220.0"),
                expected_sale_price_jpy=Decimal("32000.0"),
                expected_profit_jpy=Decimal("12000.0"),
                expected_profit_margin=Decimal("37.0"),
                recommended_max_bid_jpy=Decimal("17000.0"),
                seller_risk_score=Decimal("8.0"),
                description_risk_score=Decimal("8.0"),
                image_risk_score=Decimal("8.0"),
                total_score=Decimal("90.0"),
                rank="A",
                reason="r2",
                caution="c2",
            )
        )
        db.commit()

    response = client.get("/api/candidates?rank=A")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["auction_id"] == "a-2"


def test_list_candidates_keyword_filter_matches_partial_title_and_search_keyword() -> None:
    with TestingSessionLocal() as db:
        _create_candidate(db, auction_id="nikon-1")
        _create_candidate(db, auction_id="canon-1")
        nikon = db.query(YahooAuctionCandidate).filter(YahooAuctionCandidate.auction_id == "nikon-1").one()
        canon = db.query(YahooAuctionCandidate).filter(YahooAuctionCandidate.auction_id == "canon-1").one()
        nikon.title = "ニコン F3 ボディ"
        nikon.normalized_title = "ニコン f3 ボディ"
        nikon.search_keyword = "ニコン フィルムカメラ"
        canon.title = "Canon EOS 5D"
        canon.normalized_title = "canon eos 5d"
        canon.search_keyword = "canon"
        db.commit()

    response = client.get("/api/candidates?keyword=ニコン")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["auction_id"] == "nikon-1"


def test_list_candidates_includes_latest_score_summary() -> None:
    with TestingSessionLocal() as db:
        candidate = _create_candidate(db, auction_id="score-summary-1")
        db.add(
            RecommendationScore(
                candidate_id=candidate.id,
                similarity_score=Decimal("70.0"),
                expected_sale_price_usd=Decimal("200.0"),
                expected_sale_price_jpy=Decimal("30000.0"),
                expected_profit_jpy=Decimal("10000.0"),
                expected_profit_margin=Decimal("33.0"),
                recommended_max_bid_jpy=Decimal("16000.0"),
                seller_risk_score=Decimal("10.0"),
                description_risk_score=Decimal("10.0"),
                image_risk_score=Decimal("10.0"),
                total_score=Decimal("88.0"),
                rank="A",
                reason="r1",
                caution="c1",
            )
        )
        db.commit()

    response = client.get("/api/candidates?keyword=Canon")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["latest_total_score"] == 88.0
    assert payload[0]["latest_rank"] == "A"
    assert payload[0]["latest_score"]["reason"] == "r1"
    assert payload[0]["latest_score"]["recommended_max_bid_jpy"] == 16000.0


def test_export_candidates_csv_includes_latest_score_details() -> None:
    with TestingSessionLocal() as db:
        candidate = _create_candidate(db, auction_id="csv-score-1")
        db.add(
            RecommendationScore(
                candidate_id=candidate.id,
                similarity_score=Decimal("70.0"),
                expected_sale_price_usd=Decimal("200.0"),
                expected_sale_price_jpy=Decimal("30000.0"),
                expected_profit_jpy=Decimal("10000.0"),
                expected_profit_margin=Decimal("33.0"),
                recommended_max_bid_jpy=Decimal("16000.0"),
                seller_risk_score=Decimal("10.0"),
                description_risk_score=Decimal("10.0"),
                image_risk_score=Decimal("10.0"),
                total_score=Decimal("88.0"),
                rank="A",
                reason="strong margin",
                caution="inspect optics",
            )
        )
        db.commit()

    response = client.get("/api/candidates/export.csv?keyword=Canon")
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.text)))

    assert len(rows) == 1
    assert rows[0]["auction_id"] == "csv-score-1"
    assert rows[0]["latest_total_score"] == "88.0"
    assert rows[0]["latest_rank"] == "A"
    assert rows[0]["latest_expected_profit_jpy"] == "10000.00"
    assert rows[0]["latest_recommended_max_bid_jpy"] == "16000.00"
    assert rows[0]["latest_reason"] == "strong margin"
    assert rows[0]["latest_caution"] == "inspect optics"


def test_rank_and_score_filters_use_latest_score_only() -> None:
    with TestingSessionLocal() as db:
        candidate = _create_candidate(db, auction_id="latest-filter-1")
        db.add(
            RecommendationScore(
                candidate_id=candidate.id,
                similarity_score=Decimal("70.0"),
                expected_sale_price_usd=Decimal("200.0"),
                expected_sale_price_jpy=Decimal("30000.0"),
                expected_profit_jpy=Decimal("10000.0"),
                expected_profit_margin=Decimal("33.0"),
                recommended_max_bid_jpy=Decimal("16000.0"),
                seller_risk_score=Decimal("10.0"),
                description_risk_score=Decimal("10.0"),
                image_risk_score=Decimal("10.0"),
                total_score=Decimal("91.0"),
                rank="A",
                reason="old strong score",
                caution="",
            )
        )
        db.add(
            RecommendationScore(
                candidate_id=candidate.id,
                similarity_score=Decimal("35.0"),
                expected_sale_price_usd=Decimal("120.0"),
                expected_sale_price_jpy=Decimal("18000.0"),
                expected_profit_jpy=Decimal("1000.0"),
                expected_profit_margin=Decimal("5.0"),
                recommended_max_bid_jpy=Decimal("10000.0"),
                seller_risk_score=Decimal("40.0"),
                description_risk_score=Decimal("30.0"),
                image_risk_score=Decimal("20.0"),
                total_score=Decimal("42.0"),
                rank="C",
                reason="new weak score",
                caution="review",
            )
        )
        db.commit()

    stale_rank_response = client.get("/api/candidates?rank=A")
    assert stale_rank_response.status_code == 200
    assert stale_rank_response.json() == []

    latest_rank_response = client.get("/api/candidates?rank=C")
    assert latest_rank_response.status_code == 200
    latest_rank_payload = latest_rank_response.json()
    assert len(latest_rank_payload) == 1
    assert latest_rank_payload[0]["latest_score"]["reason"] == "new weak score"

    high_score_response = client.get("/api/candidates?min_score=80")
    assert high_score_response.status_code == 200
    assert high_score_response.json() == []


def test_score_batch_endpoint_scores_candidates_in_request_order() -> None:
    with TestingSessionLocal() as db:
        candidate_a = _create_candidate(db, auction_id="batch-a")
        candidate_b = _create_candidate(db, auction_id="batch-b")
        candidate_a_id = candidate_a.id
        candidate_b_id = candidate_b.id

    response = client.post(
        "/api/candidates/score-batch",
        json={"candidate_ids": [candidate_b_id, candidate_a_id]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [row["candidate_id"] for row in payload] == [candidate_b_id, candidate_a_id]

    with TestingSessionLocal() as db:
        rows = db.query(RecommendationScore).order_by(RecommendationScore.candidate_id.asc()).all()
        assert len(rows) == 2


def test_score_batch_endpoint_rejects_duplicate_candidate_ids() -> None:
    with TestingSessionLocal() as db:
        candidate = _create_candidate(db, auction_id="batch-duplicate")
        candidate_id = candidate.id

    response = client.post(
        "/api/candidates/score-batch",
        json={"candidate_ids": [candidate_id, candidate_id]},
    )

    assert response.status_code == 422


def test_score_batch_endpoint_returns_missing_candidate_ids() -> None:
    with TestingSessionLocal() as db:
        candidate = _create_candidate(db, auction_id="batch-missing")
        candidate_id = candidate.id

    response = client.post(
        "/api/candidates/score-batch",
        json={"candidate_ids": [candidate_id, 999999]},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "candidates not found: [999999]"


def test_feedback_batch_endpoint_updates_visible_candidates() -> None:
    with TestingSessionLocal() as db:
        candidate_a = _create_candidate(db, auction_id="feedback-batch-a")
        candidate_b = _create_candidate(db, auction_id="feedback-batch-b")
        candidate_a_id = candidate_a.id
        candidate_b_id = candidate_b.id

    response = client.post(
        "/api/candidates/feedback-batch",
        json={"candidate_ids": [candidate_b_id, candidate_a_id], "user_decision": "review", "notes": "bulk review"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [row["candidate_id"] for row in payload] == [candidate_b_id, candidate_a_id]
    assert {row["user_decision"] for row in payload} == {"review"}
    assert {row["notes"] for row in payload} == {"bulk review"}

    with TestingSessionLocal() as db:
        statuses = {
            row.auction_id: row.status
            for row in db.query(YahooAuctionCandidate).filter(YahooAuctionCandidate.id.in_([candidate_a_id, candidate_b_id])).all()
        }
        assert statuses == {"feedback-batch-a": "review", "feedback-batch-b": "review"}
        assert db.query(Feedback).count() == 2


def test_feedback_batch_endpoint_rejects_duplicate_candidate_ids() -> None:
    with TestingSessionLocal() as db:
        candidate = _create_candidate(db, auction_id="feedback-batch-duplicate")
        candidate_id = candidate.id

    response = client.post(
        "/api/candidates/feedback-batch",
        json={"candidate_ids": [candidate_id, candidate_id], "user_decision": "skip"},
    )

    assert response.status_code == 422


def test_feedback_batch_endpoint_returns_missing_candidate_ids() -> None:
    with TestingSessionLocal() as db:
        candidate = _create_candidate(db, auction_id="feedback-batch-missing")
        candidate_id = candidate.id

    response = client.post(
        "/api/candidates/feedback-batch",
        json={"candidate_ids": [candidate_id, 999999], "user_decision": "skip"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "candidates not found: [999999]"


def test_feedback_endpoint_updates_candidate_status() -> None:
    with TestingSessionLocal() as db:
        candidate = _create_candidate(db, auction_id="feedback-status-1")

    response = client.post(f"/api/candidates/{candidate.id}/feedback", json={"user_decision": "skip"})
    assert response.status_code == 200
    assert response.json()["user_decision"] == "skip"

    with TestingSessionLocal() as db:
        updated = db.get(YahooAuctionCandidate, candidate.id)
        assert updated is not None
        assert updated.status == "skip"
