import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.recommendation_score import RecommendationScore
from app.models.yahoo_candidate import YahooAuctionCandidate
from app.schemas.candidates import CandidateBulkScoreRequest, CandidateRead
from app.schemas.scores import RecommendationScoreRead
from app.services.scoring import compute_recommendation

router = APIRouter(prefix='/api/candidates', tags=['candidates'])


def attach_latest_scores(db: Session, candidates: list[YahooAuctionCandidate]) -> list[YahooAuctionCandidate]:
    candidate_ids = [candidate.id for candidate in candidates]
    if not candidate_ids:
        return candidates

    score_rows = (
        db.query(RecommendationScore)
        .filter(RecommendationScore.candidate_id.in_(candidate_ids))
        .order_by(RecommendationScore.candidate_id.asc(), RecommendationScore.id.desc())
        .all()
    )
    latest_by_candidate_id: dict[int, RecommendationScore] = {}
    for score in score_rows:
        latest_by_candidate_id.setdefault(score.candidate_id, score)

    for candidate in candidates:
        score = latest_by_candidate_id.get(candidate.id)
        candidate.latest_score = score
        candidate.latest_total_score = float(score.total_score) if score and score.total_score is not None else None
        candidate.latest_rank = score.rank if score else None

    return candidates


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
        keyword_pattern = f"%{keyword.strip()}%"
        q = q.filter(
            or_(
                YahooAuctionCandidate.search_keyword.ilike(keyword_pattern),
                YahooAuctionCandidate.title.ilike(keyword_pattern),
                YahooAuctionCandidate.normalized_title.ilike(keyword_pattern),
            )
        )
    if max_price is not None:
        q = q.filter(YahooAuctionCandidate.current_price_jpy <= max_price)
    if seller_id:
        q = q.filter(YahooAuctionCandidate.seller_id == seller_id)
    if status:
        q = q.filter(YahooAuctionCandidate.status == status)

    if rank or min_score is not None:
        latest_score_ids = db.query(func.max(RecommendationScore.id)).group_by(RecommendationScore.candidate_id)
        score_q = (
            db.query(RecommendationScore.candidate_id)
            .filter(RecommendationScore.id.in_(latest_score_ids))
        )
        if rank:
            score_q = score_q.filter(RecommendationScore.rank == rank)
        if min_score is not None:
            score_q = score_q.filter(RecommendationScore.total_score >= min_score)
        q = q.filter(YahooAuctionCandidate.id.in_(score_q))

    candidates = q.order_by(YahooAuctionCandidate.created_at.desc()).limit(200).all()
    return attach_latest_scores(db, candidates)


def upsert_recommendation_score(db: Session, candidate: YahooAuctionCandidate) -> RecommendationScore:
    computed = compute_recommendation(candidate)

    score = (
        db.query(RecommendationScore)
        .filter(RecommendationScore.candidate_id == candidate.id)
        .order_by(RecommendationScore.id.desc())
        .first()
    )

    if score is None:
        score = RecommendationScore(candidate_id=candidate.id, **computed)
        db.add(score)
    else:
        for key, value in computed.items():
            setattr(score, key, value)

    return score


@router.get('/export.csv')
def export_candidates_csv(
    db: Session = Depends(get_db),
    keyword: str | None = None,
    rank: str | None = None,
    min_score: float | None = Query(default=None),
    max_price: float | None = Query(default=None),
    seller_id: str | None = None,
    status: str | None = None,
):
    rows = list_candidates(db, keyword=keyword, rank=rank, min_score=min_score, max_price=max_price, seller_id=seller_id, status=status)

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        'id', 'auction_id', 'title', 'url', 'current_price_jpy', 'buyout_price_jpy',
        'bid_count', 'end_time', 'seller_id', 'seller_rating', 'search_keyword', 'status', 'latest_total_score', 'latest_rank',
    ])
    for c in rows:
        writer.writerow([
            c.id,
            c.auction_id,
            c.title,
            c.url,
            c.current_price_jpy,
            c.buyout_price_jpy,
            c.bid_count,
            c.end_time,
            c.seller_id,
            c.seller_rating,
            c.search_keyword,
            c.status,
            c.latest_total_score,
            c.latest_rank,
        ])

    out.seek(0)
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=candidates.csv'},
    )


@router.post('/score-batch', response_model=list[RecommendationScoreRead])
def score_candidates_batch(payload: CandidateBulkScoreRequest, db: Session = Depends(get_db)):
    candidates = (
        db.query(YahooAuctionCandidate)
        .filter(YahooAuctionCandidate.id.in_(payload.candidate_ids))
        .all()
    )
    candidates_by_id = {candidate.id: candidate for candidate in candidates}
    missing_ids = [candidate_id for candidate_id in payload.candidate_ids if candidate_id not in candidates_by_id]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f'candidates not found: {missing_ids}')

    scores = [upsert_recommendation_score(db, candidates_by_id[candidate_id]) for candidate_id in payload.candidate_ids]
    db.commit()
    for score in scores:
        db.refresh(score)
    return scores


@router.get('/{candidate_id}', response_model=CandidateRead)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    entity = db.get(YahooAuctionCandidate, candidate_id)
    if not entity:
        raise HTTPException(status_code=404, detail='candidate not found')
    return attach_latest_scores(db, [entity])[0]


@router.post('/{candidate_id}/score', response_model=RecommendationScoreRead)
def score_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(YahooAuctionCandidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail='candidate not found')

    score = upsert_recommendation_score(db, candidate)
    db.commit()
    db.refresh(score)
    return score
