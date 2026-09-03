from io import BytesIO
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.dependencies import DbSession, get_current_user
from app.models.inventory import Product
from app.models.enterprise import AuditLog, Notification
from app.models.sales import Sale, SaleItem
from app.models.user import User
from app.schemas.sales import SaleCreate, SaleResponse

router = APIRouter(prefix="/sales", dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[SaleResponse])
def list_sales(db: DbSession, current_user: User = Depends(get_current_user)) -> list[Sale]:
    return list(
        db.scalars(
            select(Sale)
            .where(Sale.user_id == current_user.id)
            .options(joinedload(Sale.items))
            .order_by(Sale.created_at.desc())
            .limit(100)
        ).unique().all()
    )


@router.post("", response_model=SaleResponse, status_code=201)
def create_sale(payload: SaleCreate, db: DbSession, current_user: User = Depends(get_current_user)) -> Sale:
    quantities: dict[int, int] = {}
    for item in payload.items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity

    products = {
        product.id: product
        for product in db.scalars(select(Product).where(Product.id.in_(quantities)).with_for_update()).all()
    }
    missing = set(quantities) - set(products)
    if missing:
        raise HTTPException(status_code=404, detail=f"Product not found: {min(missing)}")

    gross_total = Decimal("0")
    for product_id, quantity in quantities.items():
        product = products[product_id]
        if product.stock_quantity < quantity:
            raise HTTPException(status_code=409, detail=f"Insufficient stock for {product.name}")
        gross_total += product.selling_price * quantity

    if payload.discount_amount > gross_total:
        raise HTTPException(status_code=422, detail="Discount cannot exceed sale subtotal")
    sale = Sale(user_id=current_user.id, total_amount=gross_total - payload.discount_amount,
                payment_method=payload.payment_method, customer_name=payload.customer_name,
                customer_phone=payload.customer_phone)
    db.add(sale)
    db.flush()
    for product_id, quantity in quantities.items():
        product = products[product_id]
        product.stock_quantity -= quantity
        sale.items.append(SaleItem(product_id=product_id, quantity=quantity, unit_price=product.selling_price, subtotal=product.selling_price * quantity))
        if product.stock_quantity - quantity <= product.min_stock_level:
            db.add(Notification(user_id=current_user.id, title="Low stock alert", message=f"{product.name} has {product.stock_quantity - quantity} units remaining"))
    db.add(AuditLog(user_id=current_user.id, action="create", entity="sale", entity_id=sale.id))
    db.commit()
    db.refresh(sale)
    return sale


@router.get("/{sale_id}/invoice")
def invoice(sale_id: int, db: DbSession, current_user: User = Depends(get_current_user)) -> StreamingResponse:
    sale = db.scalar(select(Sale).options(joinedload(Sale.items).joinedload(SaleItem.product)).where(Sale.id == sale_id))
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    if sale.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="You do not have access to this invoice")

    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    y = height - 55
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "Smart Cloud Inventory")
    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(width - 50, y, f"Receipt #{sale.id}")
    y -= 28
    pdf.drawString(50, y, f"Date: {sale.created_at:%Y-%m-%d %H:%M}")
    pdf.drawRightString(width - 50, y, f"Payment: {sale.payment_method.value}")
    y -= 32
    pdf.line(50, y, width - 50, y)
    y -= 22
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, y, "Item")
    pdf.drawRightString(width - 160, y, "Qty")
    pdf.drawRightString(width - 50, y, "Subtotal")
    y -= 18
    pdf.setFont("Helvetica", 10)
    for item in sale.items:
        pdf.drawString(50, y, item.product.name[:55])
        pdf.drawRightString(width - 160, y, str(item.quantity))
        pdf.drawRightString(width - 50, y, f"${item.subtotal:.2f}")
        y -= 17
    y -= 8
    pdf.line(50, y, width - 50, y)
    y -= 22
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(width - 50, y, f"Total: ${sale.total_amount:.2f}")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(50, 45, "Thank you for your business.")
    pdf.save()
    output.seek(0)
    return StreamingResponse(output, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="invoice-{sale.id}.pdf"'})
