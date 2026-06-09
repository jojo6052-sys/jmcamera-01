from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.competitor import CompetitorItem, CompetitorSeller
from app.models.feedback import Feedback
from app.models.product import Product
from app.models.recommendation_score import RecommendationScore
from app.models.search_keyword import SearchKeyword
from app.models.yahoo_candidate import YahooAuctionCandidate
from app.schemas.phase import PhaseConfiguration, PhaseMetric, PhaseStatusRead

router = APIRouter(prefix=f"{settings.api_prefix}/phase", tags=["phase"])


@router.get("/status", response_model=PhaseStatusRead)
def get_phase_status(db: Session = Depends(get_db)) -> PhaseStatusRead:
    db.execute(text("SELECT 1"))
    ebay_api_credentials_configured = bool(settings.ebay_client_id.strip() and settings.ebay_client_secret.strip())
    ebay_compliance_configured = bool(
        settings.ebay_marketplace_deletion_verification_token.strip()
        and settings.ebay_marketplace_deletion_endpoint_url.strip()
    )
    metrics = [
        PhaseMetric(label="products", count=_count(db, Product)),
        PhaseMetric(label="search_keywords", count=_count(db, SearchKeyword)),
        PhaseMetric(label="yahoo_candidates", count=_count(db, YahooAuctionCandidate)),
        PhaseMetric(label="recommendation_scores", count=_count(db, RecommendationScore)),
        PhaseMetric(label="feedbacks", count=_count(db, Feedback)),
        PhaseMetric(label="competitor_sellers", count=_count(db, CompetitorSeller)),
        PhaseMetric(label="competitor_items", count=_count(db, CompetitorItem)),
    ]
    ready_checks = {
        "database_connected": True,
        "csv_import_ready": True,
        "analytics_ready": True,
        "search_keywords_ready": True,
        "yahoo_candidates_ready": True,
        "recommendation_scoring_ready": True,
        "competitor_research_ready": True,
        "ebay_compliance_endpoint_ready": ebay_compliance_configured,
    }
    core_ready_checks = {key: value for key, value in ready_checks.items() if key != "ebay_compliance_endpoint_ready"}
    core_ready = all(core_ready_checks.values())
    pending_configuration = []
    if not ebay_api_credentials_configured:
        pending_configuration.append("ebay_api_credentials")
    if not ebay_compliance_configured:
        pending_configuration.append("ebay_compliance_endpoint")

    return PhaseStatusRead(
        phase="MVP Phase 1",
        status="ready" if all(ready_checks.values()) else "ready_with_configuration_pending",
        core_ready=core_ready,
        database="ok",
        metrics=metrics,
        ready_checks=ready_checks,
        configuration=PhaseConfiguration(
            ebay_api_credentials_configured=ebay_api_credentials_configured,
            ebay_compliance_configured=ebay_compliance_configured,
        ),
        pending_configuration=pending_configuration,
    )


def _count(db: Session, model: type) -> int:
    return int(db.query(model).count())
