from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.competitor import CompetitorItem, CompetitorSeller
from app.schemas.competitors import CompetitorAnalyzeRequest, CompetitorAnalyzeResponse, CompetitorItemRead, CompetitorSellerRead
from app.services.ebay_research import CompetitorItemPayload, EbayFetchBlockedError, extract_ebay_seller_username, fetch_competitor_items

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


@router.get("", response_model=list[CompetitorSellerRead])
def list_competitor_sellers(db: Session = Depends(get_db)) -> list[CompetitorSeller]:
    return db.query(CompetitorSeller).order_by(CompetitorSeller.updated_at.desc()).limit(100).all()


@router.get("/{seller_id}/items", response_model=list[CompetitorItemRead])
def list_competitor_items(
    seller_id: int,
    db: Session = Depends(get_db),
    item_status: str | None = Query(default=None, pattern="^(active|sold)$"),
    keyword: str | None = None,
) -> list[CompetitorItem]:
    q = db.query(CompetitorItem).filter(CompetitorItem.seller_id == seller_id)
    if item_status:
        q = q.filter(CompetitorItem.item_status == item_status)
    if keyword:
        q = q.filter(CompetitorItem.title.ilike(f"%{keyword.strip()}%"))
    return q.order_by(CompetitorItem.last_seen_at.desc()).limit(200).all()


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
    now = datetime.utcnow()
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
    now = datetime.utcnow()
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
