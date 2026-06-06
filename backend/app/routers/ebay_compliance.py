import hashlib
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.competitor import CompetitorSeller

router = APIRouter(prefix="/api/ebay", tags=["ebay-compliance"])

USERNAME_KEYS = {"user_name", "username", "seller_username", "sellerUserName", "userId", "user_id"}


@router.get("/marketplace-account-deletion")
def verify_marketplace_account_deletion_endpoint(
    challenge_code: str = Query(..., min_length=1),
) -> dict[str, str]:
    verification_token = settings.ebay_marketplace_deletion_verification_token.strip()
    endpoint_url = settings.ebay_marketplace_deletion_endpoint_url.strip()
    if not verification_token or not endpoint_url:
        raise HTTPException(
            status_code=503,
            detail="eBay marketplace deletion verification is not configured",
        )

    return {
        "challengeResponse": compute_challenge_response(
            challenge_code=challenge_code,
            verification_token=verification_token,
            endpoint_url=endpoint_url,
        )
    }


@router.post("/marketplace-account-deletion")
async def receive_marketplace_account_deletion_notification(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    payload = await request.json()
    usernames = sorted(extract_possible_usernames(payload))
    deleted_competitor_sellers = 0

    if usernames:
        sellers = db.query(CompetitorSeller).filter(CompetitorSeller.seller_username.in_(usernames)).all()
        deleted_competitor_sellers = len(sellers)
        for seller in sellers:
            db.delete(seller)
        db.commit()

    return {
        "status": "received",
        "matched_usernames": usernames,
        "deleted_competitor_sellers": deleted_competitor_sellers,
    }


def compute_challenge_response(*, challenge_code: str, verification_token: str, endpoint_url: str) -> str:
    return hashlib.sha256(f"{challenge_code}{verification_token}{endpoint_url}".encode("utf-8")).hexdigest()


def extract_possible_usernames(payload: Any) -> set[str]:
    usernames: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in USERNAME_KEYS and isinstance(value, str) and value.strip():
                usernames.add(value.strip())
            else:
                usernames.update(extract_possible_usernames(value))
    elif isinstance(payload, list):
        for item in payload:
            usernames.update(extract_possible_usernames(item))
    return usernames
