import random
import re
import time
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.yahoo_candidate import YahooAuctionCandidate
from app.schemas.candidates import CandidateRead, YahooSearchRequest

router = APIRouter(prefix='/api/yahoo', tags=['yahoo'])


@router.post('/search', response_model=list[CandidateRead])
def yahoo_search(payload: YahooSearchRequest, db: Session = Depends(get_db)):
    # MVP stub designed for safe/low-impact operation and future scraper replacement.
    # Random small wait mimics polite pacing.
    time.sleep(random.uniform(0.2, 0.6))

    sanitized = re.sub(r'\s+', ' ', payload.keyword).strip()
    limit = max(1, min(payload.limit, 50))
    results: list[YahooAuctionCandidate] = []

    for i in range(limit):
        auction_id = f'mvp-{sanitized[:20]}-{i}-{uuid4().hex[:8]}'
        entity = YahooAuctionCandidate(
            auction_id=auction_id,
            title=f'{sanitized} サンプル候補 {i + 1}',
            normalized_title=sanitized.lower(),
            url=f'https://auctions.yahoo.co.jp/jp/auction/{auction_id}',
            current_price_jpy=5000 + i * 1000,
            buyout_price_jpy=9000 + i * 1200,
            bid_count=i,
            end_time=datetime.utcnow() + timedelta(hours=i + 1),
            seller_id=f'seller_{i+1:03d}',
            seller_rating=95.0,
            description='MVP generated candidate. Replace with real scraper output in next phase.',
            image_urls=[f'https://example.com/images/{auction_id}.jpg'],
            search_keyword=sanitized,
            status='new',
        )
        db.add(entity)
        results.append(entity)

    db.commit()
    for item in results:
        db.refresh(item)
    return results
