from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.recommendation_score import RecommendationScore
from app.models.yahoo_candidate import YahooAuctionCandidate
from app.schemas.candidates import CandidateRead
from app.schemas.scores import RecommendationScoreRead
from app.services.scoring import compute_recommendation

router = APIRouter(prefix='/api/candidates', tags=['candidates'])


@router.get('', response_model=list[CandidateRead])
def list_candidates(
    db: Session = Depends(get_db),
    keyword: str | None = None,
    rank: str | None = None,
    min_score: float | None = Query(default=None),
    max_price: float | None = Query(default=None),
    seller_id: str | None = None,
    status: str | None = None,
):
    q = db.query(YahooAuctionCandidate)
    if keyword:
        q = q.filter(YahooAuctionCandidate.search_keyword == keyword)
    if max_price is not None:
        q = q.filter(YahooAuctionCandidate.current_price_jpy <= max_price)
    if seller_id:
        q = q.filter(YahooAuctionCandidate.seller_id == seller_id)
    if status:
        q = q.filter(YahooAuctionCandidate.status == status)

    if rank or min_score is not None:
        q = q.join(RecommendationScore, RecommendationScore.candidate_id == YahooAuctionCandidate.id)
        if rank:
            q = q.filter(RecommendationScore.rank == rank)
        if min_score is not None:
            q = q.filter(RecommendationScore.total_score >= min_score)

    return q.order_by(YahooAuctionCandidate.created_at.desc()).limit(200).all()


@router.get('/{candidate_id}', response_model=CandidateRead)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    entity = db.get(YahooAuctionCandidate, candidate_id)
    if not entity:
        raise HTTPException(status_code=404, detail='candidate not found')
    return entity


@router.post('/{candidate_id}/score', response_model=RecommendationScoreRead)
def score_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(YahooAuctionCandidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail='candidate not found')

    computed = compute_recommendation(candidate)

    score = RecommendationScore(candidate_id=candidate_id, **computed)
    db.add(score)
    db.commit()
    db.refresh(score)
    return score
