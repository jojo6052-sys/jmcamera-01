from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feedback import Feedback
from app.models.yahoo_candidate import YahooAuctionCandidate
from app.schemas.feedbacks import FeedbackBatchCreate, FeedbackCreate, FeedbackRead

router = APIRouter(prefix='/api/candidates', tags=['feedbacks'])

CANDIDATE_STATUS_BY_DECISION = {
    'purchase': 'purchase',
    'review': 'review',
    'skip': 'skip',
}


def build_feedback(candidate_id: int, payload: FeedbackCreate | FeedbackBatchCreate) -> Feedback:
    return Feedback(
        candidate_id=candidate_id,
        user_decision=payload.user_decision,
        purchased=getattr(payload, 'purchased', False),
        actual_purchase_price_jpy=getattr(payload, 'actual_purchase_price_jpy', None),
        actual_condition=getattr(payload, 'actual_condition', None),
        inspection_result=getattr(payload, 'inspection_result', None),
        sold=getattr(payload, 'sold', False),
        actual_sale_price_jpy=getattr(payload, 'actual_sale_price_jpy', None),
        actual_profit_jpy=getattr(payload, 'actual_profit_jpy', None),
        returned=getattr(payload, 'returned', False),
        complaint=getattr(payload, 'complaint', False),
        repair_required=getattr(payload, 'repair_required', False),
        ai_prediction_was_correct=getattr(payload, 'ai_prediction_was_correct', None),
        notes=payload.notes,
    )


@router.post('/feedback-batch', response_model=list[FeedbackRead])
def create_feedback_batch(payload: FeedbackBatchCreate, db: Session = Depends(get_db)):
    candidates = (
        db.query(YahooAuctionCandidate)
        .filter(YahooAuctionCandidate.id.in_(payload.candidate_ids))
        .all()
    )
    candidates_by_id = {candidate.id: candidate for candidate in candidates}
    missing_ids = [candidate_id for candidate_id in payload.candidate_ids if candidate_id not in candidates_by_id]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f'candidates not found: {missing_ids}')

    feedbacks: list[Feedback] = []
    for candidate_id in payload.candidate_ids:
        candidate = candidates_by_id[candidate_id]
        feedback = build_feedback(candidate_id, payload)
        candidate.status = CANDIDATE_STATUS_BY_DECISION[payload.user_decision]
        db.add(feedback)
        feedbacks.append(feedback)

    db.commit()
    for feedback in feedbacks:
        db.refresh(feedback)
    return feedbacks


@router.post('/{candidate_id}/feedback', response_model=FeedbackRead)
def create_feedback(candidate_id: int, payload: FeedbackCreate, db: Session = Depends(get_db)):
    candidate = db.get(YahooAuctionCandidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail='candidate not found')

    feedback = build_feedback(candidate_id, payload)
    candidate.status = CANDIDATE_STATUS_BY_DECISION.get(payload.user_decision, candidate.status)

    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
