from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Category, PaymentMethod, Product, Sale, SaleItem, User, UserRole
from app.models import Customer, Supplier

IMAGE_URLS = {
    "Wireless Mouse": "https://images.unsplash.com/photo-1527814050087-3793815479db?q=80&w=600",
    "USB-C Hub": "https://images.unsplash.com/photo-1625842268584-8f3296236761?q=80&w=600",
    "Bluetooth Speaker": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?q=80&w=600",
    "Iced Coffee": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?q=80&w=600",
    "Sparkling Water": "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?q=80&w=600",
    "Green Tea": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?q=80&w=600",
    "Sourdough Loaf": "https://images.unsplash.com/photo-1585478259715-876acc5be8eb?q=80&w=600",
    "Blueberry Muffin": "https://images.unsplash.com/photo-1601004140026-6b08709f6be2?q=80&w=600",
    "Chocolate Croissant": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?q=80&w=600",
    "Granola Bar": "https://images.unsplash.com/photo-1622484211148-cf6b5f9c5d6e?q=80&w=600",
    "Sea Salt Chips": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?q=80&w=600",
    "Trail Mix": "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?q=80&w=600",
    "Hand Sanitizer": "https://images.unsplash.com/photo-1584483766114-2cea6f66b5d1?q=80&w=600",
    "Moisturizing Lotion": "https://images.unsplash.com/photo-1556228578-8c89e6adf883?q=80&w=600",
    "Shampoo": "https://images.unsplash.com/photo-1556229010-6c3f2c9ca5f8?q=80&w=600",
    "Lip Balm": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?q=80&w=600",
}


def seed_database(db: Session) -> None:
    if db.scalar(select(Product.id).limit(1)) is not None:
        for product in db.scalars(select(Product)).all():
            if product.name in IMAGE_URLS and not product.image_url:
                product.image_url = IMAGE_URLS[product.name]
        if db.scalar(select(Supplier.id).limit(1)) is None:
            db.add_all([
                Supplier(name="Northstar Distribution", email="orders@northstar.example", phone="+1 555 0100"),
                Supplier(name="Acme Wholesale", email="hello@acme.example", phone="+1 555 0110"),
            ])
        if db.scalar(select(Customer.id).limit(1)) is None:
            db.add(Customer(name="Walk-in Customer", notes="Default POS customer"))
        db.commit()
        return

    categories = [
        Category(name="Electronics", description="Devices and accessories"),
        Category(name="Beverages", description="Drinks and refreshments"),
        Category(name="Bakery", description="Freshly baked goods"),
        Category(name="Snacks", description="Packaged snacks"),
        Category(name="Personal Care", description="Everyday personal care"),
    ]
    db.add_all(categories)
    db.flush()

    products = [
        ("Wireless Mouse", "ELEC-1001", "890123450001", categories[0], 18, 29.99, 24, 5),
        ("USB-C Hub", "ELEC-1002", "890123450002", categories[0], 32, 49.99, 3, 5),
        ("Bluetooth Speaker", "ELEC-1003", "890123450003", categories[0], 45, 79.99, 0, 4),
        ("Iced Coffee", "BEV-2001", "890123450011", categories[1], 1.2, 3.49, 36, 10),
        ("Sparkling Water", "BEV-2002", "890123450012", categories[1], 0.5, 1.99, 8, 12),
        ("Green Tea", "BEV-2003", "890123450013", categories[1], 2, 5.99, 42, 10),
        ("Sourdough Loaf", "BAK-3001", "890123450021", categories[2], 2.5, 6.5, 2, 6),
        ("Blueberry Muffin", "BAK-3002", "890123450022", categories[2], 1.1, 3.25, 18, 5),
        ("Chocolate Croissant", "BAK-3003", "890123450023", categories[2], 1.3, 3.75, 14, 5),
        ("Granola Bar", "SNK-4001", "890123450031", categories[3], 0.7, 2.49, 65, 12),
        ("Sea Salt Chips", "SNK-4002", "890123450032", categories[3], 0.8, 2.99, 4, 10),
        ("Trail Mix", "SNK-4003", "890123450033", categories[3], 2.4, 6.99, 27, 8),
        ("Hand Sanitizer", "CARE-5001", "890123450041", categories[4], 1.8, 4.99, 31, 8),
        ("Moisturizing Lotion", "CARE-5002", "890123450042", categories[4], 4.5, 10.99, 19, 5),
        ("Shampoo", "CARE-5003", "890123450043", categories[4], 5, 12.99, 0, 5),
        ("Lip Balm", "CARE-5004", "890123450044", categories[4], 1.2, 3.99, 22, 6),
    ]
    product_rows = [
        Product(name=name, sku=sku, barcode=barcode, image_url=IMAGE_URLS[name], category=category,
                purchase_price=Decimal(str(cost)), selling_price=Decimal(str(price)),
                stock_quantity=stock, min_stock_level=minimum)
        for name, sku, barcode, category, cost, price, stock, minimum in products
    ]
    db.add_all(product_rows)
    db.flush()

    user = db.scalar(select(User).limit(1))
    if user is None:
        user = User(full_name="Demo Administrator", email="demo@smartcloud.local", hashed_password=hash_password("DemoPass123!"), role=UserRole.ADMIN)
        db.add(user)
        db.flush()

    for offset in range(10):
        first = product_rows[(offset * 2) % len(product_rows)]
        second = product_rows[(offset * 2 + 3) % len(product_rows)]
        quantity = 1 + offset % 3
        sale = Sale(
            user_id=user.id,
            total_amount=first.selling_price * quantity + second.selling_price,
            payment_method=PaymentMethod.CARD if offset % 2 else PaymentMethod.CASH,
            created_at=datetime.now(timezone.utc) - timedelta(days=offset + 1),
        )
        sale.items.extend([
            SaleItem(product_id=first.id, quantity=quantity, unit_price=first.selling_price, subtotal=first.selling_price * quantity),
            SaleItem(product_id=second.id, quantity=1, unit_price=second.selling_price, subtotal=second.selling_price),
        ])
        db.add(sale)
    db.commit()
