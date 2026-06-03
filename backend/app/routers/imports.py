import csv
import io
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.schemas.imports import ProductImportResponse

router = APIRouter(prefix='/api/import', tags=['imports'])


def to_decimal(value: str | None) -> Decimal | None:
    if not value:
        return None
    try:
        return Decimal(value)
    except Exception:
        return None


def to_bool(value: str | None) -> bool:
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y'}


def to_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except Exception:
        return None


def to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


@router.post('/products', response_model=ProductImportResponse)
async def import_products(file: UploadFile = File(...), db: Session = Depends(get_db)) -> ProductImportResponse:
    content = await file.read()
    text = content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))
    imported = 0
    skipped = 0

    for row in reader:
        title = row.get('title')
        if not title:
            skipped += 1
            continue

        product = Product(
            es_number=row.get('es_number'),
            title=title,
            normalized_title=row.get('normalized_title'),
            brand=row.get('brand'),
            model=row.get('model'),
            category=row.get('category'),
            mount=row.get('mount'),
            condition_rank=row.get('condition_rank'),
            purchase_price_jpy=to_decimal(row.get('purchase_price_jpy')),
            sale_price_usd=to_decimal(row.get('sale_price_usd')),
            sale_price_jpy=to_decimal(row.get('sale_price_jpy')),
            gross_profit_jpy=to_decimal(row.get('gross_profit_jpy')),
            final_profit_jpy=to_decimal(row.get('final_profit_jpy')),
            profit_margin=to_decimal(row.get('profit_margin')),
            purchased_at=to_datetime(row.get('purchased_at')),
            listed_at=to_datetime(row.get('listed_at')),
            sold_at=to_datetime(row.get('sold_at')),
            days_to_sell=to_int(row.get('days_to_sell')),
            sales_channel=row.get('sales_channel'),
            buyer_country=row.get('buyer_country'),
            returned=to_bool(row.get('returned')),
            complaint=to_bool(row.get('complaint')),
            repair_required=to_bool(row.get('repair_required')),
            seller_id=row.get('seller_id'),
            source_platform=row.get('source_platform'),
            source_url=row.get('source_url'),
            notes=row.get('notes'),
        )
        db.add(product)
        imported += 1

    db.commit()
    return ProductImportResponse(imported_count=imported, skipped_count=skipped)
