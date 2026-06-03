from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.search_keyword import SearchKeyword
from app.schemas.keywords import SearchKeywordCreate, SearchKeywordRead, SearchKeywordUpdate

router = APIRouter(prefix='/api/search-keywords', tags=['search-keywords'])


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def ensure_keyword_is_available(db: Session, keyword: str, *, current_id: int | None = None) -> None:
    existing = db.query(SearchKeyword).filter(SearchKeyword.keyword == keyword).first()
    if existing and existing.id != current_id:
        raise HTTPException(status_code=409, detail='search keyword already exists')


@router.get('', response_model=list[SearchKeywordRead])
def list_keywords(db: Session = Depends(get_db)):
    return db.query(SearchKeyword).order_by(SearchKeyword.priority.asc(), SearchKeyword.id.desc()).all()


@router.post('', response_model=SearchKeywordRead)
def create_keyword(payload: SearchKeywordCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    keyword = normalize_text(data.get('keyword'))
    if not keyword:
        raise HTTPException(status_code=422, detail='keyword is required')

    data['keyword'] = keyword
    data['category'] = normalize_text(data.get('category'))
    data['brand'] = normalize_text(data.get('brand'))
    data['model_group'] = normalize_text(data.get('model_group'))
    ensure_keyword_is_available(db, keyword)

    entity = SearchKeyword(**data)
    db.add(entity)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail='search keyword already exists') from exc
    db.refresh(entity)
    return entity


@router.put('/{keyword_id}', response_model=SearchKeywordRead)
def update_keyword(keyword_id: int, payload: SearchKeywordUpdate, db: Session = Depends(get_db)):
    entity = db.get(SearchKeyword, keyword_id)
    if not entity:
        raise HTTPException(status_code=404, detail='keyword not found')
    data = payload.model_dump(exclude_unset=True)
    if 'keyword' in data:
        keyword = normalize_text(data.get('keyword'))
        if not keyword:
            raise HTTPException(status_code=422, detail='keyword is required')
        ensure_keyword_is_available(db, keyword, current_id=keyword_id)
        data['keyword'] = keyword

    for key in ('category', 'brand', 'model_group'):
        if key in data:
            data[key] = normalize_text(data.get(key))

    for k, v in data.items():
        setattr(entity, k, v)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail='search keyword already exists') from exc
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
