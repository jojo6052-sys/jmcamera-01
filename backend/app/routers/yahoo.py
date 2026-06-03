from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.yahoo_candidate import YahooAuctionCandidate
from app.schemas.candidates import CandidateRead, YahooSearchRequest
from app.services.yahoo_fetcher import fetch_yahoo_candidates

router = APIRouter(prefix='/api/yahoo', tags=['yahoo'])


@router.post('/search', response_model=list[CandidateRead])
def yahoo_search(payload: YahooSearchRequest, db: Session = Depends(get_db)):
    rows = fetch_yahoo_candidates(
        payload.keyword,
        payload.limit,
        min_price=payload.min_price,
        max_price=payload.max_price,
        exclude_words=payload.exclude_words,
    )

    entities: list[YahooAuctionCandidate] = []
    seen_auction_ids: set[str] = set()
    for row in rows:
        base_auction_id = row.auction_id
        auction_id = base_auction_id
        while auction_id in seen_auction_ids or db.query(YahooAuctionCandidate).filter(YahooAuctionCandidate.auction_id == auction_id).first():
            auction_id = f"{base_auction_id}-{uuid4().hex[:6]}"
        seen_auction_ids.add(auction_id)

        entity = YahooAuctionCandidate(
            auction_id=auction_id,
            title=row.title,
            normalized_title=row.normalized_title,
            url=row.url,
            current_price_jpy=row.current_price_jpy,
            buyout_price_jpy=row.buyout_price_jpy,
            bid_count=row.bid_count,
            end_time=row.end_time,
            seller_id=row.seller_id,
            seller_rating=row.seller_rating,
            description=row.description,
            image_urls=row.image_urls,
            search_keyword=row.search_keyword,
            status=row.status,
        )
        db.add(entity)
        entities.append(entity)

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"failed to save yahoo candidates: {exc.__class__.__name__}") from exc

    for item in entities:
        db.refresh(item)
    return entities
