from decimal import Decimal

from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_revenue: Decimal
    total_sales_count: int
    low_stock_item_count: int
    total_products: int


class SalesTrendPoint(BaseModel):
    date: str
    revenue: Decimal


class TopProductPoint(BaseModel):
    product_id: int
    product_name: str
    quantity_sold: int


class CategoryBreakdownPoint(BaseModel):
    category_name: str
    revenue: Decimal
