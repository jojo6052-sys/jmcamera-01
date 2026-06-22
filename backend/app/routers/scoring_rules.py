from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.scoring_rule import ScoringRule
from app.schemas.scoring_rules import ScoringRuleCreate, ScoringRuleRead, ScoringRuleUpdate

router = APIRouter(prefix='/api/scoring-rules', tags=['scoring-rules'])


@router.get('', response_model=list[ScoringRuleRead])
def list_scoring_rules(db: Session = Depends(get_db), enabled: bool | None = None):
    q = db.query(ScoringRule).order_by(ScoringRule.enabled.desc(), ScoringRule.id.desc())
    if enabled is not None:
        q = q.filter(ScoringRule.enabled == enabled)
    return q.limit(200).all()


@router.post('', response_model=ScoringRuleRead)
def create_scoring_rule(payload: ScoringRuleCreate, db: Session = Depends(get_db)):
    rule = ScoringRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch('/{rule_id}', response_model=ScoringRuleRead)
def update_scoring_rule(rule_id: int, payload: ScoringRuleUpdate, db: Session = Depends(get_db)):
    rule = db.get(ScoringRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail='scoring rule not found')

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)

    db.commit()
    db.refresh(rule)
    return rule


@router.delete('/{rule_id}', status_code=204)
def delete_scoring_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(ScoringRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail='scoring rule not found')

    db.delete(rule)
    db.commit()
    return None
