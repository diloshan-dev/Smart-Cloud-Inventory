from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.api.router import api_router
from app.core.config import settings
from app.db.session import Base, engine
from app.db.seed import seed_database
from app.models import User

app = FastAPI(
    title="Smart Cloud Inventory & Sales Analytics API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    product_columns = {column["name"] for column in inspect(engine).get_columns("products")}
    if "image_url" not in product_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE products ADD COLUMN image_url VARCHAR(500)"))
    if "full_name" not in {column["name"] for column in inspect(engine).get_columns("users")}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(160)"))
    sale_columns = {column["name"] for column in inspect(engine).get_columns("sales")}
    with engine.begin() as connection:
        if "customer_name" not in sale_columns:
            connection.execute(text("ALTER TABLE sales ADD COLUMN customer_name VARCHAR(160)"))
        if "customer_phone" not in sale_columns:
            connection.execute(text("ALTER TABLE sales ADD COLUMN customer_phone VARCHAR(40)"))
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        seed_database(db)
