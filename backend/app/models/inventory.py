from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    sku: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    barcode: Mapped[str] = mapped_column(String(80), unique=True, nullable=True, index=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=True)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    stock_quantity: Mapped[int] = mapped_column(default=0, nullable=False)
    min_stock_level: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    category = relationship("Category", back_populates="products")
