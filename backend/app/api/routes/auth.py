from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import DbSession, get_current_user, require_admin
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserResponse

from typing import Annotated
from fastapi import Depends

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession) -> TokenResponse:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    # Public registration cannot grant elevated privileges after the workspace exists.
    requested_role = payload.role if db.scalar(select(User.id).limit(1)) is None else UserRole.STAFF
    user = User(full_name=payload.full_name.strip(), email=email, hashed_password=hash_password(payload.password), role=requested_role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)


@router.get("/me", response_model=UserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return current_user


@router.get("/users", response_model=list[UserResponse], dependencies=[Depends(require_admin)])
def users(db: DbSession) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at)).all())
