from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.sales import PaymentMethod


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class SaleCreate(BaseModel):
    items: list[SaleItemCreate] = Field(min_length=1)
    payment_method: PaymentMethod
    discount_amount: Decimal = Field(default=0, ge=0, decimal_places=2)
    customer_name: str | None = Field(default=None, max_length=160)
    customer_phone: str | None = Field(default=None, max_length=40)


class SaleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    total_amount: Decimal
    payment_method: PaymentMethod
    customer_name: str | None = None
    customer_phone: str | None = None
    created_at: datetime
    items: list[SaleItemResponse]
