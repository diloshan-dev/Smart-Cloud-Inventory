from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.api.dependencies import DbSession, get_current_user, require_admin
from app.models.enterprise import AuditLog, Customer, Notification, PurchaseOrder, PurchaseOrderStatus, Supplier
from app.models.inventory import Product
from app.models.user import User

router = APIRouter(prefix="", dependencies=[Depends(get_current_user)])


class CustomerPayload(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: str | None = None
    phone: str | None = None
    notes: str | None = None


class SupplierPayload(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: str | None = None
    phone: str | None = None
    address: str | None = None


class PurchaseOrderPayload(BaseModel):
    supplier_id: int
    notes: str | None = None
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT


class StatusPayload(BaseModel):
    status: PurchaseOrderStatus


class ReadPayload(BaseModel):
    read: bool = True


class CustomerResponse(CustomerPayload):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class SupplierResponse(SupplierPayload):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class PurchaseOrderResponse(PurchaseOrderPayload):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    message: str
    read: bool
    created_at: datetime


@router.get("/customers", response_model=list[CustomerResponse])
def customers(db: DbSession, search: str | None = None) -> list[Customer]:
    query = select(Customer).order_by(Customer.name)
    if search:
        query = query.where(Customer.name.ilike(f"%{search.strip()}%"))
    return list(db.scalars(query.limit(200)).all())


@router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(payload: CustomerPayload, db: DbSession) -> Customer:
    data = payload.model_dump()
    data["name"] = payload.name.strip()
    customer = Customer(**data)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, payload: CustomerPayload, db: DbSession) -> Customer:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    for key, value in payload.model_dump().items():
        setattr(customer, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: DbSession) -> None:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    db.delete(customer)
    db.commit()


@router.get("/suppliers", response_model=list[SupplierResponse])
def suppliers(db: DbSession) -> list[Supplier]:
    return list(db.scalars(select(Supplier).order_by(Supplier.name).limit(200)).all())


@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
def create_supplier(payload: SupplierPayload, db: DbSession) -> Supplier:
    data = payload.model_dump()
    data["name"] = payload.name.strip()
    supplier = Supplier(**data)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/purchase-orders", response_model=list[PurchaseOrderResponse])
def purchase_orders(db: DbSession) -> list[PurchaseOrder]:
    return list(db.scalars(select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).limit(200)).all())


@router.post("/purchase-orders", response_model=PurchaseOrderResponse, status_code=201)
def create_purchase_order(payload: PurchaseOrderPayload, db: DbSession, current_user: User = Depends(require_admin)) -> PurchaseOrder:
    if not db.get(Supplier, payload.supplier_id):
        raise HTTPException(404, "Supplier not found")
    order = PurchaseOrder(**payload.model_dump())
    db.add(order)
    db.flush()
    db.add(AuditLog(user_id=current_user.id, action="create", entity="purchase_order", entity_id=order.id))
    db.commit()
    db.refresh(order)
    return order


@router.patch("/purchase-orders/{order_id}/status", response_model=PurchaseOrderResponse)
def update_purchase_order_status(order_id: int, payload: StatusPayload, db: DbSession, current_user: User = Depends(require_admin)) -> PurchaseOrder:
    order = db.get(PurchaseOrder, order_id)
    if not order:
        raise HTTPException(404, "Purchase order not found")
    order.status = payload.status
    db.add(AuditLog(user_id=current_user.id, action="status_change", entity="purchase_order", entity_id=order.id, details=payload.status.value))
    db.commit()
    db.refresh(order)
    return order


@router.get("/notifications", response_model=list[NotificationResponse])
def notifications(db: DbSession, current_user: User = Depends(get_current_user)) -> list[Notification]:
    if db.scalar(select(Notification.id).where(Notification.user_id == current_user.id).limit(1)) is None:
        low_stock = db.scalars(select(Product).where(Product.stock_quantity <= Product.min_stock_level).limit(5)).all()
        for product in low_stock:
            db.add(Notification(user_id=current_user.id, title="Low stock alert", message=f"{product.name} has {product.stock_quantity} units remaining"))
        db.commit()
    return list(db.scalars(select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(100)).all())


@router.patch("/notifications/{notification_id}", response_model=NotificationResponse)
def mark_notification(notification_id: int, payload: ReadPayload, db: DbSession, current_user: User = Depends(get_current_user)) -> Notification:
    item = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    if not item:
        raise HTTPException(404, "Notification not found")
    item.read = payload.read
    db.commit()
    db.refresh(item)
    return item


@router.get("/audit-logs", dependencies=[Depends(require_admin)])
def audit_logs(db: DbSession) -> list[dict]:
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)).all()
    return [{"id": row.id, "user_id": row.user_id, "action": row.action, "entity": row.entity, "entity_id": row.entity_id, "details": row.details, "created_at": row.created_at} for row in rows]
