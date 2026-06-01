from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feedback import Feedback
from app.models.yahoo_candidate import YahooAuctionCandidate
from app.schemas.feedbacks import FeedbackCreate, FeedbackRead

router = APIRouter(prefix='/api/candidates', tags=['feedbacks'])


@router.post('/{candidate_id}/feedback', response_model=FeedbackRead)
def create_feedback(candidate_id: int, payload: FeedbackCreate, db: Session = Depends(get_db)):
    candidate = db.get(YahooAuctionCandidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail='candidate not found')

    feedback = Feedback(
        candidate_id=candidate_id,
        user_decision=payload.user_decision,
        purchased=payload.purchased,
        actual_purchase_price_jpy=payload.actual_purchase_price_jpy,
        actual_condition=payload.actual_condition,
        inspection_result=payload.inspection_result,
        sold=payload.sold,
        actual_sale_price_jpy=payload.actual_sale_price_jpy,
        actual_profit_jpy=payload.actual_profit_jpy,
        returned=payload.returned,
        complaint=payload.complaint,
        repair_required=payload.repair_required,
        ai_prediction_was_correct=payload.ai_prediction_was_correct,
        notes=payload.notes,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
