from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sku: str = Field(min_length=1, max_length=80)
    barcode: str | None = Field(default=None, max_length=80)
    image_url: str | None = Field(default=None, max_length=500)
    category_id: int | None = None
    purchase_price: Decimal = Field(default=0, ge=0, decimal_places=2)
    selling_price: Decimal = Field(default=0, ge=0, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)
    min_stock_level: int = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    category: CategoryResponse | None = None
