from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole, name="user_role", native_enum=False),
        default=UserRole.STAFF,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
