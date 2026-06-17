import csv
import io
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.competitor import CompetitorItem, CompetitorSeller
from app.models.search_keyword import SearchKeyword
from app.schemas.competitors import CompetitorAnalyzeRequest, CompetitorAnalyzeResponse, CompetitorInsights, CompetitorItemRead, CompetitorKeywordBulkCreate, CompetitorKeywordCreate, CompetitorKeywordSuggestion, CompetitorSellerRead, CompetitorTopTerm
from app.schemas.keywords import SearchKeywordRead
from app.services.ebay_research import CompetitorItemPayload, EbayFetchBlockedError, build_ebay_seller_search_url, extract_ebay_seller_username, fetch_competitor_items, _parse_ebay_items
from app.utils.time import utc_now

router = APIRouter(prefix="/api/competitors", tags=["competitors"])


@router.post("/analyze", response_model=CompetitorAnalyzeResponse)
def analyze_competitor(payload: CompetitorAnalyzeRequest, db: Session = Depends(get_db)) -> CompetitorAnalyzeResponse:
    seller_url = str(payload.seller_url)
    try:
        seller_username, fetched_items = fetch_competitor_items(
            seller_url,
            include_active=payload.include_active,
            include_sold=payload.include_sold,
            limit=payload.limit,
        )
        fetch_status = "ok"
        last_error = None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        try:
            seller_username = extract_ebay_seller_username(seller_url)
        except ValueError as parse_exc:
            raise HTTPException(status_code=422, detail=str(parse_exc)) from parse_exc
        fetched_items = []
        fetch_status = "blocked" if isinstance(exc, EbayFetchBlockedError) else "failed"
        last_error = str(exc) if isinstance(exc, EbayFetchBlockedError) else f"{exc.__class__.__name__}: {exc}"

    seller = upsert_competitor_seller(
        db,
        seller_username=seller_username,
        seller_url=seller_url,
        fetch_status=fetch_status,
        last_error=last_error,
    )
    items = upsert_competitor_items(db, seller=seller, payloads=fetched_items)
    refresh_competitor_summary(db, seller)
    db.commit()
    db.refresh(seller)
    for item in items:
        db.refresh(item)

    return CompetitorAnalyzeResponse(seller=seller, items=items)


