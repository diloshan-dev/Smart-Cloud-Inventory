from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.dependencies import DbSession, get_current_user, require_admin
from app.models.inventory import Category, Product
from app.schemas.inventory import (
    CategoryCreate,
    CategoryResponse,
    ProductCreate,
    ProductResponse,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: DbSession) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)).all())


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_category(payload: CategoryCreate, db: DbSession) -> Category:
    if db.scalar(select(Category).where(Category.name == payload.name.strip())):
        raise HTTPException(status_code=409, detail="Category name is already in use")
    category = Category(name=payload.name.strip(), description=payload.description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse, dependencies=[Depends(require_admin)])
def update_category(category_id: int, payload: CategoryCreate, db: DbSession) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    duplicate = db.scalar(select(Category).where(Category.name == payload.name.strip(), Category.id != category_id))
    if duplicate:
        raise HTTPException(status_code=409, detail="Category name is already in use")
    category.name = payload.name.strip()
    category.description = payload.description
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_category(category_id: int, db: DbSession) -> None:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    if db.scalar(select(Product.id).where(Product.category_id == category_id)):
        raise HTTPException(status_code=409, detail="Category still has products")
    db.delete(category)
    db.commit()


def _product_query(search: str | None, category_id: int | None, low_stock: bool = False):
    query = select(Product)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(or_(Product.name.ilike(term), Product.sku.ilike(term), Product.barcode.ilike(term)))
    if category_id is not None:
        query = query.where(Product.category_id == category_id)
    if low_stock:
        query = query.where(Product.stock_quantity <= Product.min_stock_level)
    return query.order_by(Product.name)


@router.get("/products", response_model=list[ProductResponse])
def list_products(
    db: DbSession,
    search: str | None = None,
    category_id: int | None = None,
) -> list[Product]:
    return list(db.scalars(_product_query(search, category_id)).all())


@router.get("/products/low-stock", response_model=list[ProductResponse])
def list_low_stock(db: DbSession) -> list[Product]:
    return list(db.scalars(_product_query(None, None, low_stock=True)).all())


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_product(payload: ProductCreate, db: DbSession) -> Product:
    if db.scalar(select(Product).where(Product.sku == payload.sku.strip())):
        raise HTTPException(status_code=409, detail="SKU is already in use")
    if payload.barcode and db.scalar(select(Product).where(Product.barcode == payload.barcode.strip())):
        raise HTTPException(status_code=409, detail="Barcode is already in use")
    if payload.category_id is not None and db.get(Category, payload.category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found")
    product = Product(**payload.model_dump())
    product.sku = payload.sku.strip()
    product.barcode = payload.barcode.strip() if payload.barcode else None
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductResponse, dependencies=[Depends(require_admin)])
def update_product(product_id: int, payload: ProductCreate, db: DbSession) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if db.scalar(select(Product).where(Product.sku == payload.sku.strip(), Product.id != product_id)):
        raise HTTPException(status_code=409, detail="SKU is already in use")
    if payload.barcode and db.scalar(select(Product).where(Product.barcode == payload.barcode.strip(), Product.id != product_id)):
        raise HTTPException(status_code=409, detail="Barcode is already in use")
    if payload.category_id is not None and db.get(Category, payload.category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    product.sku = payload.sku.strip()
    product.barcode = payload.barcode.strip() if payload.barcode else None
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: DbSession) -> None:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
