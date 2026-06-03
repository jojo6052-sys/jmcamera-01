from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.schemas.analytics import BestSellerItem, CategoryAnalyticsItem

router = APIRouter(prefix='/api/analytics', tags=['analytics'])


@router.get('/best-sellers', response_model=list[BestSellerItem])
def best_sellers(db: Session = Depends(get_db)) -> list[BestSellerItem]:
    rows = (
        db.query(
            Product.title,
            func.count(Product.id).label('sales_count'),
            func.coalesce(func.sum(Product.sale_price_jpy), 0).label('total_sales_jpy'),
            func.coalesce(func.sum(Product.final_profit_jpy), 0).label('total_profit_jpy'),
            func.coalesce(func.avg(Product.profit_margin), 0).label('avg_profit_margin'),
            func.coalesce(func.avg(Product.days_to_sell), 0).label('avg_days_to_sell'),
        )
        .group_by(Product.title)
        .order_by(func.count(Product.id).desc())
        .limit(50)
        .all()
    )
    return [BestSellerItem(**row._asdict()) for row in rows]


@router.get('/categories', response_model=list[CategoryAnalyticsItem])
def category_analytics(db: Session = Depends(get_db)) -> list[CategoryAnalyticsItem]:
    rows = (
        db.query(
            func.coalesce(Product.category, 'Unknown').label('category'),
            func.coalesce(func.sum(Product.sale_price_jpy), 0).label('total_sales_jpy'),
            func.coalesce(func.sum(Product.final_profit_jpy), 0).label('total_profit_jpy'),
            func.coalesce(func.avg(Product.profit_margin), 0).label('avg_profit_margin'),
            func.coalesce(func.avg(Product.days_to_sell), 0).label('avg_days_to_sell'),
        )
        .group_by(Product.category)
        .order_by(func.sum(Product.final_profit_jpy).desc())
        .all()
    )
    return [CategoryAnalyticsItem(**row._asdict()) for row in rows]