@router.post("/import-html", response_model=CompetitorAnalyzeResponse)
async def import_competitor_html(
    seller_url: str = Form(...),
    item_status: str = Form(..., pattern="^(active|sold)$"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CompetitorAnalyzeResponse:
    try:
        seller_username = extract_ebay_seller_username(seller_url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    raw = await file.read()
    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError:
        html = raw.decode("utf-8", errors="ignore")

    source_url = build_ebay_seller_search_url(seller_username, item_status)
    fetched_items = _parse_ebay_items(html, source_url=source_url, item_status=item_status, limit=100)
    seller = upsert_competitor_seller(
        db,
        seller_username=seller_username,
        seller_url=seller_url,
        fetch_status="imported",
        last_error=None,
    )
    items = upsert_competitor_items(db, seller=seller, payloads=fetched_items)
    refresh_competitor_summary(db, seller)
    db.commit()
    db.refresh(seller)
    for item in items:
        db.refresh(item)

    return CompetitorAnalyzeResponse(seller=seller, items=items)


@router.get("", response_model=list[CompetitorSellerRead])
def list_competitor_sellers(db: Session = Depends(get_db)) -> list[CompetitorSeller]:
    return db.query(CompetitorSeller).order_by(CompetitorSeller.updated_at.desc()).limit(100).all()


@router.get("/{seller_id}/insights", response_model=CompetitorInsights)
def get_competitor_insights(seller_id: int, db: Session = Depends(get_db)) -> CompetitorInsights:
    seller = db.get(CompetitorSeller, seller_id)
    if seller is None:
        raise HTTPException(status_code=404, detail="competitor seller not found")

    refresh_competitor_summary(db, seller)
    total_count = seller.active_count + seller.sold_count
    sell_through_rate = round((seller.sold_count / total_count) * 100, 1) if total_count else None
    sold_active_price_gap = None
    if seller.avg_sold_price is not None and seller.avg_active_price is not None:
        sold_active_price_gap = float((seller.avg_sold_price - seller.avg_active_price).quantize(Decimal("0.01")))

    return CompetitorInsights(
        seller_id=seller.id,
        seller_username=seller.seller_username,
        active_count=seller.active_count,
        sold_count=seller.sold_count,
        sell_through_rate=sell_through_rate,
        avg_active_price=float(seller.avg_active_price) if seller.avg_active_price is not None else None,
        avg_sold_price=float(seller.avg_sold_price) if seller.avg_sold_price is not None else None,
        sold_active_price_gap=sold_active_price_gap,
        top_sold_terms=_top_sold_terms(db, seller.id),
        suggested_keywords=_suggested_sold_keywords(db, seller.id),
    )


@router.post("/{seller_id}/keywords", response_model=SearchKeywordRead)
def create_keyword_from_competitor(
    seller_id: int,
    payload: CompetitorKeywordCreate,
    db: Session = Depends(get_db),
) -> SearchKeyword:
    _get_competitor_seller_or_404(db, seller_id)
    return _get_or_create_search_keyword(
        db,
        keyword=payload.keyword,
        category=payload.category,
        brand=payload.brand,
        model_group=payload.model_group,
        priority=payload.priority,
        active=payload.active,
    )


@router.post("/{seller_id}/keywords/bulk", response_model=list[SearchKeywordRead])
def bulk_create_keywords_from_competitor(
    seller_id: int,
    payload: CompetitorKeywordBulkCreate,
    db: Session = Depends(get_db),
) -> list[SearchKeyword]:
    _get_competitor_seller_or_404(db, seller_id)
    keywords = payload.keywords or [item.keyword for item in _suggested_sold_keywords(db, seller_id)]
    normalized_keywords = _dedupe_keywords(keywords)
    if not normalized_keywords:
        raise HTTPException(status_code=422, detail="at least one keyword is required")

    return [
        _get_or_create_search_keyword(
            db,
            keyword=keyword,
            category=payload.category,
            brand=payload.brand,
            model_group=payload.model_group,
            priority=payload.priority,
            active=payload.active,
        )
        for keyword in normalized_keywords
    ]


@router.get("/{seller_id}/export.csv")
def export_competitor_items_csv(
    seller_id: int,
    db: Session = Depends(get_db),
    item_status: str | None = Query(default=None, pattern="^(active|sold)$"),
    keyword: str | None = None,
):
    seller = db.get(CompetitorSeller, seller_id)
    if seller is None:
        raise HTTPException(status_code=404, detail="competitor seller not found")

    rows = _competitor_items_query(db, seller_id=seller_id, item_status=item_status, keyword=keyword).limit(1000).all()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "seller_username",
        "item_status",
        "title",
        "price",
        "currency",
        "item_url",
        "image_url",
        "external_item_id",
        "source_url",
        "first_seen_at",
        "last_seen_at",
    ])
    for item in rows:
        writer.writerow([
            seller.seller_username,
            item.item_status,
            item.title,
            item.price,
            item.currency,
            item.item_url,
            item.image_url,
            item.external_item_id,
            item.source_url,
            item.first_seen_at.isoformat() if item.first_seen_at else None,
            item.last_seen_at.isoformat() if item.last_seen_at else None,
        ])

    out.seek(0)
    filename = f"competitor-{seller.seller_username}-items.csv"
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{seller_id}/items", response_model=list[CompetitorItemRead])
def list_competitor_items(
    seller_id: int,
    db: Session = Depends(get_db),
    item_status: str | None = Query(default=None, pattern="^(active|sold)$"),
    keyword: str | None = None,
) -> list[CompetitorItem]:
    return _competitor_items_query(db, seller_id=seller_id, item_status=item_status, keyword=keyword).limit(200).all()


def _competitor_items_query(db: Session, *, seller_id: int, item_status: str | None, keyword: str | None):
    q = db.query(CompetitorItem).filter(CompetitorItem.seller_id == seller_id)
    if item_status:
        q = q.filter(CompetitorItem.item_status == item_status)
    if keyword:
        q = q.filter(CompetitorItem.title.ilike(f"%{keyword.strip()}%"))
    return q.order_by(CompetitorItem.last_seen_at.desc())


def _get_competitor_seller_or_404(db: Session, seller_id: int) -> CompetitorSeller:
    seller = db.get(CompetitorSeller, seller_id)
    if seller is None:
        raise HTTPException(status_code=404, detail="competitor seller not found")
    return seller


def _dedupe_keywords(keywords: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for keyword in keywords:
        value = keyword.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def _get_or_create_search_keyword(
    db: Session,
    *,
    keyword: str,
    category: str | None,
    brand: str | None,
    model_group: str | None,
    priority: int,
    active: bool,
) -> SearchKeyword:
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        raise HTTPException(status_code=422, detail="keyword is required")

    existing = db.query(SearchKeyword).filter(SearchKeyword.keyword == normalized_keyword).one_or_none()
    if existing is not None:
        return existing

    entity = SearchKeyword(
        keyword=normalized_keyword,
        category=(category.strip() if category else None),
        brand=(brand.strip() if brand else None),
        model_group=(model_group.strip() if model_group else None),
        priority=priority,
        active=active,
    )
    db.add(entity)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing = db.query(SearchKeyword).filter(SearchKeyword.keyword == normalized_keyword).one_or_none()
        if existing is not None:
            return existing
        raise HTTPException(status_code=409, detail="search keyword already exists") from exc
    db.refresh(entity)
    return entity


def _sold_title_tokens(db: Session, seller_id: int) -> list[list[str]]:
    stopwords = {
        "with",
        "from",
        "for",
        "the",
        "and",
        "body",
        "camera",
        "lens",
        "mint",
        "near",
        "excellent",
        "working",
        "tested",
        "japan",
    }
    rows = (
        db.query(CompetitorItem.normalized_title)
        .filter(CompetitorItem.seller_id == seller_id, CompetitorItem.item_status == "sold")
        .all()
    )
    tokenized: list[list[str]] = []
    for (title,) in rows:
        tokens: list[str] = []
        for raw_term in (title or "").split():
            term = raw_term.strip(".,:/()[]{}+_-'\"").lower()
            has_letter = any(char.isalpha() for char in term)
            has_digit = any(char.isdigit() for char in term)
            if term in stopwords or term.isdigit() or (len(term) < 3 and not (has_letter and has_digit)):
                continue
            tokens.append(term)
        if tokens:
            tokenized.append(tokens)
    return tokenized


def _suggested_sold_keywords(db: Session, seller_id: int) -> list[CompetitorKeywordSuggestion]:
    counts: dict[str, int] = {}
    for tokens in _sold_title_tokens(db, seller_id):
        seen: set[str] = set()
        for index in range(len(tokens) - 1):
            keyword = f"{tokens[index]} {tokens[index + 1]}"
            seen.add(keyword)
        if len(tokens) >= 2:
            seen.add(" ".join(tokens[:3] if len(tokens) >= 3 else tokens))
        for keyword in seen:
            counts[keyword] = counts.get(keyword, 0) + 1
    return [
        CompetitorKeywordSuggestion(keyword=keyword, count=count)
        for keyword, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10]
    ]


def _top_sold_terms(db: Session, seller_id: int) -> list[CompetitorTopTerm]:
    counts: dict[str, int] = {}
    for tokens in _sold_title_tokens(db, seller_id):
        for term in tokens:
            counts[term] = counts.get(term, 0) + 1
    return [
        CompetitorTopTerm(term=term, count=count)
        for term, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10]
    ]


