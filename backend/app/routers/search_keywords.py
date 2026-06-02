from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.search_keyword import SearchKeyword
from app.schemas.keywords import SearchKeywordCreate, SearchKeywordRead, SearchKeywordUpdate

router = APIRouter(prefix='/api/search-keywords', tags=['search-keywords'])


@router.get('', response_model=list[SearchKeywordRead])
def list_keywords(db: Session = Depends(get_db)):
    return db.query(SearchKeyword).order_by(SearchKeyword.priority.asc(), SearchKeyword.id.desc()).all()


@router.post('', response_model=SearchKeywordRead)
def create_keyword(payload: SearchKeywordCreate, db: Session = Depends(get_db)):
    entity = SearchKeyword(**payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@router.put('/{keyword_id}', response_model=SearchKeywordRead)
def update_keyword(keyword_id: int, payload: SearchKeywordUpdate, db: Session = Depends(get_db)):
    entity = db.get(SearchKeyword, keyword_id)
    if not entity:
        raise HTTPException(status_code=404, detail='keyword not found')
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(entity, k, v)
    db.commit()
    db.refresh(entity)
    return entity


@router.delete('/{keyword_id}')
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    entity = db.get(SearchKeyword, keyword_id)
    if not entity:
        raise HTTPException(status_code=404, detail='keyword not found')
    db.delete(entity)
    db.commit()
    return {'deleted': True}
