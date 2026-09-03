from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select

from app.api.dependencies import DbSession, get_current_user
from app.models.inventory import Category, Product
from app.models.sales import Sale, SaleItem
from app.schemas.analytics import (
    AnalyticsSummary,
    CategoryBreakdownPoint,
    SalesTrendPoint,
    TopProductPoint,
)

router = APIRouter(prefix="/analytics", dependencies=[Depends(get_current_user)])


@router.get("/summary", response_model=AnalyticsSummary)
def summary(db: DbSession) -> AnalyticsSummary:
    revenue = db.scalar(select(func.coalesce(func.sum(Sale.total_amount), 0))) or 0
    return AnalyticsSummary(
        total_revenue=Decimal(str(revenue)),
        total_sales_count=db.scalar(select(func.count(Sale.id))) or 0,
        low_stock_item_count=db.scalar(
            select(func.count(Product.id)).where(Product.stock_quantity <= Product.min_stock_level)
        ) or 0,
        total_products=db.scalar(select(func.count(Product.id))) or 0,
    )


@router.get("/sales-trend", response_model=list[SalesTrendPoint])
def sales_trend(
    db: DbSession,
    days: int = Query(default=7, ge=1, le=90),
) -> list[SalesTrendPoint]:
    start = date.today() - timedelta(days=days - 1)
    sale_date = func.date(Sale.created_at)
    rows = db.execute(
        select(sale_date.label("date"), func.sum(Sale.total_amount).label("revenue"))
        .where(Sale.created_at >= start)
        .group_by(sale_date)
        .order_by(sale_date)
    ).all()
    values = {str(row.date): Decimal(str(row.revenue)) for row in rows}
    return [
        SalesTrendPoint(date=str(start + timedelta(days=offset)), revenue=values.get(str(start + timedelta(days=offset)), Decimal("0")))
        for offset in range(days)
    ]


@router.get("/top-products", response_model=list[TopProductPoint])
def top_products(db: DbSession) -> list[TopProductPoint]:
    rows = db.execute(
        select(Product.id, Product.name, func.sum(SaleItem.quantity).label("quantity"))
        .join(SaleItem, SaleItem.product_id == Product.id)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(5)
    ).all()
    return [
        TopProductPoint(product_id=row.id, product_name=row.name, quantity_sold=row.quantity)
        for row in rows
    ]


@router.get("/category-breakdown", response_model=list[CategoryBreakdownPoint])
def category_breakdown(db: DbSession) -> list[CategoryBreakdownPoint]:
    category_name = func.coalesce(Category.name, "Uncategorized")
    rows = db.execute(
        select(category_name.label("category_name"), func.sum(SaleItem.subtotal).label("revenue"))
        .join(Product, Product.id == SaleItem.product_id)
        .outerjoin(Category, Category.id == Product.category_id)
        .group_by(category_name)
        .order_by(func.sum(SaleItem.subtotal).desc())
    ).all()
    return [
        CategoryBreakdownPoint(category_name=row.category_name, revenue=Decimal(str(row.revenue)))
        for row in rows
    ]