def upsert_competitor_seller(
    db: Session,
    *,
    seller_username: str,
    seller_url: str,
    fetch_status: str,
    last_error: str | None,
) -> CompetitorSeller:
    seller = (
        db.query(CompetitorSeller)
        .filter(
            CompetitorSeller.marketplace == "ebay",
            CompetitorSeller.seller_username == seller_username,
        )
        .one_or_none()
    )
    now = utc_now()
    if seller is None:
        seller = CompetitorSeller(
            marketplace="ebay",
            seller_username=seller_username,
            seller_url=seller_url,
            fetch_status=fetch_status,
            last_error=last_error,
            last_analyzed_at=now,
        )
        db.add(seller)
        db.flush()
        return seller

    seller.seller_url = seller_url
    seller.fetch_status = fetch_status
    seller.last_error = last_error
    seller.last_analyzed_at = now
    return seller


def upsert_competitor_items(db: Session, *, seller: CompetitorSeller, payloads: list[CompetitorItemPayload]) -> list[CompetitorItem]:
    rows: list[CompetitorItem] = []
    now = utc_now()
    for payload in payloads:
        row = (
            db.query(CompetitorItem)
            .filter(
                CompetitorItem.seller_id == seller.id,
                CompetitorItem.external_item_id == payload.external_item_id,
                CompetitorItem.item_status == payload.item_status,
            )
            .one_or_none()
        )
        if row is None:
            row = CompetitorItem(
                seller_id=seller.id,
                marketplace="ebay",
                external_item_id=payload.external_item_id,
                title=payload.title,
                normalized_title=payload.normalized_title,
                item_url=payload.item_url,
                image_url=payload.image_url,
                price=payload.price,
                currency=payload.currency,
                item_status=payload.item_status,
                source_url=payload.source_url,
                raw=payload.raw,
                first_seen_at=now,
                last_seen_at=now,
            )
            db.add(row)
        else:
            row.title = payload.title
            row.normalized_title = payload.normalized_title
            row.item_url = payload.item_url
            row.image_url = payload.image_url
            row.price = payload.price
            row.currency = payload.currency
            row.source_url = payload.source_url
            row.raw = payload.raw
            row.last_seen_at = now
        rows.append(row)
    db.flush()
    return rows


def refresh_competitor_summary(db: Session, seller: CompetitorSeller) -> None:
    active = _status_summary(db, seller.id, "active")
    sold = _status_summary(db, seller.id, "sold")
    seller.active_count = active[0]
    seller.avg_active_price = active[1]
    seller.sold_count = sold[0]
    seller.avg_sold_price = sold[1]


def _status_summary(db: Session, seller_id: int, item_status: str) -> tuple[int, Decimal | None]:
    count, avg_price = (
        db.query(func.count(CompetitorItem.id), func.avg(CompetitorItem.price))
        .filter(CompetitorItem.seller_id == seller_id, CompetitorItem.item_status == item_status)
        .one()
    )
    return int(count or 0), Decimal(str(avg_price)).quantize(Decimal("0.01")) if avg_price is not None else None
